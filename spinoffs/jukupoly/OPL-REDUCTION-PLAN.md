# OPL-aware reduction plan

Status: design plan, 2026-09-01.  Nothing in this document is a claim that
the Juku can emulate an OPL chip.  Each target-side feature is conditional on
passing the cycle, memory, timing, and listening gates below.

## Objective

Improve VGZ-to-Juku conversion by preserving musically important OPL behavior:

- key-on, key-off, attack, decay, sustain, and release;
- OPL sustain/percussive envelope behavior (`EGT`), total level (`TL`), key
  scaling (`KSL` and `KSR`), and note retriggering;
- OPL tremolo (`AM` plus global depth) and vibrato (`VIB` plus global depth);
- pitch-register changes, legato, portamento-like motion, and release tails;
- additive versus FM connection when estimating which operators are audible;
- logical musical voices that may move between or be layered across OPL
  hardware channels.

The intended result is a better **three-pulse-voice plus percussion reduction**.
Exact FM waveforms, feedback timbre, eighteen OPL voices, stereo, and exact
four-operator synthesis are outside the physical capabilities of this player.

## Governing feasibility rule

This is a capability ladder, not an all-or-nothing specification.  The goal is
to implement the largest useful, truthful subset that fits the measured Juku
hardware budget.  Failure of an advanced feature must not discard improvements
from an earlier, affordable stage.

Every proposed feature has four legitimate outcomes:

1. **Target implementation:** run a compact form on the 8080 after it passes
   all cycle, sample-rate, RAM, file-size, and physical-listening gates.
2. **Host-side reduction:** analyze the exact OPL behavior on the host and emit
   a cheaper approximation, such as fitted envelope segments or sparse pitch
   changes.
3. **Perceptual omission:** omit behavior which cannot survive three pulse
   voices, 4-bit level quantization, or the available sample rate in a useful
   way.  The omission must be reported, not silently misrepresented.
4. **Unsupported:** reject or retain the old conversion when neither a correct
   nor a musically useful approximation fits the hardware budget.

Implementation therefore proceeds in independently useful layers:

- first, correct register timing, key transitions, pitch, and logical voice
  grouping on the host;
- next, affordable attack/decay/sustain/release and key-off tails;
- then tremolo, if audible after 4-bit quantization and inside the shared 10%
  sample-rate budget;
- then vibrato and held-note pitch changes under the same combined budget;
- finally, optional timbral, four-operator, and rhythm approximations only
  where measurements show that they add value.

There is no requirement that all layers succeed.  At every exit gate the
current passing subset must remain buildable, testable, and usable.  A failed
experiment is recorded as a limit of the platform and the plan continues with
other independent features where possible.

The immediate motivation is the failure observed in DOOM's “The Imp's Song.”
Several layered, evolving OPL voices became a long constant square tone when
the current converter retained pitch and approximate carrier level but emitted
every melodic note with a `hold` envelope.  The solution must be general; it
must not contain track numbers, filename checks, or instrument-signature
overrides for that song.

## Source semantics

The Yamaha YMF262 provides two- and four-operator synthesis, operator envelope
generators, selectable waveforms, feedback and connection modes, rhythm mode,
and shared low-frequency oscillators for amplitude and frequency modulation.
The datasheet gives approximately 3.7 Hz for tremolo and a nominal 6.4 Hz for
vibrato.  The pinned core's exact eight-step counter at the DOOM pack's
14,318,180 Hz clock and divide-by-288 native rate is 6.068835788 Hz; target
timing uses that measured source behavior rather than the rounded manual
figure.  `EGT` selects sustained versus percussive envelope behavior, while
`KSR` changes envelope rate with pitch.  `TL` is logarithmic attenuation, not
linear volume.

VGM files preserve timed YM3812/YMF262 register writes.  The importer must
therefore interpret a register timeline, including writes made while a note is
already sounding; it must not reduce the stream to key-on events first.

Primary references:

