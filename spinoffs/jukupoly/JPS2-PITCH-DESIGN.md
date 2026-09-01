# JPS v2 pitch and vibrato vertical-slice contract

Status: guarded M5 implementation, 2026-09-01.  Source semantics,
three-voice allocation survival, host-baked pitch, and experimental parser
and synthetic runtime targets are measured; normal conversion does not yet
accept the runtime pitch capability.  Capability `01h` envelopes,
experimental capability `03h` envelope+tremolo, host-baked pitch, and JPS v1
remain independent fallbacks.

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

## Host-format checkpoint

Step 1 is implemented without target support.  `build_jukupoly.py` validates
the exact `opl_vibrato` object, encodes shallow/deep modes in packet bits 4--5,
appends `peak_step_delta - 1` only for nonzero modes, and advertises capability
`05h` or `07h`.  It rejects unsafe low/high base-step bounds, malformed
objects, vibrato on key-off, and vibrato in JPS v1.  A request to assemble a
standalone pitch-capable target fails explicitly because no target slice
exists yet; host code can build the guarded JPS image for format tests.

Omitted vibrato preserves the exact capability-`01h` image, and existing
tremolo retains capability `03h`.  Tests cover delta 256, combined `07h`,
reserved mode values through strict source validation, and both underflow and
overflow boundaries.  The M4 library player rejects proposed capability
`05h` with zero PIT writes and zero keyboard polls.  Thus the host ABI is
reversible and cannot accidentally run on an older player.

## Host-baked held-pitch checkpoint

Guarded implementation step 2 is complete without accepting capability bit 2.
`--enhanced-held-pitch` evaluates the selected logical source contour at the
50 Hz reducer grid, maps it through the allocator's target octave, and emits a
normal raw-step JPS2 legato packet only when the same logical note retains its
channel and its quantized phase step changes.  Onsets also use raw steps from
the same calculation.  The score records `phase_step_generation_hz`, which
must equal `sample_rate_hz`; tests independently calculate an expected step
at both 7,170 and 6,850 Hz.  This guard exists because reducing only the frame
batch and metadata would preserve timing while detuning every stored step.

The complete “At Doom's Gate” fixture emits 566 such packets.  Its 17,215-byte
JPS remains below G5, and the fixed-pitch control is 14,073 bytes.  Both use
capability `01h` and the existing 4,537-byte envelope player, so this slice
adds no target code or state.  The initial 143-sample profile failed duration
and music-clock gates at 100.296 seconds and 48.118 Hz.  The fully regenerated
137-sample/6,850 Hz version measures 6,859.2 samples/s, 50.067 Hz, and 96.391
seconds versus 96.513 seconds, with a 43,380-cycle maximum frame.  All
automated gates in `OPL-PITCH-REAL-M5.json` pass; physical A/B remains pending.

This is an accepted progressive stopping point, not evidence that runtime
vibrato will fit.  Steps 3--7 and all combined capability-`07h` guards remain
in force independently.

## Parser/state target checkpoint

Guarded implementation step 3 now passes in a separate `-P6=1` experimental
build.  Capability `05h` uses a distinct variable-length parser so the
qualified `01h`/`03h` packet path remains byte- and cycle-identical.  The
library preflight accepts only exact capability combinations, consumes the
conditional delta byte, rejects mode 3 and unadvertised tremolo/vibrato bits,
and proves `base-delta > 0` and `base+delta < 8000h` before touching the PIT.
Missing conditional bytes, both bound failures, and all capability mismatches
are exercised with zero PIT writes and zero keyboard polls.

[`OPL-VIBRATO-PARSER-M5.json`](OPL-VIBRATO-PARSER-M5.json) records a 4,993-byte
pitch-parser player ending at `1481h`, with 54 declared state bytes and 895
bytes left before the song window.  The combined `-P5=1 -P6=1` parser is 5,349
bytes, ends at `15E5h`, leaves 539 bytes, and has exactly the proposed 56 state
bytes.  Every build retains the frozen sample-loop hash.  JPS v1, capability
`01h`, and combined-build capability `03h` execution profiles are exact
matches for their already-qualified P4/P5 players.

The synthetic target trace covers encoded deltas 1 and 256, a legato base and
delta replacement, enabling/disabling vibrato on a held note, immediate
release clearing, and a non-immediate release which retains its mode.  The
shared phase deliberately remains zero and temporary steps are not yet
applied.  The normal assembler continues to reject a vibrato target request.
Therefore this checkpoint proves synchronization, safety, and bounded state
only; step 4's exact eight-position runtime trace is still required before
capability bit 2 can claim playback support.

## Synthetic runtime target checkpoint

Guarded implementation steps 4 and 5 now pass behind the additional `-P7=1`
define.  The frame preparation routine calculates three temporary steps from
the existing immutable `chN_step` words, uses only bounded shifts/branches and
16-bit addition or subtraction, advances the shared phase by `1F13h`, and
then lends the temporary channel-3 step through SP to the unchanged sample
loop.  The next frame jumps over the normal temporary-step writeback before
restoring the real stack, preventing cumulative drift.  No multiply, divide,
or sample-loop instruction was added.

Initialization explicitly clears all three base words before the first row.
The target test seeds them with stale prior-song values, proving that reuse of
the library player cannot leak a previous track into a new track whose first
row omits a channel.  Separate capability-`05h` and combined-`07h` traces
compare every temporary BC/DE/SP step over 18 frames, including deltas 1 and
256, all eight shape positions, legato base replacement, release retention
and clearing, phase advancement, and immutable bases.  Symmetric positive and
negative magnitudes sum to zero for every representable delta 1..256.

