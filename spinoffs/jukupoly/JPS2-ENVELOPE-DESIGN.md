# JPS v2 envelope vertical-slice contract

Status: M3 target-side synthetic checkpoint and host fitting primitive
implemented, 2026-09-01.  Real-song voice extraction/integration, the
30-second Imp's Song comparison, and physical listening gate remain pending.
This slice is deliberately limited to fitted amplitude envelopes.  Tremolo,
vibrato, held-key pitch automation, four-operator synthesis, and hardware
rhythm remain later independent gates.

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

## Measured synthetic checkpoint

The separately assembled `-P2=1 -P4=1` library player now implements the
packet parser and the five-stage target state machine.  The 46-frame fixture
exercises immediate and timed attack, decay, keyed sustain, non-sustaining
automatic release, explicit key-off release, concurrent percussion, and
phase-step removal only after release reaches zero.  The library preflights
the entire variable row stream plus drum descriptors and PCM extents before
touching the PIT.  Reserved envelope bits, invalid peak/sustain levels,
truncated packets, invalid drum descriptors, and oversized PCM all fail with
zero PIT writes.

[`OPL-ENVELOPE-M3.json`](OPL-ENVELOPE-M3.json) records the reproducible target
measurements.  The enhanced player is 4,537 bytes, ends at `12B9h`, and leaves
1,351 bytes before the song load address.  Its persistent player state remains
49 bytes.  The exact frozen 64-byte sample loop and its SHA-256 are unchanged,
and an enhanced-player run of the v1 Doomgate fixture matches every frozen v1
playback metric.

The expanded v2 stress fixture uses 141 samples per frame.  It measures
7,044.10 samples/s and 49.958 music frames/s, above the selected frozen
Doomgate comparison floor of 6,401.15 Hz and within 0.084% of the 50 Hz source
clock.  Its worst complete frame is 42,670 cycles and its largest row boundary
is 8,586 cycles.  An earlier 16-frame
fixture made 139 samples appear suitable, but the expanded mixture measured
50.647 frames/s at that setting.  This demonstrates that the batch count must
be selected and verified over each converted full song; a short synthetic
average is not sufficient evidence.

`opl_envelope.py` is the first host-side fitting primitive.  Its simulator
matches the 8080 stage ordering and global power-of-two update masks exactly;
an exhaustive deterministic search recovers target-generated synthetic
curves with zero error.  For an isolated pinned-Nuked two-operator reference,
the helper quantizes 20 ms RMS blocks relative to a separately resolved peak
level and fits a strict packet with 1.375 mixer levels mean absolute error and
six levels maximum error.  The largest mismatch is the deliberately exposed
limit that Juku's linear one-level attack cannot follow Yamaha's accelerating
attack curve.  The fitted packet passes the strict JPS v2 encoder.

For real-source absolute levels, the pinned oracle additionally exposes each
operator's post-envelope `eg_out` attenuation and the two-operator connection
bit at 50 Hz.  `eg_out` already includes the live envelope, TL, KSL, and
tremolo.  The host converts its 0.1875 dB units to linear amplitude, selects
the carrier in FM mode or a capped operator sum in additive mode, and
quantizes that semantic amplitude to 0..15.  This does not claim to reproduce
waveform, feedback, or FM timbre; isolated PCM/RMS remains a separate shape
cross-check.

The bridge also has a guarded all-channel probe mode.  A synthetic regression
proves that its channel-zero sequence is byte-for-field identical to the
existing isolated channel-zero probe, allowing one oracle render to feed the
real 18-channel logical-voice mapper.

This checkpoint does not complete M3.  The next independent layer is mapping
real selected logical voices to isolated oracle intervals, then producing the
like-for-like v1/v2/reference comparison.  That real-song comparison supplies
the per-song G2 floor which a synthetic fixture cannot.  No Doom library track
is emitted as JPS v2 yet, so a failed real-song fit can still fall back to its
unchanged v1 reduction.
