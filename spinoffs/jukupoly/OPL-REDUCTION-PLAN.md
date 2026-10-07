# OPL-aware reduction plan

Status: implemented reduction with qualified fallbacks; corrected M7 target-shape
candidates still require physical A/B qualification. [OPL-PLAN-STATUS.json](OPL-PLAN-STATUS.json)
owns the cross-report status and remaining action. This contract does not claim
that Juku emulates an OPL chip; target features must pass the gates below.

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

Implement independently useful stages that fit the measured hardware budget.
Each feature may become:

1. **Target implementation:** compact 8080 code passing the cycle, sample-rate,
   RAM, file-size and physical-listening gates.
2. **Host-side reduction:** accurate host analysis emitted as a cheaper
   approximation, such as fitted envelopes or sparse pitch changes.
3. **Perceptual omission:** explicitly report behavior lost to three pulse
   voices, 4-bit levels or the available sample rate.
4. **Unsupported:** reject the feature or retain the previous conversion when
   no correct, useful approximation fits.

Proceed from host register timing, key transitions, pitch and voice grouping
through envelopes/key-off tails, tremolo, then vibrato and held-note pitch
changes. Target effects share one 10% sample-rate budget. Optional timbral,
four-operator and rhythm reductions require evidence that they add value.

At each gate, keep the passing subset buildable, testable and usable. Record a
failed experiment's platform limit and continue with independent features.

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
- Baseline VGZ reductions use 143 sample-loop iterations per music frame and
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
  about 7.12 kHz. This approximately 2.5% sample-rate reduction is measured
  in the cycle model; physical MOD listening remains pending. OPL reductions
  must pass their own timing and listening gates within the 10% limit below.

## Feasibility guards

### G0: establish and lock the baseline

The reproducible C-cosim baseline is [OPL-BASELINE.json](OPL-BASELINE.json).
Keep the following measurements available when changing the format or player:

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

- the measured effective sample rate must remain at least 90% of the frozen
  G0 `doomgate` profile: the shared floor is 6,401.146221 Hz, recorded in
  [OPL-ENVELOPE-M3.json](OPL-ENVELOPE-M3.json) and consumed by the generic pack
  builder. The lower minimum across all G0 fixtures is not this delivery gate;
- all newly enabled OPL work is combined when applying this limit--envelope,
  tremolo, vibrato, pitch handling, Escape polling, and worst normal row work
  are not granted separate 10% budgets;
- the music-frame rate and full-song duration must remain within 1% of the
  source timing after selecting the sample count;
- the worst enhanced frame must be measured and must not produce a visible
  missed sample batch, timing runaway, or audible periodic click;
- phase-step tables must be regenerated from the measured enhanced sample
  rate, so the accepted sample-rate change cannot detune every note.

Choose sample iterations from complete-workload measurements to retain the
music clock. If combined envelope and LFO processing falls below the shared
90% sample-rate floor, it is not shipped in that form.

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

## Reduction architecture

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

`import_jukupoly_vgz.py` retains both operators' `20h`, `40h`, `60h`,
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

`tools/jukupoly_opl_oracle.c` uses the pinned Nuked OPL3 submodule to render
timed register streams and emit channel-state probes at 50 Hz. The probes
include frequency number/block, key state, operator attenuation and envelope
stage, connection, AM/VIB enables, and LFO state. They are register-derived
measurements, not waveform pitch detection or perceptual loudness estimates.

`firmware/opl_oracle.py` isolates selected keyed spans while preserving their
register context. The [voice differential workflow](OPL-VOICE-DIFFERENTIAL.md)
renders those streams and computes RMS contours from the reference and target
audio separately. Host reduction uses the oracle state to fit compact target
packets; the full probe stream is not stored in the JPS song.

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

| Layer | Target representation and contract |
| --- | --- |
| [Envelope](JPS2-ENVELOPE-DESIGN.md) | Host-fitted 4-bit peak/sustain levels and compact ADSR stages; key-off starts release and `EGT` controls keyed sustain |
| [Tremolo](JPS2-TREMOLO-DESIGN.md) | One shared fractional LFO with bounded per-tone attenuation; enable only direct AM that survives quantization |
| [Pitch/vibrato](JPS2-PITCH-DESIGN.md) | Host-precomputed deltas and one shared fractional LFO; temporary steps preserve the base pitch and prevent drift |

The linked contracts own packet layouts, state, constants and build flags.
Fit against the isolated oracle rather than translating raw Yamaha rate codes
into arbitrary target speeds. FM-modulator changes do not establish direct
amplitude or pitch modulation. All three layers share G2's measured cycle
budget; sparse host-baked changes or explicit omission remain fallbacks when
runtime effects cannot meet it.

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
templates.  The current production reducer rejects those modes; any future target reduction
requires independent feasibility and physical qualification.

## Qualification and remaining work

The generated [status report](OPL-PLAN-STATUS.json) checks the underlying evidence
and distinguishes automated PASS from physical qualification:

| Layer | Current boundary |
| --- | --- |
| Baseline, timed register model and logical voices (M0–M2) | Implemented and guarded |
| Compact envelope (M3) | Enhanced Imp failed physical listening; unchanged JPS1 fallback is delivered |
| Tremolo (M4) | Three capability-03 tracks delivered; Dark Halls/Suspense listening was acceptable but inconclusive |
| Vibrato (M5) | Complete capability-05 At Doom's Gate has physical listening evidence |
| Mixed library (M6) | 44 tracks: four enhanced and 40 explicit JPS1 fallbacks; whole-disk C-cosim plus scoped physical evidence |
| Optional reduction (M7) | Detuned Imp and corrected envelope shape pass offline; corrected target-shape candidates lack physical A/B qualification |

The required next action is the cold-boot CS00000 comparison described in
[OPL-IMP-TARGET-SHAPE-PHYSICAL-AB.json](OPL-IMP-TARGET-SHAPE-PHYSICAL-AB.json):
compare REAROLD/REARNEW and DETOLD/DETNEW at one volume, recording fade preference,
Escape behavior and CP/M return. Prepared payloads are not listening evidence.
The earlier failed/partial run remains in the
[physical record](sessions/cs00000-jukupoly-m7-physical/README.md).

Packet, state and rollback contracts live in
[JPS2 envelope](JPS2-ENVELOPE-DESIGN.md),
[tremolo](JPS2-TREMOLO-DESIGN.md) and [pitch](JPS2-PITCH-DESIGN.md).
Use the [voice differential workflow](OPL-VOICE-DIFFERENTIAL.md) for source versus
target diagnosis. Preserve exact artifact/cycle/listening evidence in reports;
completed experiment chronology belongs in Git.

The status writer checks committed report values, evidence hashes and selected
source/listening markers. It does not rebuild payloads, rerun cycle simulations
or perform listening tests. `--check` compares the generated JSON with the
selected report without writing it; the default command overwrites that report.

Regenerate and verify the status after updating its inputs:

```sh
python3 spinoffs/jukupoly/tools/report_opl_plan_status.py
python3 spinoffs/jukupoly/tools/report_opl_plan_status.py --check
```