[`OPL-VIBRATO-TARGET-M5.json`](OPL-VIBRATO-TARGET-M5.json) records the
reproducible map and timing evidence.  The `-P6=1 -P7=1` player is 5,255 bytes,
ends at `1587h`, declares 54 state bytes, and leaves 633 bytes before `1800h`.
Adding M4 tremolo produces a 5,632-byte player ending at `1700h`, with exactly
56 state bytes and 256 bytes left.  V1, capability `01h`, and capability
`03h` paths are execution-identical to matched P4/P5 controls, and every
sample-loop hash remains frozen.

The matched three-channel runtime cost is about 1,359 boundary cycles per
frame.  This exceeds the preliminary 900-cycle orientation estimate, which
was explicitly not an acceptance limit, but the authoritative combined G2
measurement passes.  The pitch-only high-step/percussion fixture selects
131 samples/frame and a 6,530 Hz table, measuring 6,532.9 samples/s, 49.869
frames/s, and 4.010 seconds over 200 frames.  The more expensive combined
three-depth tremolo plus three-vibrato fixture selects the minimum permitted
129 samples/frame and a 6,450 Hz table, measuring 6,455.4 samples/s, 50.042
frames/s, and 3.997 seconds.  Worst rows are 42,713 and 42,696 cycles; both
fixtures retain concurrent percussion fetching and Escape polling and remain
above the shared 6,401.1 Hz floor.

This is synthetic runtime acceptance only.  `build_jukupoly.py` continues to
refuse runtime-vibrato target assembly, so capability bit 2 cannot enter the
normal player accidentally.  Steps 6 and 7—representative real-song
conversion/render, complete-track/pack regression, and physical CS00000
listening—remain open.  If any fails, the qualified host-baked held-pitch path
and capability `03h` remain the stopping points; the 129-sample guard may not
be reduced further.

## Bounded real-song checkpoint

Guarded implementation step 6 now passes on the first 30 seconds of “At
Doom's Gate.”  The new host option is still score generation only:
`--enhanced-vibrato` requires envelopes, the pinned all-channel oracle, and
explicit `--enhanced-frame-samples` plus `--enhanced-sample-rate` values from
a measured profile.  The reducer applies no source-name or instrument-ID
rule.  For each selected logical note and frame it classifies the currently
audible OPL operators, accepts only a direct common-pitch VIB path on every
active layer, derives each layer's target delta from the immutable mapped
phase step and current OPL F-number, and requires all layers to agree.  Zero,
mixed/indirect, inconsistent, out-of-range, and bound-violating decisions are
reported and omitted.

The score carries the resolved shallow/deep mode and `1..256` peak delta.
When depth, operator VIB, source F-number, or quantized delta changes while a
logical note retains its target channel, a normal JPS2 legato packet replaces
the setting without resetting phase or envelope.  The score records
`phase_step_generation_hz`, and the real report requires it to equal the
declared phase-table rate; this is the same protection against metadata-only
detuning used by held pitch.

[`OPL-VIBRATO-REAL-M5.json`](OPL-VIBRATO-REAL-M5.json) records 1,806 selected
channel-frames: 1,455 are direct, 213 have no direct VIB, and 138 rounded
allocation frames have no currently active source member.  The generic policy
emits 251 logical notes through
289 vibrato packets, including 156 held-setting updates.  All 280 protected
onsets are retained and every serialized delta passes the exact 15-bit bounds.
Removing vibrato and all 156 now-redundant update packets produces a controlled
5,894-byte capability-`01h` score; the runtime score is 7,065 bytes with
capability `05h`, still well below G5.

The rejected initial 131-sample/6,530 Hz calibration ran at 50.738 frames/s
and 29.564 seconds and did not match its phase table within 1%.  A timing-only
sweep selected 133 samples, after which the entire score—base steps and
vibrato deltas included—was regenerated from source at 6,650 Hz.  The accepted
profile measures 6,657.4 samples/s, 50.055 frames/s, 29.967 seconds, a 6.076
Hz target LFO, and a 43,628-cycle worst row.  The shared floor is 6,401.1 Hz.
Percussion fetching, 1,501 Escape polls, the 5,255-byte/54-state runtime map,
and the frozen sample loop remain present.  The independently calibrated
139-sample/6,970 Hz envelope control measures 50.153 frames/s and 29.909
seconds; both target WAV hashes differ, and the pinned-Nuked 30-second WAV hash
is recorded for listening comparison.

The identical generic policy also passes the complete 96.520-second source.
[`OPL-VIBRATO-FULL-M5.json`](OPL-VIBRATO-FULL-M5.json) records 908 emitted
logical notes, 1,018 vibrato packets, 520 held-setting updates, all 1,080
source onsets retained, and no protected-onset regression.  Its 18,133-byte
JPS is below the 30 KiB soft limit.  At the same 133-sample/6,650 Hz
calibration, it measures 6,605.7 samples/s, 49.667 frames/s, 97.167 seconds,
a 6.029 Hz LFO, and a 44,481-cycle worst frame.  The frozen loop, percussion,
and Escape polling remain present.

This evidence does not enable the normal assembler.  Complete-track
automation has passed, but pack regression plus physical CS00000 A/B remain
step 7.  If either fails, the capability-`01h` envelope control and qualified
host-baked held pitch remain the accepted result.
