# JPS v2 pitch and vibrato vertical-slice contract

Status: guarded M5 design, 2026-09-01.  Source semantics and three-voice
allocation survival are measured; this document does not accept a new target
capability.  Capability `01h` envelopes, experimental capability `03h`
envelope+tremolo, and JPS v1 remain independent fallbacks.

## Scope and evidence

This slice has two deliberately separate parts:

1. Preserve source frequency-register changes while a selected logical note
   remains keyed.  This reuses an existing JPS v2 legato tone packet and adds
   no target instruction or state.
2. Approximate only conservative direct common-pitch OPL vibrato with one
   shared eight-position LFO and a host-precomputed phase-step delta.  It does
   not turn FM-modulator-only VIB or one-sided additive VIB into whole-note
   pitch modulation.

[`OPL-PITCH-M5.json`](OPL-PITCH-M5.json) records 30,118 direct common-pitch
melodic key-ons across the two known DOOM packs.  After logical layering,
22,829 melodic logical notes remain conservative direct candidates and 21,017
are selected by the M2 three-voice allocation.  Of 7,264 valid held-key
melodic pitch events, 6,495 occur while that exact logical note owns a target
channel.  Protected-v1 onset regressions remain zero.  This justifies a
bounded experiment, not default enablement.

## Compatibility boundary

Target support, if implemented, is compiled only in a new experimental build
after `-P5=1`.  Proposed JPS v2 capability bit 2 means bounded pitch/vibrato.
The accepted capability combinations are:

- `01h`: fitted envelopes;
- `03h`: fitted envelopes plus tremolo;
- `05h`: fitted envelopes plus pitch/vibrato;
- `07h`: fitted envelopes, tremolo, and pitch/vibrato.

Bit 2 cannot appear without bit 0.  Players which do not implement bit 2 must
reject `05h` and `07h` before touching the PIT.  A capability-`05h` player
must reject tremolo packet bits, and every player must reject packet fields
which were not advertised.  JPS v1 and capability `01h` retain their exact
existing parser and frame profiles.

Held-note pitch automation does not require capability bit 2 by itself.  It is
already exactly expressible as a normal nonzero JPS v2 tone packet with the
high phase-step legato bit set.  The existing parser replaces `chN_step` and
the packet settings without resetting the phase accumulator or envelope.
Host conversion must emit such a packet only when the selected note still
owns the same target channel.

## Packet encoding

The first five bytes of every nonzero tone packet retain their current layout.
Byte 4 becomes:

| Bit | Meaning |
|---:|---|
| 0 | release rate code bit 2 |
| 1 | sustain while keyed (`EGT`) |
| 2–3 | tremolo depth `0..3` |
| 4–5 | vibrato mode: `0` off, `1` shallow, `2` deep, `3` invalid |
| 6–7 | reserved; must be zero |

Mode zero leaves the packet exactly five bytes.  Mode one or two appends one
byte encoding `peak_step_delta - 1`, so the representable host-precomputed
positive magnitude is `1..256`.  The conditional byte is present only under
capability bit 2.  This covers the complete 15-bit phase-step range without
runtime multiplication and avoids charging non-vibrato packets.

The score-side record is proposed as `opl_vibrato` adjacent to
`opl_envelope`, containing source mode (`shallow` or `deep`) and the already
resolved `peak_step_delta` in `1..256`.  The compiler must reject booleans,
unknown fields, zero deltas, mode 3, vibrato on key-off, or a field on a song
without JPS v2 envelopes.  Omitting it is byte-identical mode zero.

Preflight must walk the conditional byte and prove, for every vibrato packet:

- the base step is nonzero and below `8000h` after removing the legato bit;
- `base - peak_delta` remains positive;
- `base + peak_delta` remains below `8000h`;
- mode and capability agree;
- the row and JPS image remain bounded.

Malformed input is rejected before playback rather than clipped at runtime.
This preserves the qualified low/high frequency range and makes target
underflow or 15-bit overflow impossible in the hot path.

## Exact target semantics

The host and pinned oracle establish Nuked's eight positions as
`0,+half,+full,+half,0,-half,-full,-half`.  At the DOOM OPL clock, one cycle
is 6.068835788 Hz.  The target uses:

- one 16-bit unsigned shared phase reset to zero at song start;
- phase increment `7955` (`1F13h`) once per rendered music frame;
- table index `phase >> 13`;
- the serialized peak delta and a right shift for half positions;
- a temporary `base step +/- delta` loaded for the next sample batch.