- [Yamaha YMF262 datasheet](https://www.bitsavers.org/components/yamaha/YMF262_199110.pdf)
- [VGM 1.71 command and timing specification](https://github.com/vgmrips/vgmplay-legacy/blob/master/VGMPlay/vgmspec171.txt)
- [Nuked OPL3 upstream implementation](https://github.com/nukeykt/Nuked-OPL3)

Nuked OPL3 is to be used only on the host as the behavioral oracle and
reference renderer.  Its synthesis algorithm is not a candidate for the 8080
player.

## Existing hardware and software boundaries

These are constraints, not optimization suggestions:

- The target CPU is modeled at 1.70 MHz.  At a nominal 50 Hz music-frame rate,
  one complete frame has about 34,000 CPU cycles, including all sample output.
- VGZ reductions currently use 143 sample-loop iterations per music frame and
  measure about 7.12 kHz in the cycle model.
- The three-tone/percussion sample hot loop owns the 8080 register file and
  stack pointer.  No envelope or LFO work may be inserted into that loop.
- Effects may run only at the approximately 50 Hz frame boundary, after the
  real stack has been restored.
- Tone amplitude at the speaker is only a 4-bit mix value.  A higher-resolution
  internal envelope cannot create more physical output levels; it can only
  improve rounding and timing.
- Library songs load at `1800h` and a JPS image must remain smaller than
  32,768 bytes.  Player growth must not overlap the song load address.
- The existing ABI-v2 MOD player is evidence that frame work is not free: it
  uses 139 samples per frame and about 6.94 kHz instead of the normal 143 and
  about 7.12 kHz.  This approximately 2.5% measured sample-rate reduction was
  physically acceptable.  The OPL plan may make the same deliberate trade,
  but must measure it and remain inside the 10% limit below.

## Feasibility guards

### G0: establish and lock the baseline

Before changing the format or player, add a reproducible C-cosim report for
the current library player.  Record:

- exact instructions and cycles in one sample-loop iteration;
- cycles for an empty frame boundary;
- minimum, mean, 99th-percentile, and maximum frame cycles for representative
  DOOM tracks;
- effective sample and music-frame rates;
- player end address, mutable-state bytes, stack margin, and largest JPS file;
- reference WAV hashes for unchanged JPS v1 fixtures.

All later percentage limits are relative to this recorded baseline, not to an
estimate in this document.

### G1: preserve the hot-loop structure

The normal sample-loop instruction sequence must remain unchanged.  CI should
compare either the loop bytes or a disassembly of the bounded loop.  A
hot-loop instruction change requires a separate design decision and physical
qualification; it cannot enter as part of an envelope or LFO patch.

The number of iterations per frame may be reduced deliberately to pay for
frame-boundary effects while keeping the music clock near 50 Hz.  It must be
selected from cycle-model measurements, recorded in the generated song, and
must still pass G2.  With the present 143-iteration VGZ baseline, 129
iterations is the approximate 10%-reduction boundary; the effective measured
sample rate, rather than this rounded iteration count, is authoritative.

### G2: bound the accepted sample-rate trade

For a feature to be enabled by default in VGZ library songs:

- the measured effective sample rate must remain at least 90% of the G0 VGZ
  baseline;
- with the current approximately 7.12 kHz VGZ rate, the provisional hard floor
  is approximately 6.41 kHz;
- all newly enabled OPL work is combined when applying this limit--envelope,
  tremolo, vibrato, pitch handling, Escape polling, and worst normal row work
  are not granted separate 10% budgets;
- the music-frame rate and full-song duration must remain within 1% of the
  source timing after selecting the sample count;
- the worst enhanced frame must be measured and must not produce a visible
  missed sample batch, timing runaway, or audible periodic click;
- phase-step tables must be regenerated from the measured enhanced sample
  rate, so the accepted sample-rate change cannot detune every note.

At 1.70 MHz, a nominal 50 Hz frame has about 34,000 cycles.  A 10% reduction
in sample rate corresponds to allowing roughly 11.1% more total cycles per
fixed-size sample batch, or about 3,800 cycles per nominal frame as a rough
upper orientation value.  In practice the implementation should reduce the
sample iterations enough to retain the 50 Hz music clock, just as the accepted
MOD path uses 139 instead of 143.  The measured rate and duration are
authoritative, not this estimate.  If three-channel envelope plus LFO
processing falls below the 90% floor, it is not shipped in that form.

### G3: no invisible quality trade

An implementation may lower `FRAME_SAMPLES` within G2, but the change must be
explicit in generated metadata, cycle reports, and old/new physical A/B
listening.  It must not omit the concurrent drum fetch, disable Escape, or
reduce the tone frequency range to buy cycles.  The default response to a
failed 90% sample-rate gate is to simplify or precompute the effect.

### G4: bounded target state and code

The assembler map must prove that the player still ends below `1800h` and that
the playback stack retains its current safety margin.  New per-channel state
must be enumerated in the design before assembly.  There may be no unbounded
tables, per-song generated code, dynamic allocation, multiplication, division,
or host-style OPL register engine on the target.

### G5: bounded song data

The preferred soft ceiling is 30 KiB per JPS file, leaving diagnostic and
format-growth margin; 32,767 bytes is the hard existing limit.  A fallback
which emits volume or pitch commands on every 50 Hz frame must be measured
against this ceiling over the longest track.  If it does not fit, use compact
runtime state, compress repeated patterns, split the representation, or omit
the inaudible effect.

### G6: retain backward compatibility

Existing `JPS\1` library songs must remain accepted and render identically.
Enhanced data should use `JPS\2` with explicit capabilities.  A v1 song must
not pay the enhanced frame cost.  Unsupported flags or malformed packets must
be rejected before playback rather than being interpreted approximately.

### G7: generality and confidence

No production rule may mention a song, track number, source filename, or a
single observed instrument signature.  Every conversion rule needs either:

- an OPL-register semantic justification;
- a measurement from the accurate host oracle; or
- a documented, pack-wide perceptual allocation rule.

If source behavior cannot be explained confidently, preserve the current
conversion and report the case.  Do not tune random constants until one song
sounds less wrong.

### G8: host and physical validation

C-cosim is the timing and regression authority, but not the final sound
authority.  A feature is complete only after old/new/reference renders and a
short physical CS00000 A/B test.  Pack-wide conversion must also complete
without new special cases or unsupported-file regressions.

## Proposed architecture

```text
timed VGZ register writes
          |
          v
complete OPL register/state timeline
          |
          +--> Nuked OPL3 isolated reference renders
          |
          v
logical voice reconstruction and perceptual ranking
          |
          v
three pulse voices + percussion + compact JPS v2 automation
```

The host is allowed to do expensive work.  It should calculate nonlinear OPL
envelope timing, pitch-dependent `KSR` behavior, logarithmic level conversion,
operator audibility, and fitted automation.  The 8080 should receive only
small integer increments, targets, flags, and table indices.

## Host-side OPL analysis

### Complete register model

Extend `import_jukupoly_vgz.py` to retain both operators' `20h`, `40h`, `60h`,
`80h`, and `E0h` register groups, channel `A0h`, `B0h`, and `C0h`, global
tremolo/vibrato depth, four-operator enable, rhythm state, and OPL3 routing.
Process writes at their original VGM timestamps.

Build synthetic VGM fixtures which isolate:

- each attack, decay, sustain-level, and release extreme;
- `EGT` held and percussive forms;
- key-off release and retrigger;
- `KSR`, `KSL`, and representative `TL` values at low and high notes;
- shallow and deep tremolo and vibrato;
- pitch-register writes during a held note;
- additive and FM connection, feedback, multiplier, and waveforms;
- OPL rhythm and four-operator mode, even while target support remains absent.

### Accurate host oracle

Integrate a pinned, attributed Nuked OPL3 revision as a build-time analysis
dependency or tool.  It should be able to render the complete mix and each OPL
channel in isolation.  At 50 Hz analysis points, derive:

- fundamental pitch and instantaneous pitch deviation;
- perceptual/RMS level and attack energy;
- key and envelope state;
- effective tremolo depth;
- whether modulator changes primarily affect loudness or timbre.

The oracle result is test evidence, not data that must be stored verbatim in
the song.

### Logical voices

Do not equate one OPL channel with one musical voice.  Group channel segments
when key times, pitch contour, note changes, and envelope motion are strongly
correlated.  Layered same-pitch instruments may become one logical voice, or
two detuned physical voices only when a channel is genuinely spare.  A melody
which migrates between OPL channels should retain continuity.

Voice allocation should rank onset/attack preservation, melodic continuity,
bass and lead roles, perceptual energy, and recent ownership.  The result must
be deterministic and inspectable in a JSON trace.

## Target representation

### Envelope

Do not translate raw OPL rate nibbles directly into the current arbitrary
Juku speed numbers.  OPL rates are nonlinear and may be pitch-dependent.
Instead, use the oracle to fit a compact attack/decay/sustain/release curve at
the 50 Hz target rate and serialize already-resolved targets and increments.

The proposed player state for each channel is:

- key/envelope stage: off, attack, decay, sustain, or release;
- an internal level or attenuation accumulator;
- current stage target and precomputed increment/timing mask;
- 4-bit mapped output level;
- optional tremolo and vibrato enable/depth.

An 8-bit internal envelope is acceptable only if its mapping and update fit G2.
It is intended to reduce rounding error; it does not imply 8-bit speaker
amplitude.  A cheaper piecewise 4-bit or masked update is the fallback.

Key-off must start release instead of immediately deleting the voice.  `EGT`
must decide whether a keyed note rests at sustain or continues its percussive
decay.  Attacks shorter than one 20 ms frame may correctly quantize to an
immediate attack.

### Tremolo

OPL tremolo uses a shared-running LFO with per-operator enable and global
depth.  Implement at most one fractional phase accumulator and a small fixed
table.  Per logical voice, store only enable and precomputed effective depth.
If tremolo exists only on an FM modulator and the oracle shows mainly a timbre
change, do not falsely turn it into large square-wave amplitude modulation.

The 3.7 Hz source LFO has about 13.5 target frames per cycle at 50 Hz.  A
fractional accumulator is required so it does not become an incorrectly
rounded fixed-period oscillator.  Shallow modulation which cannot survive the
4-bit output mapping may be omitted, but that decision must come from the
quantized oracle comparison.

### Vibrato

Use one shared fractional vibrato phase and a small OPL-shaped lookup table.
The importer precomputes the shallow/deep phase-step deviations for each base
note.  At the frame boundary, the player selects a signed delta and forms the
temporary step used for the next sample batch.  It must retain an unmodulated
base step so vibrato cannot accumulate into pitch drift.

The pinned DOOM source LFO is 6.068835788 Hz, or about 8.24 target frames per
cycle at 50 Hz.  Its 16-bit target phase increment is 7,955.  This is coarse
but representable.  Runtime multiplication by the current phase step is not
allowed; if the precomputed-delta update misses G2, use a still smaller table
or host-baked sparse pitch automation.

### Mid-note effects and legato

Preserve writes to frequency and key registers while a note is active.
Distinguish an actual key-off/key-on retrigger from a pitch change with the key
held.  Reuse the existing slide/portamento mechanism only after cycle and
semantic review; the standalone MOD-effect implementation is not automatically
enabled for library songs.

### Timbre-related fields

Connection, multiplier, feedback, waveform, and operator envelopes must inform
host-side loudness, grouping, and salience.  They do not justify claims of FM
timbre reproduction.  Possible later reductions include spending a spare
pulse channel on a detuned layer or converting a short attack/rhythm sound to
the existing percussion path.  Each consumes voice or memory budget and is a
separate gated feature.

Four-operator and hardware-rhythm sources should first be recognized and
reported accurately.  Later, four-operator output may be collapsed from an
isolated oracle render, and hardware drums may be mapped to documented sample
templates.  Neither is part of the first implementation milestone.

## Implementation milestones and gates

### M0: measurement harness

Produce the G0 baseline, loop-byte guard, map/RAM report, and cycle
distribution.  No player feature work begins until this is reproducible in
one command.

Exit gate: repeatable baseline on CI and current representative songs.

Status on 2026-09-01: **complete**.  The generated
[`OPL-BASELINE.json`](OPL-BASELINE.json) and
`sync/jukupoly_baseline_check.sh` cover four complete committed-source songs.
The library player measures 7.070–7.132 kHz, so each future enhanced fixture
must remain at or above 90% of its own recorded v1 rate.  The report also locks
the 64-byte hot-loop hash, observed sample/frame/boundary cycle distributions,
player and stack margins, JPS sizes, mutable player bytes, and deterministic
reference-WAV hashes.

### M1: register trace and oracle

Implement complete timed OPL state and synthetic fixtures; pin Nuked OPL3 and
generate per-channel reference traces/renders.

Exit gate: synthetic fixture results agree with the oracle for key timing,
pitch, envelope direction, and LFO presence.  This milestone changes no Juku
output.

Progress on 2026-09-01: **complete**.  `opl_trace.py`
retains every ordered raw write and decodes operator envelope/LFO flags,
channel pitch/key/connection/routing, key transitions, global depth/rhythm,
OPL3 mode, and four-operator pairing.  `--opl-trace-output` exposes this
without changing conversion output.  A synthetic VGM regression covers both
operators, live pitch, key-on/off, deep AM/VIB, all rhythm bits, stereo, and
four-operator state.  Unmodified Nuked OPL3 is pinned at commit
`765ec962e473aeb767e4cba74ffdc8f588ffbfe8` as a host-only oracle.  Its
synthetic agreement test proves key and pitch timing, envelope direction and
release tail, LFO progression and audible modulation, and per-channel
two-operator isolation.  No Juku binary or score changes in this milestone.

### M2: logical voice reconstruction

Add general layer grouping, cross-channel continuity, and inspectable
allocation reasoning.  Run it on The Imp's Song, Dark Halls, Suspense, and the
whole DOOM/DOOM II set.

Exit gate: no song-specific rule; no pack-wide regression in important note
onsets; The Imp's Song layers are explained as logical voices rather than
forced by signature.

Progress on 2026-09-01: the first analysis-only slice is complete, but M2's
exit gate is **not** yet complete.  `opl_voices.py` reconstructs every keyed
segment and live pitch point, assigns a complete semantic patch identity, and
reports high-confidence same-pitch layer candidates plus same-patch
cross-channel continuation candidates with explicit reasons.  The importer
exposes this as `--opl-voice-output` without changing score allocation.
Synthetic guards cover layers, live pitch, channel migration, chord rejection,
and valid JSON.

The analyzer completed both local Doom pack archives (SHA-256
`04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a` and
`3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365`):
44 tracks, 159,398 keyed segments, 37,797 layer candidates, and 21,989
continuation candidates in 10.75 seconds.  The large continuation count is
evidence that local same-patch adjacency alone is ambiguous, especially for
chords.  These edges therefore remain evidence rather than assignments until
a global, deterministic allocator and onset-regression check exist.  No
target code, score, sample rate, or sound changes in this slice.

The second analysis-only slice replaces ambiguous edge-by-edge choices with a
deterministic maximum-cardinality, minimum-cost one-to-one match at each exact
key boundary.  Cost is lexicographic: retain the complete patch first, retain
the hardware channel second, prefer known and smaller pitch motion third, and
then minimize the key gap.  Same-pitch layers are collapsed before matching,
and their keyed spans must overlap; this prevents adjacent short repetitions
from being mislabeled as simultaneous layers.  Every accepted continuation
records the decision fields and human-readable evidence in the v2 voice JSON.

`tools/report_opl_voices.py` makes the two-pack measurement reproducible.  On
the hash-identified archives above it reduced the 159,398 physical keyed
segments to 123,347 logical notes, then made 13,151 one-to-one continuation
assignments forming 110,196 provisional voice chains.  Of those assignments,
13,028 migrate across an OPL hardware channel and 120 retain a hardware
channel across a semantic patch change.  The complete report fingerprint is
`53ebe84878b16e2cc1f42ed3bdc993f493779496bc18826c92116c66c4d02f82`.
These are still analysis chains, not three-voice Juku allocation: onset
salience and pack-wide old/new allocation comparison remain required before
M2's exit gate can pass.

Final M2 progress on 2026-09-01: **complete**.  The analysis-only three-voice
allocator ranks the generic evidence in a documented order: v1 compatibility,
new onset and attack, logical-voice continuity, bass/lead role, logarithmic-TL
level, sustained-envelope evidence, and remaining duration.  It deduplicates
equal target pitches and never selects more than three.  “Important onset” for
the no-regression gate is defined reproducibly as a source logical-note onset
which the shipping v1 reducer already retained; those onsets rank first, so
the new policy can add information but cannot silently trade existing musical
content away.

The v2 pack report proves this over every track in both hash-identified packs:
75,703 distinct classified melodic source onsets, 53,286 retained by v1,
69,062 retained by the provisional allocator, 15,776 gained, and **zero** v1
onset regressions.  The Imp's Song specifically collapses 2,565 keyed segments
through 1,113 layer relations to 1,764 logical notes; it preserves all 506 v1
source onsets and adds 6.  Dark Halls preserves all 2,341, and Suspense
preserves all 1,210 while adding 162.  The full deterministic report fingerprint
is `213eb7ad4db98535a4d1567cbaed47beee61007dbef8c65db0447988a7e94808`.
The importer includes every frame decision and its reasons in
`--opl-voice-output`; the score remains byte-identical with or without that
option.  No filename, track, or instrument special case was added to the new
analysis.  M2 changes no target code, JPS data, sample rate, or audio; M3 is
the first gated target-side vertical slice.

M3 fixture preparation exposed one generic M2 eligibility gap.  The Imp intro
really begins at sample zero as four detuned, pitch-aligned, sustained OPL
channels; it was absent only because an evolving patch used at one keyed pitch
cannot pass v1's distinct-pitch signature heuristic.  Voice-evidence schema
v3 therefore admits an otherwise unclassified logical note only when all four
guards hold: at least two channels already passed the strict layer relation,
the keyed span lasts at least 50 analysis frames (one second), its pitch is
finite, and OPL `EGT` supplies sustained-envelope evidence.  Eligibility JSON
records every reason.  Synthetic negative guards exclude a 49-frame layer, a
single long channel, and a long non-sustained layer; this is not a filename,
track-number, or patch-signature override.

The v3 two-pack rerun recognizes 156 such logical notes among 44 tracks.  It
raises eligible source onsets from 75,703 to 75,846 and provisional retained
onsets from 69,062 to 69,140 while preserving all 53,286 v1 onsets, with zero
regressions.  The Imp allocation now begins at frame zero on MIDI F#2 and
preserves all 506 protected Imp onsets.  Its gain rises from six to 14; Dark
Halls and Suspense retain their preceding onset counts.  The complete report
fingerprint is
`26f0e6d09848cbee34755b247057092dd9defea435781a9e5cedbd5acb939b55`.
This remains host-only evidence: it does not relax G1--G8 or claim that the
target envelope fit has succeeded.

### M3: JPS v2 envelope-only vertical slice

Add backward-compatible `JPS\2`, key-off release, and compact fitted envelopes.
Do not add LFOs yet.  Convert a short synthetic suite and a 30-second Imp's
Song excerpt.

Exit gate: G1--G8 pass; v1 renders remain identical; the Imp intro is no
longer a constant full-level beep; release timing and envelope direction match
the reference after 50 Hz/4-bit quantization.

If G2 fails, first replace expensive envelope math with precomputed masks or
piecewise segments.  If that fails G5, retain v1 conversion for the affected
track and stop this milestone rather than crossing the 10% sample-rate limit.

Progress on 2026-09-01: the implementation contract is recorded in
[`JPS2-ENVELOPE-DESIGN.md`](JPS2-ENVELOPE-DESIGN.md).  It fixes the v2 header,
one-byte-per-note envelope extension, already-fitted 4-bit levels/rate codes,
15-byte total channel-state growth, key-off release semantics, and a dispatch
scheme in which v1 retains its exact frame routines.  Target implementation
and measurement remain pending; this design alone does not satisfy M3.

The first host-format slice is complete.  `build_jukupoly.py` now validates
`jukupoly-song-v2`, rejects raw/unknown envelope fields and incompatible MOD
effects, encodes already-resolved peak/sustain levels and three fitted rate
codes, and assembles the fixed-address `JPS\2` header/capability byte.  The
synthetic regression checks exact row bytes and malformed inputs.  All v1
generated sources, binaries, baseline profiles, and WAV guards remain
unchanged.  At that checkpoint the library deliberately still rejected v2
until the separately guarded `-P4=1` player slice was implemented.

The target-side synthetic checkpoint is now complete.  The isolated
`-P2=1 -P4=1` player accepts both v1 and envelope-capability v2 songs, dispatches
v1 to the frozen routines, and executes attack, decay, keyed sustain,
non-sustaining automatic release, key-off tails, and delayed phase-step
clearing for all three channels while percussion remains active.  Its strict
preflight walks every v2 row, descriptor, and PCM extent before playback; five
independent corruptions are rejected with zero PIT writes.  The preflight work
also exposed and corrected a stale-condition-code bug in the enhanced
loader's verifier return path.

The committed [`OPL-ENVELOPE-M3.json`](OPL-ENVELOPE-M3.json) measures a
4,537-byte enhanced player ending at `12B9h`, 49 bytes of declared player
state, an unchanged 64-byte hot-loop hash, and 1,351 bytes of remaining player
window.  The 46-frame three-envelope-plus-percussion fixture uses an explicit
141-sample batch and measures 7,044.10 samples/s and 49.958 frames/s; its
selected frozen Doomgate comparison floor is 6,401.15 Hz.  The worst frame is
42,670 cycles.  The
enhanced player's v1 Doomgate timing and audio-event profile remains exactly
equal to the frozen profile; image size, self-modification bookkeeping, and
the report label are intentionally compared separately.

At that checkpoint M3's real-song gates were still open.  The 30-second Imp
old/new/reference comparison is now complete below; longest affected JPS size
and duration evidence plus physical CS00000 A/B listening remain pending.
Until those pass, the Doom library still emits v1 songs and the implemented v2
path remains a reversible progressive layer.

The first host-fitting primitive is also complete.  `opl_envelope.py` models
the target's exact parse/update ordering and global rate-mask phase, then
performs a deterministic grid fit over only the representable JPS v2 packet
space.  It recovers target-generated keyed and percussive envelopes exactly.
An isolated pinned-Nuked reference is reduced to relative 20 ms RMS levels
while absolute peak loudness remains an independent policy input; its first
guarded fit has 1.375 levels mean absolute error and six levels maximum error.
The error is reported rather than disguised: the reference has Yamaha's
accelerating attack while the affordable target state changes by one mixer
level per eligible frame.

The pinned-oracle probe now also exports each operator's post-envelope
`eg_out` attenuation and the channel connection bit.  Unlike raw `TL`, this
value already includes the running Yamaha envelope, TL, KSL, and tremolo.
The host maps its documented 0.1875 dB units to linear amplitude, uses the
carrier alone for FM connection or the capped sum for additive connection,
then quantizes to Juku's 4-bit range.  This supplies a deterministic absolute
level policy for the real-song fit without pretending that an OPL waveform
and the Juku one-bit speaker have identical timbre.  The previous isolated
PCM/RMS path remains a useful independent shape comparison.

The oracle bridge can emit this probe state for all 18 channels in one pass.
Its all-channel rows are verified against the existing isolated-channel form,
so a 30-second real-song fit does not require 18 redundant OPL renders.

The real-song M3 slice is now implemented by `opl_enhanced.py` and the guarded
importer flags `--seconds`, `--enhanced-envelopes`, and `--opl-oracle`.  It
uses complete-source instrument classification even for an excerpt, maps the
M2 allocation to stable target channels, sums only proven logical layers,
fits post-EG oracle attenuation, and carries the unchanged v1 percussion
timeline into JPS v2.  Synthetic regressions cover sparse allocation expansion,
logical-voice channel continuity, key-off, percussion concurrency, probe fit,
and strict score encoding.

[`OPL-IMP-M3.json`](OPL-IMP-M3.json) is the reproducible 30-second Imp
comparison.  V1's first tone is frame 706 (14.12 s); v2 begins the evidenced
four-layer F#2 at frame zero.  All 13 v1-protected excerpt onsets survive and
two are gained.  Sixteen selected logical notes average 0.601 4-bit mixer
levels absolute error; the maximum is eight on the intro because its repeated
mid-note OPL level evolution cannot be represented by one ADSR packet.  Two
notes have significant renewed keyed articulation and exceed the two-level
per-note mean-error delivery limit.  Significant net attack, decay, and
release directions match the quantized oracle, but this weaker condition no
longer qualifies the candidate.

The first real-song build used the synthetic fixture's 141-sample batch and
was rejected: 30 seconds rendered in 29.495 seconds, outside G2's 1% duration
limit.  The measured 143-sample build with a 7,170 Hz phase table renders in
29.900 seconds, at 50.168 frames/s and 7,174.0 samples/s.  Its fixture-specific
floor is 6,480.8 Hz.  The JPS grows only from 1,290 to 1,341 bytes, the player
remains 4,537 bytes ending at `12B9h`, and the frozen sample-loop hash remains
exact.  Target v1/v2 WAV hashes and the pinned-oracle reference WAV hash are
recorded in the report.

The longest affected full-song check is now also complete.  An initial Imp
pass found ten significant direction mismatches among 532 selected notes:
nine two-level keyed decays which unconstrained least squares flattened, and
one release too slow to move inside its observed tail.  The real-song fitter
now ranks preservation of net attack/decay/release changes of at least two
4-bit levels ahead of squared error.  Sub-two-level motion remains a reported
approximation and does not acquire extra target machinery.  The guarded pass
has zero significant direction mismatches, 0.655 levels mean absolute error,
and 14 levels maximum error.  Twelve of its 532 notes still fail the renewed-
articulation/error delivery gate.

[`OPL-IMP-FULL-M3.json`](OPL-IMP-FULL-M3.json) records the complete
157.508-second source pass: all 506 protected onsets retained, 14 gained,
9,978-byte v2 JPS versus 8,537-byte v1, 7,087.5 samples/s versus a 6,460.3 Hz
floor, 49.563 frames/s, and 158.888 seconds rendered duration.  The 0.88%
duration error passes G2; the player map and frozen sample loop remain exact.

Physical CS00000 listening on 2026-09-01 confirmed that the low lead entered
immediately but did not reproduce the source's quick fade.  The first logical
note is four same-pitch OPL layers with staggered renewed volume rises; one
compact ADSR instead becomes a nearly constant-volume compromise.  This
closes M3 as a useful negative result for that representation.  The qualified
delivery is unchanged v1, and any later multi-articulation attempt must pass
the same source-independent gate without violating G1--G8.

The same audit fixed a boundary error in the diagnostic: `key_off_frame` is
the first release sample, not the final keyed sample.  The direction check now
ends keyed decay at `key_off_frame - 1`, with a regression proving that an
otherwise flat hold is not reported as decay merely because immediate release
drops the next sample.  This is host qualification only and consumes no target
cycles, bytes, or sample-rate budget.

### M4: tremolo

Add the shared tremolo phase and per-voice effective depth.

Exit gate: synthetic rate/depth test, cycle gate, long-track size gate, and no
false large modulation when only an inaudible modulator has AM enabled.

If G2 fails, omit sub-quantization tremolo and use compact host-baked changes
only where audible and affordable.

First host-only progress on 2026-09-01: `opl_tremolo.py` implements a bounded
shared 16-step attenuation triangle with a 16-bit phase accumulator.  Its
4,850-unit increment produces 37.0 cycles in ten seconds at the 50 Hz target
clock, rather than rounding 3.7 Hz to an incorrect integer frame period.  The
only representable depths are zero through three 4-bit mixer levels, and depth
zero wins equal-error fits.  Synthetic guards recover an exact depth-three
curve and reject an inaudible-modulator false positive.

The pinned oracle now exposes each operator's actual AM-enable state as well
as post-EG attenuation.  A direct target-amplitude candidate requires carrier
AM, or modulator AM in additive connection mode, plus measured improvement in
the quantized oracle fit.  AM only on an FM modulator is timbre evidence, not
permission to invent square-wave volume modulation.  A pinned-Nuked test
proves carrier AM produces a fitted nonzero depth while otherwise identical
FM-modulator-only AM leaves the semantic carrier trace unchanged and fits
depth zero.

[`OPL-TREMOLO-M4.json`](OPL-TREMOLO-M4.json) records the complete two-pack
semantic scan: 102,172 melodic key-ons, of which 20,772 in 27 tracks have a
direct AM path, 12,071 have only an FM-modulator path, and 69,329 have none.
There are 89 direct-AM melodic signatures and 33 modulator-only signatures;
the deterministic fingerprint is
`c8924b6aca4fed55983d9fc9d98130c05be485180b1a90ed5f0262af0d80ff7a`.
This prevalence justifies continuing M4 but does not enable target tremolo.

On the 30-second Imp fixture only one of 16 selected notes is a semantically
valid depth-one candidate, improving squared error by nine over 88 frames
(0.10 per frame).  A second mathematical depth-one fit is rejected because
its source has no direct AM path.  The Imp result is too small by itself to
justify player code; the next gate is quantized-oracle benefit on representative
direct-AM tracks, followed by a bounded ABI/cycle experiment if warranted.

The v2 pack report now includes that exact quantized-oracle gate.  For each
active melodic physical channel it analytically removes Nuked's live tremolo
attenuation from `eg_out`, independently quantizes the with/without forms to
four bits, and discards PCM output.  Across both packs, 69,978 of 405,454
direct-AM channel-frames change, totaling 70,188 mixer levels with maximum
depth two.  All 232,212 FM-modulator-only channel-frames change by exactly zero.
Every one of the 27 direct-AM tracks has at least one surviving frame.  The v2
report fingerprint is
`e8e2b5e69bf62f80619242b09411e7b8c55b4fbe08616f2ac6641bab07525ab0`.

Sequential fitting was then rejected as an M4 decision method: the envelope
can absorb average AM attenuation into its sustain level, making a later
attenuation-only LFO appear useless.  `fit_joint_envelope_tremolo` searches the
same strict envelope packet space jointly with depths zero through three.
The pinned synthetic fixture recovers its exact envelope and depth.
[`OPL-TREMOLO-CANDIDATE-M4.json`](OPL-TREMOLO-CANDIDATE-M4.json) records a
real “Opening to Hell” candidate at 62.0 seconds: source AM changes 53 of 114
reference frames by one level, and joint depth one reduces squared error from
222 to 180 while preserving significant stage directions.  Mean absolute
error rises from 0.842 to 0.930 while maximum error falls from five to four;
all three metrics are retained so the improvement is not overstated.

This is enough evidence for a reversible target ABI/cycle experiment, not for
default enablement.  M4 target work must fit the combined envelope+tremolo 10%
budget, retain an off path with no per-frame cost for v1 and non-AM v2 songs,
and undergo physical A/B before the host candidate policy is accepted.
The byte/state/cycle contract and explicit rollback points are recorded in
[`JPS2-TREMOLO-DESIGN.md`](JPS2-TREMOLO-DESIGN.md).

The reversible `-P5=1` target slice now passes its synthetic gates.  The
five-byte tone packet does not grow; depth uses two reserved bits, per-channel
depth reuses existing state, and only a two-byte shared phase is added.
[`OPL-TREMOLO-TARGET-M4.json`](OPL-TREMOLO-TARGET-M4.json) records a
cycle-identical v1 and capability-`01h` off path, the unchanged hot-loop hash,
a 4,863-byte player ending at `13FFh`, 51 state bytes, and 195/258/374 added
boundary cycles for zero/one/three active depths.  The selected three-depth
fixture uses 140 samples per frame and measures 6,962.7 Hz, 49.734 frames/s,
0.54% duration error, and a 42,135-cycle worst frame against the 6,401.1 Hz
floor.  This completes only the synthetic ABI/map/cycle gate; representative
render, long-track, default host-policy, and physical-listening gates remain
open.

The first real target/render gate is also complete for a bounded 66-second
“Opening to Hell” excerpt.  The opt-in, song-independent policy requires a
direct AM path, a source AM change which survives 4-bit quantization, and a
positive joint fit.  It emits ten of 61 selected notes, including the
previously reported note 100.  [`OPL-TREMOLO-REAL-M4.json`](OPL-TREMOLO-REAL-M4.json)
records identical 2,090-byte comparison JPS sizes, a 7,100.2 Hz effective
sample rate, 49.652 frames/s, 0.70% duration error, a 40,943-cycle worst frame,
and envelope/tremolo/Nuked WAV hashes.  The per-song 143-sample batch is
measured rather than inherited from the more expensive synthetic fixture.
The optional converter path is general and explicit; complete-track and
physical-listening gates remain open, so it is not the default.

The complete-track M4 gate is now closed by
[`OPL-TREMOLO-FULL-M4.json`](OPL-TREMOLO-FULL-M4.json).  The full 279.98-second
“Opening to Hell” conversion selects 592 logical notes and emits 38 shallow
direct-AM candidates, with maximum depth two, 1,670 source frames changed
after 4-bit quantization, and 1,734 total squared-error improvement.  The
controlled envelope and tremolo JPS files are both 10,504 bytes.  At the
measured 142 samples/frame and 7,100 Hz phase table, the tremolo profile is
7,059.7 samples/s, 49.716 frames/s, and 281.577 seconds (0.57% long), with a
43,141-cycle worst frame.  The sample-loop hash, `13FFh` player end, format
capabilities, and all recorded G1--G5 gates pass.  Automated M4 size, timing,
and render qualification is complete; physical CS00000 A/B remains open, so
the feature stays explicitly opt-in and the envelope/v1 paths remain the
fallback.

### M5: vibrato and held-note pitch writes

Add the shared vibrato phase, temporary phase-step modulation, and generic
mid-note pitch handling.

Exit gate: no mean pitch drift, correct approximate LFO rate, no low-note
underflow, no high-note 15-bit overflow, and all cycle/size gates pass.

If G2 fails, reduce table/update complexity or emit sparse precomputed pitch
changes.  A measured sample-count reduction is permitted only while the
combined enhanced player remains at or above 90% of the baseline rate.

First host-only M5 evidence is recorded in
[`OPL-PITCH-M5.json`](OPL-PITCH-M5.json).  `opl_vibrato.py` reproduces Nuked's
eight-position F-number deviations exactly and derives every temporary target
step from an immutable base, preventing cumulative pitch drift.  The oracle
now exposes each operator's VIB enable and effective post-vibrato F-number;
the synthetic regression agrees at every 50 Hz probe.

Across both known DOOM packs, 30,118 of 102,172 melodic key-ons in 30 tracks
have a conservative direct common-pitch vibrato path.  Another 13,466 have
VIB only on an FM modulator and are timbre-only; 270 use one-sided additive
VIB and are a partial two-pitch mixture, so neither class may enable whole-note
target vibrato.  After excluding same-timestamp writes which end in key-off or
retrigger, nine tracks contain 7,264 coalesced held-key melodic pitch events:
6,034 move by 5--50 cents, 1,176 by less than five cents, and 54 by at least 50
cents.

The existing M2 allocation selects 21,017 of 22,829 conservative direct-
vibrato logical notes at some point and retains 6,495 of 7,264 held-pitch
events at the exact event frame.  Its protected-v1 regression count remains
zero.  This closes M5's source-prevalence and allocation-survival gates only.
No JPS packet, target state, CPU cycle, or default conversion has changed; the
next gate is guarded host encoding followed by a bounded target experiment.

That proposed contract is now recorded in
[`JPS2-PITCH-DESIGN.md`](JPS2-PITCH-DESIGN.md).  Held pitch is deliberately
first because existing JPS2 legato packets can replace the immutable base step
without any new target code.  Runtime vibrato is a separate proposed
capability with one conditional `delta-1` byte, three channel delta bytes, a
two-byte shared phase, exact low/high preflight, and a combined M4+M5 cycle
gate.  This is a reversible design checkpoint; no capability or assembler
implementation is accepted yet.

The host-format portion is now implemented.  The compiler emits the
conditional `delta-1` byte and capabilities `05h`/`07h`, proves each base step
plus and minus its peak delta stays in `1..7FFFh`, and rejects malformed or
mis-capabilitied fields.  Omitted vibrato and capability `03h` remain byte-
identical.  Standalone target assembly is deliberately refused, and the M4
library player rejects capability `05h` before any PIT write.  This completes
only the reversible format/rejection gate; runtime vibrato remains separate.

The host-baked held-pitch stopping point is now implemented and qualified on
the complete 96.513-second “At Doom's Gate” source.  The opt-in generic policy
emits 566 existing legato packets only for target-step changes while a logical
note retains its target channel.  It retains all 1,080 source onsets, misses
zero protected onsets, grows the fixed-pitch control from 14,073 to 17,215
JPS bytes, and continues to use capability `01h` and the unchanged 4,537-byte
M3 player.  [`OPL-PITCH-REAL-M5.json`](OPL-PITCH-REAL-M5.json) records zero
new target code/state and an exact frozen sample-loop hash.

The first 143-sample attempt was correctly rejected: it measured 48.118 Hz
music timing and 100.296 seconds, 3.92% longer than the source.  The guarded
fallback regenerates both score steps and metadata for 137 samples/frame and
a 6,850 Hz phase table; it measures 6,859.2 samples/s, 50.067 frames/s,
96.391 seconds (0.13% short), and a 43,380-cycle worst frame, above the shared
6,401.1 Hz floor.  A regression requires the recorded phase-step generation
rate to equal the declared table rate, specifically guarding against a
metadata-only calibration which would detune the whole track.  Automated
held-pitch size/timing/render gates pass; physical A/B remains open and the
feature stays opt-in.  This independently useful result remains valid even if
the later runtime-vibrato experiment fails.

The next reversible checkpoint implements only M5's experimental parser,
preflight, and bounded state under `-P6=1`.  A separate pitch packet path
preserves exact JPS v1 and capability-`01h`/`03h` execution profiles.  It
validates the conditional byte, advertised feature bits, mode, and both
15-bit bounds before I/O.  Synthetic corruptions for mode 3, underflow,
overflow, a missing delta, and unadvertised pitch/tremolo all stop with zero
PIT writes and zero keyboard polls.

[`OPL-VIBRATO-PARSER-M5.json`](OPL-VIBRATO-PARSER-M5.json) records 4,993 bytes
and 54 state bytes for pitch-only, and 5,349 bytes with exactly 56 state bytes
for the combined M4+M5 parser.  The latter ends at `15E5h`, still below
`1800h`, with 539 bytes of margin; all sample-loop hashes remain exact.  Its
trace covers deltas 1/256, legato replacement, mode disable, and release
semantics.  This is not runtime acceptance: the phase remains inactive,
temporary steps are not applied, and the normal build still refuses
capability bit 2.  M5 step 4 is the next independent gate.

The separately gated `-P7=1` runtime experiment now completes M5 steps 4 and
5 on synthetic fixtures without enabling the normal converter.  It derives
all three temporary phase steps from immutable bases before advancing the
shared `1F13h` phase, implements the exact symmetric eight-position shape with
bounded adds/subtracts, and keeps every instruction outside the frozen sample
loop.  A reuse guard seeds prior-song base steps and proves initialization
clears them before the first row; the 18-frame traces for both capability
`05h` and combined `07h` cover deltas 1/256, legato replacement, release, and
nonaccumulating bases.

[`OPL-VIBRATO-TARGET-M5.json`](OPL-VIBRATO-TARGET-M5.json) records a 5,255-byte
pitch runtime ending at `1587h` with 54 state bytes, and a 5,632-byte combined
M4+M5 runtime ending at `1700h` with exactly 56 state bytes and 256 bytes of
song-window margin.  JPS v1 and capabilities `01h`/`03h` remain execution-
identical and every hot-loop hash is exact.  The measured runtime boundary
cost is about 1,359 cycles/frame over matched controls, exceeding the earlier
900-cycle orientation estimate but not the authoritative G2 budget.

The deliberately expensive three-high-step-voice plus percussion fixture
selects 131 samples/frame and a 6,530 Hz phase table for capability `05h`; it
measures 6,532.9 samples/s, 49.869 frames/s, 4.010 seconds, and a 42,713-cycle
worst row.  Combined tremolo depths 1/2/3 plus all three vibratos require the
allowed 129-sample boundary and a 6,450 Hz table; they measure 6,455.4
samples/s, 50.042 frames/s, 3.997 seconds, and a 42,696-cycle worst row.  Both
remain above the shared 6,401.1 Hz floor and retain percussion fetching and
Escape polling.  This closes only the synthetic runtime/map/cycle gate:
representative real-song rendering and physical CS00000 A/B remain open, the
normal assembler still refuses capability bit 2, and host-baked held pitch is
the recorded fallback if either later gate fails.

The first bounded real-song runtime gate is now complete on a 30-second “At
Doom's Gate” excerpt.  The opt-in `--enhanced-vibrato` policy has no track or
instrument special cases: on each selected frame it requires every active
audible operator and logical layer to carry a direct common-pitch VIB path,
requires every layer to resolve to the same bounded target delta, omits
sub-step/mixed/indirect cases, and emits a legato packet whenever the setting
changes while the note remains assigned.  It also requires explicit measured
frame/sample-rate overrides so an uncalibrated conversion cannot silently
enter the experiment.

[`OPL-VIBRATO-REAL-M5.json`](OPL-VIBRATO-REAL-M5.json) records 251 emitted
logical notes, 289 vibrato packets, 156 held-setting updates, all 280 protected
onsets retained, and zero unsafe deltas.  The capability-`05h` JPS is 7,065
bytes versus a separately calibrated 5,894-byte capability-`01h` envelope
control.  At 133 samples/frame and a phase table regenerated at 6,650 Hz, the
runtime measures 6,657.4 samples/s, 50.055 frames/s, 29.967 seconds, a 6.076 Hz
LFO, and a 43,628-cycle worst row.  It remains above the shared 6,401.1 Hz
floor with the frozen sample loop, percussion fetching, and Escape polling.
The 139-sample/6,970 Hz envelope control, target WAV pair, and pinned-Nuked
reference hash are also recorded.  This closes M5 step 6's bounded automated
gate only, with the earlier host-baked pitch and envelope paths as explicit
fallbacks.

The same generic conversion now passes the complete 96.520-second source in
[`OPL-VIBRATO-FULL-M5.json`](OPL-VIBRATO-FULL-M5.json): 908 emitted logical
notes, 1,018 vibrato packets, 520 held-setting updates, every one of 1,080
source onsets retained, and no missed protected onset.  Its 18,133-byte JPS is
below G5's soft ceiling.  The 133-sample/6,650 Hz runtime measures 6,605.7
samples/s, 49.667 frames/s, 97.167 seconds, a 6.029 Hz LFO, and a 44,481-cycle
worst frame.  The frozen sample loop, percussion fetch, and 4,827 Escape polls
remain present.  On 2026-09-01 this exact At Doom's Gate payload completed on
physical CS00000 and the operator assessed it as “sounds decent.”  This closes
the M5 complete-track physical gate for the guarded payload; pack-wide policy
continues under M6's per-track delivery guards.

Before starting the pack run, the exact host envelope search was made cheaper
without narrowing its candidate space.  Parameter tuples which simulate to an
identical 4-bit trace are now scored once, retaining the original complete
score tuple as their deterministic tie-break.  A representative 68-frame fit
dropped from about 0.50--0.57 seconds to 0.28--0.29 seconds.  Regenerating the
30-second runtime-vibrato fixture produced the exact committed
`eba8af46...5267ca` SHA-256, and regressions pin two ambiguous-trace packet
choices.  A bounded 8,192-result cache also reuses only complete identical
reference/search keys; counters are normalized to their semantically complete
low six bits only after the original `0..255` validation.  The cache-enabled
regeneration has the same exact hash.  This is host tooling only; it changes
neither target bytes nor any feasibility allowance.

### M6: pack regression and physical qualification

Build the complete DOOM library and generate old Juku, new Juku, and accurate
OPL reference excerpts for at least The Imp's Song, Dark Halls, Suspense, and
one rhythm-heavy track.  Report note-onset retention, pitch contour, envelope
error after quantization, file sizes, cycles, and duration.

Exit gate: complete C-cosim runs, no new special cases, and CS00000 A/B
confirmation.  Keep old renders and disk image available for comparison until
qualification is recorded.

The first M6 representative profile is now recorded in
[`OPL-M6-REPRESENTATIVE-PROFILE.json`](OPL-M6-REPRESENTATIVE-PROFILE.json).
Neither source pack sets OPL hardware-rhythm mode, so the rhythm-heavy
representative is “The Dave D. Taylor Blues,” whose 2,030 percussion rows are
the largest v1 count in the 44-track library.  The selected set otherwise
follows the named Imp, Dark Halls, and Suspense requirement.  All four exact
oracle conversions retain every protected onset and use no new source,
instrument, or track-specific conversion rule.

The first generic calibrations were rejected rather than normalized away.
Under the combined 5,632-byte player, Imp measured 50.928 frames/s at
139 samples/frame, while Dark Halls and Suspense measured only 48.389 and
48.426 frames/s at 142.  Because these three scores contain symbolic notes and
no held-pitch/vibrato phase steps, the guarded timing-only tool could safely
regenerate their note tables.  It explicitly refuses every explicit-step,
held-pitch, or vibrato score.  The timing-qualified candidate settings were:

- Imp: `143/7100`, 7,087.8 samples/s, 49.565 frames/s, 158.882 seconds,
  9,978-byte capability `01h` JPS;
- Dark Halls: `137/6850`, 6,854.0 samples/s, 50.029 frames/s, 272.002 seconds,
  20,151-byte capability `03h` JPS with six tremolo notes;
- Suspense: `137/6850`, 6,858.5 samples/s, 50.062 frames/s, 172.426 seconds,
  12,969-byte capability `03h` JPS with 29 tremolo notes.

All three pass the shared rate, 1% table/clock/duration, 30 KiB, frozen-loop,
percussion, and Escape gates.  Later physical listening showed that those
checks were insufficient for Imp: 12 fitted notes have significant renewed
keyed articulation which one compact ADSR fits above the two-level per-note
mean-error limit.  Imp therefore takes an 8,537-byte unchanged-v1 fit
fallback.  The Dave Taylor capability-`07h` candidate is 40,983 bytes and is
correctly rejected by the 32,767-byte hard library limit; its existing
30,071-byte v1 JPS is retained as the explicit size fallback.

The excerpt gate is now closed by
[`OPL-M6-REPRESENTATIVE-RENDERS.json`](OPL-M6-REPRESENTATIVE-RENDERS.json).
Each track is independently converted for its first 1,500 frames rather than
blindly inheriting a full-song calibration.  Initial inherited calibrations
were rejected at 50.720--50.938 frames/s for Dark Halls/Suspense and a 1.03%
phase-table mismatch for Imp.  The source-derived accepted settings are Imp
`143/7170`, Dark Halls `138/6950`, Suspense `139/6980`, and Dave Taylor
`135/6750`.

Their complete C-cosim excerpt profiles measure respectively 7,174.0,
6,952.4, 6,984.9, and 6,760.4 samples/s and 50.168, 50.380, 50.251, and
50.077 frames/s.  Every 30-second enhanced JPS is below 5 KiB, every timing,
shared-rate, percussion-descriptor, Escape, and frozen-loop gate passes, and
each v1/enhanced/pinned-Nuked WAV triple has three distinct committed hashes.
The WAVs remain under `out/jukupoly-m6-representative/renders/` for listening.

The next progressive disk gate is now complete.  The generic optional
replacement-manifest path in `build_doom_library.py` validates every JPS2
payload's size, SHA-256, header, capability, source name, pack, and track
number before replacing a v1 delivery; the default 44-track v1 build is
unchanged.  [`M6-REPRESENTATIVE-DELIVERY.json`](M6-REPRESENTATIVE-DELIVERY.json)
selects four qualified full tracks: At Doom's Gate (`05h`) plus Dark Halls,
Suspense, and Opening to Hell (`03h`).  The resulting capability-`07h` player
is 5,632 bytes, and 40 tracks—including Imp and Dave Taylor—remain ordinary
v1 fallbacks.

[`OPL-M6-MIXED-LIBRARY.json`](OPL-M6-MIXED-LIBRARY.json) records the complete
800 KiB disk (`af0f4486...0015bf9`), 630,447 song bytes, and exact capability
distribution `00h:40, 03h:3, 05h:1`.  Every one of the 44 on-disk JPS
files completes a full C-cosim run under the combined player, every catalog
size/hash/capability matches, all four enhanced full-song timing/rate gates
pass, and the hot-loop hash remains exact.  This proves a usable mixed-library
stopping point and cross-version loader compatibility.

The preceding five-enhanced disk (`6f61b809...f350c`) was exercised on
physical CS00000 on 2026-09-01.  At Doom's Gate sounded decent; Dark Halls and
Suspense were acceptable/inconclusive; Opening to Hell and the v1 Kitchen Ace
control executed cleanly without operator assessment.  The Imp low lead
entered immediately but failed the listening gate because it remained nearly
constant in volume instead of fading like the OPL source.  Escape, quit, and
CP/M return all worked with zero retries, resets, writes, or UART errors.  The
corrected disk changes only Imp back to v1: its player and other four enhanced
payloads are byte-identical to the run.  The exact evidence boundary is
recorded in `sessions/cs00000-jukupoly-m6-physical/`; a future exact corrected-
disk smoke is optional, not grounds to pretend the failed payload passed.

M6 is therefore a qualified progressive delivery, not complete enhanced
conversion of all 44 songs.  Broader conversion and a bounded multi-
articulation experiment remain later work.

### M7: optional timbral and unsupported-mode reductions

Only after M6, investigate detuned spare-voice layers, short oracle-derived
attack samples, four-operator collapse, and hardware-rhythm mapping.  Each is
a separate experiment with the same gates.  Failure is an acceptable outcome;
the documented supported subset remains honest.

The first M7 experiment addresses the physically rejected Imp envelope without
adding a target feature.  The opt-in `--enhanced-rearticulation` host path
finds a renewed keyed rise only after a fall and rise of at least four mixer
levels (strictly above the target tremolo's maximum depth three), permits at
most six extra packets per logical note, and re-sends an ordinary same-pitch,
non-legato ADSR packet at each accepted 50 Hz boundary.  It neither changes
the player nor adds per-sample work.  Tremolo-bearing notes are excluded from
this first composition rule.

[`OPL-IMP-REARTICULATION-M7.json`](OPL-IMP-REARTICULATION-M7.json) records the
first 30-second candidate.  Six extra packets across two logical notes reduce
mean envelope error from 0.601 to 0.404 levels and maximum error from eight to
seven; the intro note falls from 2.833 to 1.119 mean error.  All 13 protected
onsets remain, the JPS is 1,383 bytes, and the unchanged 4,537-byte player
measures 7,170.9 samples/s, 50.146 frames/s, and 29.913 seconds.  The frozen
sample-loop hash and every automated delivery gate pass.  This is an offline
candidate only: full-song size/timing, interactions with other capabilities,
and physical CS00000 listening remain required before replacing the v1 Imp
delivery.

The complete 157.5-second candidate also passes the automated gate.  It emits
49 extra packets across 20 of 532 notes, leaves zero notes above the delivery
limit, and produces a 10,293-byte JPS.  C-cosim measures 7,083.9 samples/s,
49.538 frames/s, 158.970 seconds, and a 42,197-cycle worst frame; the player,
memory map, sample loop, percussion, and Escape path are unchanged.  The
compact evidence is committed in
[`OPL-IMP-REARTICULATION-FULL-M7.json`](OPL-IMP-REARTICULATION-FULL-M7.json).
Physical listening remains the decisive open gate.

Synthetic composition guards also cover collisions with held-pitch and
runtime-vibrato updates.  When an articulation boundary coincides with either
setting change, one combined packet carries the new phase data and envelope
but deliberately omits `legato`, so the envelope really restarts.  Ordinary
pitch/vibrato-only updates retain their previously qualified legato behavior.

The hash-locked two-pack discovery scan is committed in
[`OPL-M7-PACK-SCAN.json`](OPL-M7-PACK-SCAN.json).  It converts the first 30
seconds (or each complete shorter source) of all 44 tracks with the same
envelope-only policy and profiles every JPS in C-cosim.  Only two tracks emit
re-articulation: Imp uses six packets, while “Nobody Told Me About id” uses
124 packets across 42 notes.  The latter evidence justified raising the
general per-note bound from four to six; the repeated scan then leaves zero
unrepresented notes in every discovery window.  Thirty-five common-calibration
timing failures remain explicit and are not delivery failures or silently
normalized: the scan is candidate discovery, and any promoted track requires
its own measured timing plus a complete-source pass.

“Nobody Told Me About id” demonstrates that a good opening window is not
enough.  Its recalibrated `139/6950` excerpt passes at 6,924.6 samples/s,
49.817 frames/s, and 30.110 seconds, but the complete source is rejected.
[`OPL-NOBODY-REARTICULATION-M7.json`](OPL-NOBODY-REARTICULATION-M7.json)
records 1,028 selected notes, 724 extra packets, a 13,297-byte candidate, and
otherwise passing timing at 6,912.8 samples/s, 49.732 frames/s, and 179.381
seconds.  Forty-five later notes remain above the per-note error limit and one
significant attack direction is missed.  Delivery therefore stays the exact
8,311-byte v1 payload.  The packet cap is not increased again to hide this
result.

The separate exact mode audit
[`OPL-M7-MODES.json`](OPL-M7-MODES.json) closes two other M7 branches for the
current source packs.  All 44 tracks enable OPL3 new mode, but none writes a
nonzero four-operator pairing mask and none enables hardware rhythm for even
one source sample.  Four-operator collapse and hardware-drum mapping therefore
have zero pack benefit and receive no target code.  The importer continues to
recognize and reject those modes honestly for future sources; this is a
source-scoped no-demand result, not a claim of general support.

Detuned spare-voice restoration, in contrast, has substantial source demand.
[`OPL-M7-DETUNED-SPARES.json`](OPL-M7-DETUNED-SPARES.json) reconstructs the
same protected three-voice allocation for both packs and counts a candidate
only when a selected proven layer quantizes to a phase step distinct from the
logical base at 7,170 Hz while one of the three physical voices is unused.
Thirty-three tracks, 5,303 selected logical notes, 58,922 source frames, and
84,709 duplicate-voice frame slots qualify, with zero protected-onset
regression.  Imp alone contributes 9,157 slots over 5,488 frames, with at most
19.0 cents and 14 target-step units of separation.

The first guarded emission checkpoint is now recorded in
[`OPL-IMP-DETUNED-M7.json`](OPL-IMP-DETUNED-M7.json).  It never dynamically
steals a channel: an episode is eligible only when one logical voice remains
selected contiguously and the required spare capacity persists for the whole
episode.  It replaces that merged logical voice with at most three strongest
source members having distinct, fixed target phase steps and independently
passing oracle-derived envelope fits.  The members use their own measured
4-bit levels rather than copies of the merged envelope.  At episode end the
ordinary allocator releases them before assigning later real onsets.

For the first 30 seconds of Imp, the intro logical voice becomes three members
at phase steps 839, 845, and 848.  Their individual envelopes need six bounded
ordinary ADSR re-triggers in total, so this checkpoint deliberately composes
the already guarded re-articulation policy; another later logical voice uses
the normal two re-triggers.  All protected onsets remain and no selected note
is left above the two-level delivery limit.  The 1,405-byte JPS runs with the
unchanged 4,537-byte player and frozen sample loop at 7,159.9 samples/s,
50.069 frames/s, and 29.958 seconds; its worst frame is 40,690 cycles.  Thus
the episode policy, target encoding, timing, size, and three-way offline render
gate pass without a player/state/hot-loop change.

This is still a progressive experiment, not a library promotion.  Complete-
track conversion and physical CS00000 comparison against both the accepted
v1 fallback and pinned-Nuked reference remain mandatory.  Tracks lacking a
contiguous episode, persistent spare capacity, distinct fixed steps, or a
bounded per-member envelope fit continue unchanged through the ordinary
logical-voice path.

The complete-track gate is now closed offline by
[`OPL-IMP-DETUNED-FULL-M7.json`](OPL-IMP-DETUNED-FULL-M7.json).  The first
attempt exposed overlapping valid episodes which had independently counted
the same spare channel; the compiler's hard three-voice assertion rejected
that score.  The generic fitter now maintains a per-frame reservation ledger
in first-selected-note order.  A later episode is reduced or rejected when
its remaining capacity is insufficient, and a synthetic collision regression
pins that behavior.  Five full-song opportunities are conservatively reported
as `overlapping_episode_capacity` instead of exceeding the hardware.

The accepted full score contains 216 episodes, 217 extra voice reservations,
and 433 independently fitted members.  Their sample-weighted mean envelope
error is 0.322 levels, maximum error is five, and six member re-triggers are
required.  All 506 protected onsets remain, with zero significant direction
mismatch and zero unrepresentable selected note.  Initial `143/7170` timing
was honestly rejected at 49.329 frames/s and 159.642 seconds.  Exact source-
derived regeneration at `141/7050` produces an 11,692-byte JPS and measures
7,049.2 samples/s, 49.994 frames/s, 157.518 seconds, and a 42,597-cycle worst
frame.  The unchanged 4,537-byte player, frozen sample loop, memory limits,
percussion path, and 7,876 Escape polls all pass.  A complete C-cosim render is
retained locally at
`out/jukupoly-imp-detuned-m7/imp-detuned-reart-full.wav`.

Physical comparison is still mandatory before replacing Imp v1 in the mixed
library.  In particular, independent source-member pulse trains can restore
beating and separate fades but cannot reproduce OPL waveform/FM timbre; the
speaker is the decisive check that this added structure is an improvement.

That physical gate now has one exact reproducible A/B medium rather than three
ad-hoc host loads.  [`OPL-IMP-M7-PHYSICAL-AB.json`](OPL-IMP-M7-PHYSICAL-AB.json)
pins the score and COM hashes for `IMPV1.COM`, `IMPREAR.COM`, and `IMPDET.COM`,
their common source VGM, the on-disk listening order, and a native 800 KiB
image at SHA-256 `00c7c66b...2c87870`. The builder round-trips every CP/M file
before converting the logical image to Juku cylinder order.  A separate
standalone `-P8=1` flag now enables the same physical Escape polling without
selecting the `-P2=1` JPS library ABI.  The builder asserts both emitted poll
sites and executes each exact COM both to normal completion (29.783, 29.909,
and 29.962 seconds) and with Escape injected after one second (returning at
1.012, 1.017, and 1.000 seconds).

The disk is retained at
`out/jukupoly-imp-m7-physical-ab/jukupoly-imp-m7-physical-ab.cpm`.  Its protocol
keeps the volume fixed, plays unchanged v1 first, then bounded merged-voice
re-articulation, then source-member detuning, and records lead onset/fade,
beating or roughness, percussion balance, Escape, and CP/M return.  This is
no longer preparation only, but the first physical run remains incomplete.
[`sessions/cs00000-jukupoly-m7-physical/README.md`](sessions/cs00000-jukupoly-m7-physical/README.md)
records two clean v1 runs and confirms the missing intro lead plus acceptable
early ticking/percussion.  The re-articulation COM then failed to return and
the physical screen showed garbage, despite that original exact hash still
returning cleanly in the instruction-level 8080 test.  The detuned candidate
was not run.  The original comparison disk also omitted standalone keyboard
polling while claiming Escape support; the rebuilt medium above corrects that
packaging error and its automated normal/abort paths pass.  Imp therefore
remains v1 and the physical gate stays open pending a cold-boot isolated
`IMPREAR` reproduction.  The same session also proved that
C10's late-ready recovery booted CP/M; the apparent boot failure was a missing
console PTY endpoint, for which `jukuhost` now performs a pre-bootstrap check
and emits an explicit path/error diagnostic.

Subsequent host-render listening rejected the unchanged-v1 control for its
missing intro and identified a slower-than-OPL fade in both M7 candidates.
This was not treated as a subjective tuning request.  The fitter had copied
source OPL `EGT` directly into the target sustain-state choice, even though
`EGT` describes an OPL operator and not the best reduction into Juku's two
existing envelope state machines.  The guarded
`--enhanced-target-envelope-shape` experiment now fits both target modes
against the same oracle trace and retains source `EGT` on an exact tie.  It
adds no opcode, player code, or per-sample work; choosing the already existing
automatic-release state can still change bounded 50 Hz frame work, so all
ordinary timing gates remain mandatory.

The policy also composes with M4 rather than creating a mutually exclusive
converter mode.  Joint envelope+tremolo fitting evaluates every permitted
target sustain state, compares improvement against the best no-tremolo target
shape, and keeps source `EGT` as the final exact-error tie preference.  An
exact synthetic two-slope-plus-tremolo regression and the unchanged frozen M4
real/full reports guard both the new combination and old default behavior.
The final cross-depth/cross-shape selection also retains the existing
significant-stage-direction priority; a fixed regression covers the case where
least squares alone would reverse the observed release direction.

[`OPL-IMP-TARGET-SHAPE-M7.json`](OPL-IMP-TARGET-SHAPE-M7.json) supplies an
independent check rather than validating the choice only with the attenuation
model which selected it.  It re-renders the hash-locked source through pinned
Nuked OPL with channels 0--3 isolated, derives the absolute 4-bit peak from
post-EG attenuation, derives relative shape from 20 ms PCM/RMS blocks, and
compares the exact old/new target traces.  Mean absolute error falls
1.920 to 1.409 levels for the merged first lobe, 0.779 to 0.593 for the
equal-step channel-0/2 composite, and 0.556 to 0.333 for detuned channel 1.
Squared error also falls and
maximum error does not increase in all three comparisons.  The two corrected
30-second score artifacts are committed separately from the delivered
library.

The broader opt-in experiment is pinned by
[`OPL-TARGET-SHAPE-PACK-SCAN-M7.json`](OPL-TARGET-SHAPE-PACK-SCAN-M7.json).
Across 441,072 fitted reference frames from all 44 Doom/Doom II openings,
sample-weighted absolute error falls 10.40% and baseline squared error falls
5.86%; 39 tracks improve absolute error, four tie, and one increases by only
26 accumulated 4-bit levels because squared error remains the fitter's primary
objective.  The worst measured sample-rate change is -0.370%, well inside the
explicit 10% reduction budget, and the candidate scan has one fewer timing-
gate failure than its source-semantic control.  This is broad offline evidence,
not permission to enable the policy by default before speaker qualification.

The corresponding physical medium is recorded by
[`OPL-IMP-TARGET-SHAPE-PHYSICAL-AB.json`](OPL-IMP-TARGET-SHAPE-PHYSICAL-AB.json).
It contains `REAROLD/REARNEW` and `DETOLD/DETNEW`, keeps one listening volume,
round-trips every file through CP/M, and checks both uninterrupted completion
and injected Escape for all four programs.  The native disk SHA-256 is
`f0923753...253affd`. This closes reproduction, independent-source, file,
cycle, and abort-path gates only.  The new policy remains opt-in and Imp stays
unchanged in the jukebox until the NEW fades are clearly preferable on the
physical speaker.

The first cold C10 run of the predecessor target-shape disk reproduced the
standalone enhanced-player failure before a useful OLD/NEW judgment could be
made.  It was not a target-envelope failure: the exact old COM also failed in
the complete C10/CP/M cosim.  Standalone startup had executed `LXI SP,0000h`
for tone channel 3 before `CALL envelope_dispatch_init`; the wrapped call
stack was writable in the flat-RAM audio harness but lies behind Juku's
write-protected high-ROM overlay.  Moving the dispatcher call ahead of the SP
loan leaves the hot loop and score unchanged.  A focused high-ROM regression
now rejects the old ordering, and the repaired COM returns through CP/M and
accepts a following B: `DIR` in full-system cosim.  The failed physical image
is superseded first by the repaired `aea4ec65...` disk and then by the
equal-step grouping `f0923753...` disk above, whose listening gate remains
open.

The later isolated-voice differential in
[`OPL-VOICE-DIFFERENTIAL.md`](OPL-VOICE-DIFFERENTIAL.md) replaces ambiguous
whole-song diagnosis with one exact logical-note experiment. It exposed a
separate M7 allocation defect: multiple OPL members may quantize to one target
phase step while carrying complementary envelopes. Discarding all but the
highest-total-energy member created real silent gaps. Equal-step members are
now combined and fitted on the host before at most three distinct phase groups
are emitted. This adds score metadata and packets only; it adds no opcode,
sample-loop instruction, or target-side OPL work. A two-pass host-only phase
calibration accounts for the isolated score's lighter frame overhead. The Imp
intro's normalized rendered contour improves from `2.99/54.22 dB` median/p90
error and `0.557` correlation to `0.97/6.17 dB` and `0.832`, with `0.969`
cents worst measured pitch error. These are offline gates; physical speaker
judgment remains required.

The short oracle-derived attack-sample branch now has a structural upper-bound
audit in [`OPL-M7-ATTACK-PCM.json`](OPL-M7-ATTACK-PCM.json).  It deliberately
does not synthesize or emit PCM yet.  The existing target has one PCM lane and
a new descriptor replaces a still-playing tail, so an attack must not overlap
an existing kick/snare/hat, another attack tail, or a second selected onset.
Moreover PCM has no pitch control: an honest pitched attack needs a distinct
sample for every source patch plus folded target note, from only 96 custom
sample IDs.  The projection accounts for raw u4 bytes, descriptors, row
pointers, row splits, and the 32,767-byte JPS limit while retaining all
protected tone onsets.

At the shortest useful bound of one 50 Hz frame (20 ms), only 16,515 of 36,326
selected onset frames across the two packs are schedulable without replacing
percussion, or 45.46%.  Seven tracks exceed the hard file limit and nine need
more than 96 patch/pitch samples.  Extending attacks to 40/60 ms reduces
coverage to 39.08/33.72% and makes 11/15 tracks exceed the hard limit.  Imp is
a particularly poor target: 594 drum triggers leave only 47 of 395 onset
frames (11.90%) available even for 20 ms, although its small projected file
would fit.  This cannot address its characteristic low lead as broadly as the
detuned-envelope candidate.

Therefore M7 adds no generic attack-PCM emission or target feature at this
checkpoint.  A later track-specific *selection* may still be justified for a
source with high collision-free coverage and enough IDs/memory, but it must
first fit an isolated oracle residual against the already-playing tone;
copying the whole OPL attack on top of that tone would double rather than
restore energy.  The present report is an explicit capacity/collision
fallback, not a claim that all attack timbre is impossible.

The cross-milestone completion audit is generated as
[`OPL-PLAN-STATUS.json`](OPL-PLAN-STATUS.json).  It verifies the frozen loop
across M3--M7 reports, every automated delivery gate, the `1700h` maximum
player end, 30,071-byte largest delivered JPS, exact `40/3/1` capability
distribution, all 44-track scans, generic-reducer title-literal guard, and the
recorded M3--M6 physical evidence.  Its automated status is `pass`; G3, G8,
and M7 point to the single remaining required action, the prepared Imp
target-shape physical A/B.  Older milestone reports retain their historically accurate
“pending” strings, while this audit records which later evidence closed them.

## Required reporting for every implementation change

Every merge which affects target playback must include:

- baseline and new mean/max cycles and effective sample rate;
- confirmation that the hot-loop guard passes;
- player end address and added state bytes;
- largest affected JPS size and full-track duration error;
- old/new/reference short renders;
- which OPL semantics are preserved, approximated, or intentionally omitted;
- confirmation that no song-specific conversion rule was added;
- physical result when the milestone requires it.

This plan is deliberately incremental.  Up to a 10% measured sample-rate
reduction is an explicitly accepted budget for the combined OPL feature set.
A milestone that exceeds that budget does not authorize taking more cycles,
RAM, frequency range, percussion concurrency, or other capability from
already-qualified playback.  It authorizes a cheaper representation, a
host-side approximation, or an honest unsupported-feature report.
