# JPS v2 envelope vertical-slice contract

Status: M3 implementation contract, 2026-09-01.  This is deliberately limited
to fitted amplitude envelopes.  Tremolo, vibrato, held-key pitch automation,
four-operator synthesis, and hardware rhythm remain later independent gates.

## Compatibility boundary

The enhanced library player is a separate `-P2=1 -P4=1` build.  The frozen G0
player remains reproducible with `-P2=1` alone, so the pre-OPL baseline cannot
silently move while v2 is developed.

An enhanced player accepts:

- `JPS\1`, header capability byte `00h`: the existing packet ABI and exact v1
  frame routines;
- `JPS\2`, header capability byte `01h`: the envelope packet ABI below;
- no other version, capability bit, MOD-effects packet, or pattern packet.

At song start the player patches the three tone-parser call operands and the
three envelope-update call operands.  A v1 song continues to call the existing
routines directly, with the same per-frame instructions and cycles.  Only v2
uses the enhanced routines.  The 64-byte sample hot loop is never patched or
changed.

## Tone packet

Row duration, flags, percussion, and the 15-bit phase-step/legato word retain
their v1 meanings.  A zero phase step is still a two-byte key-off packet.  A
nonzero v2 tone packet is five bytes:

| Bytes | Meaning |
|---|---|
| 0–1 | little-endian 15-bit phase step; bit 15 is legato |
| 2 | peak level in the high nibble, sustain level in the low nibble |
| 3 | attack code bits 0–2, decay code bits 3–5, release code bits 6–7 |
| 4 | release-code bit 2 in bit 0; sustain-while-keyed (`EGT`) in bit 1; bits 2–7 zero |

Levels are already-resolved target mixer values `0..15`; they are not raw OPL
TL fields.  Peak must be `1..15`, and sustain must not exceed peak.

Each three-bit rate code is also already fitted on the host:

| Code | One mixer-level step |
|---:|---:|
| 0 | immediate |
| 1 | every frame |
| 2 | every 2 frames |
| 3 | every 4 frames |
| 4 | every 8 frames |
| 5 | every 16 frames |
| 6 | every 32 frames |
| 7 | every 64 frames |

Thus the packet stores a compact piecewise approximation, not Yamaha rate
nibbles.  The host fitter must compare its 50 Hz, 4-bit result with an isolated
Nuked OPL3 reference.  An attack shorter than one frame becomes code 0.

## Runtime semantics

Each enhanced channel follows `off → attack → decay → sustain → release`:

- a non-legato key-on resets phase and starts at zero;
- an immediate attack sets the peak during row parsing;
- decay stops at the serialized sustain level;
- with sustain-while-keyed set, the channel holds there until key-off;
- without it, release begins as soon as decay reaches sustain;
- key-off starts release without clearing phase step;
- reaching zero clears the phase step and stage;
- a new key-on during release retriggers the general envelope normally;
- legato changes pitch/configuration without restarting the current envelope.

The implementation adds five bytes after each existing six-byte channel
record: sustain level, decay mask, release mask, stage, and envelope flags.
The existing target and mask bytes hold the current stage target and rate
mask.  Total added persistent state is 15 bytes plus bounded parser scratch.

## Guarded implementation order

1. Add pure host encoding/validation and malformed-packet tests.
2. Add the `-P4=1` loader/version dispatch while proving all v1 binaries and
   renders unchanged.
3. Add v2 parsing and stage updates with a short synthetic JPS fixture.
4. Measure the enhanced player map, state, worst frame, effective sample rate,
   duration, and JPS size against G1–G6.
5. Fit a 30-second Imp's Song excerpt with the pinned oracle and compare
   reference, v1, and v2 renders.
6. Run the physical CS00000 A/B gate before enabling v2 for library tracks.

The rough M0 orientation permits about 3,800 additional cycles per 50 Hz frame,
but no estimate is an acceptance result.  The measured enhanced rate must stay
above the fixture-specific 90% baseline floor, all new effects share that one
budget, player end must remain below `1800h`, and JPS files retain the 30 KiB
soft/32,767-byte hard limits.  If the runtime stage update fails those gates,
the fallback is host-baked sparse level changes or v1 playback for that track,
not a larger sample-rate reduction.