`chN_step` remains the immutable base between explicit source pitch events.
Vibrato must never write the temporary result back to it, so there is no mean
pitch drift.  Frame zero consults phase zero before incrementing.  The shared
phase advances in every capability-bit-2 song even when all current modes are
off, preserving absolute source-LFO alignment.

A legato pitch packet replaces the base step and current precomputed vibrato
delta together.  It does not reset the shared LFO, sample phase accumulator,
or envelope.  Key-off retains vibrato through the release tail, matching the
OPL phase generator; release completion clears the channel mode/delta when it
clears the base step.  A new non-legato note replaces mode and delta.

Global depth or operator VIB changes made while a key is held must become a
legato update at the next representable 50 Hz frame, or be reported as
unsupported.  The importer may not silently retain a stale delta.

## Static resource guard

The M4 player is 4,863 bytes, ends at `13FFh`, declares 51 state bytes, and
leaves 1,025 bytes before the `1800h` song window.  The proposed runtime adds:

- exactly two bytes of shared vibrato phase;
- exactly one peak-delta byte per tone channel;
- no per-channel base word, because `chN_step` already provides it;
- at most an eight-byte sign/half/full table, or equivalent bounded branches;
- bounded parser, verifier, dispatch, and preparation code;
- one song byte only on packets whose vibrato mode is nonzero.

The experimental map must still end below `1800h`, declared state must be
exactly 56 bytes for the combined M4+M5 build, and stack/JPS bounds remain
unchanged.  If the combined implementation cannot fit, capability `03h` and
host-baked held-pitch packets remain valid stopping points.

## Cycle guard

The intended runtime performs one shared phase update and, for each enabled
channel, one byte lookup/shift plus a bounded 16-bit add or subtract at the
50 Hz frame boundary.  It performs no multiply, divide, allocation, or work
inside the frozen sample loop.  A preliminary orientation ceiling is 900
additional cycles for three vibrato voices on top of envelope preparation;
this is an estimate, not an acceptance result.

The combined capability-`07h` path, not vibrato in isolation, must pass G2
with envelopes, tremolo, row parsing, percussion, and Escape polling.  The
effective sample rate remains at least 90% of the frozen baseline, music clock
and full-track duration stay within 1%, and the sample-loop hash is exact.
The feature may not buy cycles by removing percussion, Escape, frequency
range, or existing effects.

Held-pitch automation normally costs only row-boundary parsing.  Its longest
affected tracks must nevertheless pass worst-row timing, duration, and the
30 KiB JPS soft ceiling.  Per-frame host baking is acceptable only if those
measurements pass.

## Guarded implementation order

1. Add host-only packet encoding, strict malformed-input tests, and capability
   rejection.  Prove modes zero and capabilities `01h`/`03h` remain byte- and
   cycle-identical.
2. Emit selected held-key pitch changes through existing legato packets and
   measure retained contours, row cost, and longest-track JPS growth.  This is
   independently useful even if runtime vibrato stops here.
3. Add a separate experimental parser/state build for capability `05h`, with
   exact preflight and source-to-target trace tests.
4. Add shared-phase temporary-step preparation and compare every synthetic
   target frame against `opl_vibrato.py`, including low/high bounds and zero
   mean drift over whole cycles.
5. Compose capability `07h` with M4 tremolo and report binary/map/state growth,
   off-path identity, exact cycle distributions, effective rates, duration,
   and JPS sizes.
6. Convert a bounded direct-vibrato excerpt and one held-pitch-heavy excerpt;
   render old/new/Nuked comparisons without song-specific rules.
7. Run complete-track and two-pack gates, then CS00000 A/B before any default
   enablement.

## Failure and rollback rules

- If held-pitch packets exceed G5, quantize out sub-step changes, coalesce
  identical target steps, use sparse interpolation only if it improves size,
  or omit the least audible motion.  Do not add unbounded per-frame data.
- If a source pitch path is mixed, indirect, or changes semantics mid-note
  without a truthful mapping, preserve the previous conversion and report it.
- If parser/preflight or exact target traces disagree, retain the host report
  and existing legato capability; do not ship capability bit 2.
- If code/state fails G4, stop at host-baked held pitch or remove runtime
  vibrato while retaining M3/M4.
- If combined cycles fail G2, simplify the eight-step update or compare sparse
  host-baked vibrato.  Do not exceed the shared 10% sample-rate reduction.
- If representative or physical A/B does not improve the result, keep the
  feature experimental or unsupported.  Capability `03h`, `01h`, and JPS v1
  remain usable fallbacks.

The successful result is the largest measured subset the Juku can afford.
Nothing in this contract requires runtime vibrato to succeed merely because
the source analysis did.
