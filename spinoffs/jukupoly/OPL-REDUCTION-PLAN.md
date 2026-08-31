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
The datasheet gives approximately 3.7 Hz for tremolo and 6.4 Hz for vibrato.
`EGT` selects sustained versus percussive envelope behavior, while `KSR`
changes envelope rate with pitch.  `TL` is logarithmic attenuation, not linear
volume.

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

The 6.4 Hz source LFO has about 7.8 target frames per cycle.  This is coarse
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

### M4: tremolo

Add the shared tremolo phase and per-voice effective depth.

Exit gate: synthetic rate/depth test, cycle gate, long-track size gate, and no
false large modulation when only an inaudible modulator has AM enabled.

If G2 fails, omit sub-quantization tremolo and use compact host-baked changes
only where audible and affordable.

### M5: vibrato and held-note pitch writes

Add the shared vibrato phase, temporary phase-step modulation, and generic
mid-note pitch handling.

Exit gate: no mean pitch drift, correct approximate LFO rate, no low-note
underflow, no high-note 15-bit overflow, and all cycle/size gates pass.

If G2 fails, reduce table/update complexity or emit sparse precomputed pitch
changes.  A measured sample-count reduction is permitted only while the
combined enhanced player remains at or above 90% of the baseline rate.

### M6: pack regression and physical qualification

Build the complete DOOM library and generate old Juku, new Juku, and accurate
OPL reference excerpts for at least The Imp's Song, Dark Halls, Suspense, and
one rhythm-heavy track.  Report note-onset retention, pitch contour, envelope
error after quantization, file sizes, cycles, and duration.

Exit gate: complete C-cosim runs, no new special cases, and CS00000 A/B
confirmation.  Keep old renders and disk image available for comparison until
qualification is recorded.

### M7: optional timbral and unsupported-mode reductions

Only after M6, investigate detuned spare-voice layers, short oracle-derived
attack samples, four-operator collapse, and hardware-rhythm mapping.  Each is
a separate experiment with the same gates.  Failure is an acceptable outcome;
the documented supported subset remains honest.

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
