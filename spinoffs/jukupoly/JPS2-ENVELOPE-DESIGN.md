# JPS v2 envelope contract

Status: implemented compact envelope ABI. The enhanced Imp candidate failed
physical listening and is delivered as unchanged JPS1. This document defines
the envelope layer; tremolo and pitch extensions have their own contracts.
[OPL-PLAN-STATUS.json](OPL-PLAN-STATUS.json) owns the combined qualification status.

## Compatibility boundary (envelope-only build)

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
uses the enhanced routines. The assembled 64-byte sample loop matches the
frozen baseline. Playback retains its existing self-modifying phase, volume,
percussion-pointer and sample-count operands.

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

Nonzero rates use the shared `env_counter`: a step occurs when the counter
AND the current stage's mask is zero. Key-on and stage changes do not reset
that counter, so the first step can occur before a full listed interval has
elapsed. The intervals describe the shared frame cadence.

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

## Verification and qualification

The envelope-only library build uses `-P2=1 -P4=1`; the combined library adds
the feature definitions described in [tremolo](JPS2-TREMOLO-DESIGN.md) and
[pitch](JPS2-PITCH-DESIGN.md). Its extra accepted capabilities do not change the
packet and stage meanings above. The strict host compiler, library preflight
and C-cosim tests check malformed data before any PIT output.

[OPL-ENVELOPE-M3.json](OPL-ENVELOPE-M3.json) records synthetic exact-state,
map, hot-loop, compatibility and timing evidence.
[OPL-IMP-M3.json](OPL-IMP-M3.json) and
[OPL-IMP-FULL-M3.json](OPL-IMP-FULL-M3.json) record bounded/full-song source fits,
size, cycle measurements and explicit delivery fallback. A single compact ADSR
cannot reproduce every evolving keyed OPL contour; timing passes do not override
the negative physical result in the
[M6 physical record](sessions/cs00000-jukupoly-m6-physical/README.md).

All envelope/effect work shares the [reduction contract](OPL-REDUCTION-PLAN.md)
budget: unchanged sample loop, at least 90% of baseline sample rate, source
music/duration within 1%, player below `1800h`, and bounded JPS data. Regenerate
phase steps from measured rates rather than changing timing metadata alone.
Run the documented guards from the repository root:

```sh
bash sync/jukupoly_envelope_check.sh
bash sync/jukupoly_library_check.sh
```
