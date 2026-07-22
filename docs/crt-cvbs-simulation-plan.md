# Juku X7 composite-video and CRT simulation task plan

Status date: **2026-07-22**.

Status: **IN PROGRESS / PARAMETERIZED GENERIC RECEIVER + STATIC X7 TOPOLOGY MODEL / NO RAW-X7 RECEIVER CLAIM YET**.

This is a subordinate execution plan for the video/composite item in
`../PLAN.md`. The main plan remains authoritative for project priorities and
release gates. This document owns only the work needed to generate the Juku
X7 waveform, decode it as a monitor would, and render the resulting monochrome
CRT picture.

## Goal

Build a reproducible path from the reconstructed Juku video circuit to a
sample-domain monitor model:

```text
Juku timing + framebuffer readout
  -> D42/D43 serializer and D37/D34 video logic
  -> R62/R63/R64 + VT2 + R65 + 75-ohm load
  -> timestamped X7 baseband voltage samples
  -> sync/line/frame receiver
  -> monochrome CRT presentation
```

The result must answer two different questions without conflating them:

1. **Electrical/timing validity:** does the modeled X7 waveform have plausible
   levels, pulse widths, line/frame periods, loading, and polarity?
2. **Monitor behavior:** can a receiver recover stable horizontal and vertical
   synchronization and display the expected framebuffer content from those
   samples?

A visually attractive framebuffer filter is not sufficient evidence for
either question.

## Repositories and provenance

- Juku source and verification repository:
  `https://github.com/ddanila/8080-cosim`
- Decoder fork:
  `https://github.com/ddanila/famicom-rf-hackrf-decoder`
- Upstream decoder:
  `https://github.com/GOROman/famicom-rf-hackrf-decoder`
- Fork point recorded for this plan:
  `6cce72d4a0e35ed364d086470191d61e3f6cd116`
- Upstream license at the fork point: MIT.

The decoder fork and its upstream were byte-aligned at the recorded fork
point. Future reports must record both the fork commit and the `8080-cosim`
commit used to generate an input waveform.

The repositories have deliberately different authority:

- `8080-cosim` owns historical evidence, physical net interpretation, Juku
  timing, analog-component values, waveform fixtures, and acceptance results.
- `famicom-rf-hackrf-decoder` owns reusable sample ingestion, synchronization,
  receiver DSP, and display code.
- The decoder fork must not become an independent source of guessed Juku
  timing constants.

## What the selected upstream actually provides

The upstream decoder performs its DSP on the host CPU. HackRF One is only the
RF tuner and 8-bit I/Q sampler. The existing pipeline is:

```text
10 MS/s RF I/Q
  -> DC blocking and frequency shift
  -> RF filtering
  -> AM detection
  -> AGC / IRE normalization
  -> horizontal sync and line PLL
  -> vertical sync and frame assembly
  -> NTSC chroma or grayscale decode
  -> SDL2 display
```

The program also accepts recorded `.cs8` I/Q input and passes the detected
baseband envelope to `NtscDecoder::process(const float *, size_t)`, where AGC
and synchronization are applied. That makes it a
useful receiver foundation, but not a drop-in Juku decoder:

- its file input is RF I/Q rather than baseband X7 voltage;
- line rate, sync widths, active window, and 262-line frame behavior are
  Famicom/NTSC-specific;
- its color decoder is unnecessary for Juku monochrome video; and
- its current CRT toggle is presentation, not proof of the X7 circuit.

`libanalogtv` was considered and rejected as the primary receiver. Its public
low-level structure contains a fixed 263-by-912 IRE grid, while its documented
Apple II path fills that grid from emulated RAM. It is useful prior art for TV
artifacts, but it is not a raw arbitrary-timing voltage-stream decoder.

## Existing Juku evidence and open boundaries

Already guarded in `8080-cosim`:

- the runnable framebuffer is 40 bytes by 241 rows;
- the abstract serializer reproduces all 9,640 framebuffer bytes;
- physical D42/D43 serializers, D37 pixel inversion, D44-D47 video counters,
  D50/D51 muxes, D53 decode, and D54/D55/D56 timing endpoints exist in the
  structural model;
- D56 uses modeled typical one-shot widths of about 223 us and 5.04 us from
  the traced RC networks;
- exact-revision sheet evidence and owner continuity close the important
  D54/D55/D56 crossings into D34;
- the composite handoff topology and values are recorded as R62=2 kOhm,
  R63=1 kOhm, R64=5.1 kOhm, VT2=KT315, and R65=430 Ohm; and
- X7 is the VIDEO_OUT/GND connector; and
- `scripts/model_x7_output_stage.py` now guards the traced DC topology, solves
  all four D34 logic combinations with 75-ohm and unterminated loads, sweeps
  7,776 terminated corners per state, and emits an optional metadata-complete
  float32 stepped diagnostic. The model also hash-guards exact-device
  К555ЛП5 voltage/fanout data and the old-package КТ315Б E-C-B and electrical
  limits. This is a static transfer result, not video.

Not yet proved:

- the exact shared-DRAM video-read slot schedule;
- a faithful physical D34 picture/sync waveform in the runnable HDL;
- X7 voltage levels and edge shape under a 75-ohm monitor load;
- a nonlinear output model or measured DC curves for exact-revision D34
  К555ЛП5; its preserved sheet's fanout and input-current limits imply 0.4 mA
  source/8 mA sink full-fanout loads but give no I/V curves, while the
  provisional fixed-pin-voltage model exceeds that exact-device derived
  envelope in three nominal active combinations;
- the installed КТ315Б device's actual gain and active-region VBE;
- the function and endpoints of C94 beside VT2;
- monitor lock against the actual Juku line/frame waveform; and
- agreement with an oscilloscope capture from surviving hardware.

The current `juku_top.vid_out` is only an abstract serialized pixel stream. It
bypasses the physical sync summing and transistor output stage and must never
be labeled as a simulated X7 waveform.

## Architecture decisions

### Preserve the upstream mode

Keep the Famicom/HackRF pipeline operational and retain its synthetic NTSC
test. Add Juku support as a separate input/profile path. This makes upstream
rebases possible and detects accidental receiver regressions.

### Use raw samples, not a reconstructed framebuffer, as the contract

The integration boundary is a monotonically sampled baseband stream. The
decoder must recover sync and pixels from samples; it must not receive row,
column, sync, or framebuffer metadata as hidden truth.

Metadata may describe the capture, but not solve it. At minimum it should
record:

- sample format and endianness;
- sample rate in hertz;
- voltage scale and offset;
- source repository and commit;
- generating test or capture command;
- load impedance; and
- whether the waveform is synthetic, HDL-derived, circuit-simulated, or
  measured.

Use float32 volts for the first implementation. Add integer ADC formats only
when a real capture device requires them.

### Separate decoder configuration from discovered measurements

Introduce a timing-profile structure instead of scattering Juku constants
through NTSC code. A profile may provide broad acquisition bounds and an
expected polarity, but the receiver must measure actual line/frame periods and
report them. Fixed active-window hints are acceptable only after sync lock.

### Keep electrical and CRT models separable

The output-stage model produces voltage samples. The receiver consumes voltage
samples. The CRT renderer consumes recovered luminance and beam position. Each
stage needs independent fixtures so a pretty renderer cannot hide a broken
waveform or receiver.

## Work packages

### WP0 — Baseline and reproducibility

Progress: **complete**. The recorded fork point has a guarded clean-checkout baseline in
`docs/crt-decoder-baseline.md`. On the 2026-07-22 Linux host, the unmodified
fork configured and built `fam_dsp`, `famidec`, and `synth_ntsc`; CTest passed
1/1, and the direct synthetic test decoded 29 frames with all seven bars in
tolerance. Development packages were extracted below `/tmp`, not installed on
the host. Fork commits `175cb65`/`feec5d7` now record the upstream/fork point,
authority split, and deterministic-fixture policy and add Linux CI. CI run
`29885055666` builds the full RF/IQ application and tests, then passes CTest
and direct `synth_ntsc`.

- [x] Record upstream and fork remotes and the fork point in the decoder README.
- [x] Build the unmodified fork on the development host.
- [x] Run `synth_ntsc` and upstream CTest before changing the pipeline.
- [x] Add CI for the existing RF/IQ path and the future baseband path.
- [x] Define a small deterministic fixture policy; do not commit multi-gigabyte
  captures.

Exit gate: the fork builds and its upstream tests pass from a clean checkout.

### WP1 — Generic baseband input

Progress: **complete** in decoder fork commit
`d383beb3dd038154364fb76f993ad32d12fe2d44`. The implementation keeps the
`.cs8`/HackRF route intact and adds a separate headerless little-endian
IEEE-754 float32 source. It rejects empty, non-four-byte-aligned, and
non-finite input; requires an explicit positive sample rate; applies optional
polarity, gain, and offset before auto or fixed AGC; and bypasses every RF/IQ
DC/NCO/filter/AM/audio/spectrum/recording stage. Fixed AGC levels describe the
post-transform stream and require sync greater than blank.

The generated fixture is decoder-independent and temporary: 999,093 samples
cover six grayscale fields without storing a binary fixture in Git. The real
headless CLI decoded five frames, and its first retained PPM matched all five
bars exactly at 0/64/128/191/255. Source tests separately cover transforms,
looping, empty/truncated files, and NaN rejection. GitHub CI run
`29886015187` built the full RF/IQ application and all test targets, passed the
three-test CTest suite (upstream RF synthetic, baseband source, baseband E2E),
and passed direct `synth_ntsc` on the exact fork commit.

- [x] Add an explicit baseband file/source mode:

  ```text
  --input baseband-f32 --file x7.f32 --rate HZ --mode gray
  ```

- [x] Bypass RF-only DC/NCO/channel-filter/AM stages in this mode.
- [x] Retain optional polarity, gain, offset, and AGC controls.
- [x] Make headless frame dumping work with baseband input.
- [x] Reject missing sample-rate and malformed/truncated input clearly.
- [x] Add a generated grayscale composite fixture independent of Juku.

Exit gate: **passed at the generic NTSC-rate boundary**. A synthetic baseband
fixture locks and produces a deterministic frame without passing through RF
modulation or HackRF code. This does not claim non-NTSC/Juku synchronization,
physical X7 voltage, or agreement with a Juku framebuffer; those remain WP2,
WP3/WP4, and WP5 respectively.

### WP2 — Parameterized synchronization receiver

Progress: **complete at the generic synthetic boundary** in decoder fork
commit `10bfa4b9ae6c1ce071633459170b067fe3e2d91f`. A
`VideoTimingProfile` now owns nominal line rate, hsync acquisition/track bounds,
broad-pulse vsync criteria, frame length, active rows/window, and AGC porch.
Custom mode is deliberately accepted only for float32 baseband grayscale and
requires every field explicitly; there is no guessed Juku preset. The
monochrome path bypasses the NTSC chroma filters and scales an arbitrary
declared active-line count into the 480-row output.

The independent positive fixture differs materially from NTSC: 8 MS/s,
12.5 kHz lines, 200-line frames, four broad-pulse vsync lines, 180 active
lines, 6 us hsync, and an 80 us line period. Its five bars decode exactly.
Machine-readable statistics guard independent line/frame lock, measured
12.5 kHz/62.5 Hz rates, 6 us sync width, about 0 IRE blank, and a 0..100 IRE
video range. Five negative fixtures prove explicit failure for reversed
polarity, missing hsync, malformed vsync, clipped sync, and excessive period
error; malformed vsync retains horizontal lock but fails frame lock. GitHub CI
run `29886839537` builds the full RF/IQ app, passes all five CTests, and keeps
direct `synth_ntsc` green at the exact fork tip.

- [x] Replace hard-coded NTSC constants with a `VideoTimingProfile`.
- [x] Parameterize acquisition bounds for line period, sync width, frame length,
  active-line count, and active-window position.
- [x] Retain measured line-PLL state and lost-lock/coast reporting.
- [x] Support broad-pulse vertical sync without requiring NTSC equalizing pulses.
- [x] Provide a monochrome-only decode path that does not run chroma filters.
- [x] Report measured line rate, frame rate, sync width, blank level, and video
  range in machine-readable output.
- [x] Add negative fixtures: reversed polarity, missing horizontal pulses,
  malformed vertical sync, clipped levels, and excessive period error.

Exit gate: **passed for generic synthetic input**. Both the original synthetic
NTSC test and a non-NTSC monochrome fixture pass; failures distinguish
horizontal from frame-lock loss instead of silently claiming a successful
framebuffer. Actual Juku timing/profile values and X7 lock remain WP3-WP5 work.

### WP3 — Juku digital waveform source

Progress: the first bounded physical-probe checkpoint is implemented. Simulation-
only top-level probes expose the source-proved D42/D43/D37 pixel contributor and
D54/D55/D56/D34_SYNC chain without changing the Yosys/LVS interface. A guarded
controlled-stimulus exporter verifies the modeled 223 us and 5.04 us D56 pulses,
the traced D34 sync XOR truth, and exact board endpoints. Every exported event
also carries `slot_schedule_known=0`; D34_SIG is deliberately absent. This proves
component-chain observability only, not a Juku raster, framebuffer reconstruction,
composite voltage, or X7 samples. See `video-physical-probes.md`.

The second checkpoint decodes and executes the exact `ekta37` PIT programming
sequence through `juku_top`. Correct 8253 BCD, mode-1, and mode-2 behavior now
drives the autonomous physical D54/D55/D56/D34_SYNC chain. The guard measures
64 us lines (15.625 kHz), 313-line/20.032 ms frames (49.920128 Hz), 8 us/25-line
front porches, 24 us/72-line blank intervals, and the D56 pulses. The resulting
320x241 active geometry independently matches the vendored MAME reference.
This closes raster timing, but not physical framebuffer slots or D34_SIG. See
`video-pit-timing.md`.

The decoder fork now consumes that bounded timing evidence in commit
`b1d62c085e416c80cff35d8a77a8fbc397eead51`, explicitly pinned to source
commit `eb4d6ab6777db3f97306c9111e9c723c97dcf750`. Its ideal five-bar waveform
uses the exact 64 us/313-line raster and guarded 5.04 us/223 us D56 pulse
widths. Linux CI run `29888769589` passes the full RF/IQ build, all six CTests,
and the unchanged direct NTSC regression. This is a receiver-development
fixture, not a built-in Juku preset or a claim about shared-DRAM pixels,
D34_SIG, analog X7 voltage, or a physical capture.

- [x] Add explicit HDL probes for the physical pixel and sync contributors instead
  of using the current abstract `vid_out` as X7.
- [x] Drive D54/D55/D56/D34_SYNC through the physical structural path where
  evidence is complete. D34_SIG remains separately open.
- [x] Export timestamped controlled-stimulus logic events for the bounded physical
  contributors, with unresolved fields machine-marked. A complete Juku waveform
  remains open.
- [x] Initially use a synthetic known-good Juku timing fixture to develop the
  receiver; keep it visibly distinct from the physical HDL result.
- [ ] Replace the simulation-only framebuffer read port only after the
  shared-DRAM video-slot schedule is evidence-complete.

Exit gate: the exported digital waveform contains independently measurable
horizontal sync, vertical sync, blanking, and picture intervals, and its active
pixels reconstruct the guarded framebuffer without metadata assistance.

### WP4 — X7 output-stage model

Progress: the traced resistor rails, VT2 E-C-B mapping, +5 V collector, grounded
emitter load, and X7 endpoint are machine-guarded by the static model. The
piecewise-linear emitter follower, exact КТ315Б beta endpoints and absolute
limits, declared VBE sensitivity bounds, independent resistor corners,
supply/load sweep, compact JSON summary, and on-demand float32 step fixture are
implemented. The exact-device К555ЛП5 sheet guards its voltage/fanout envelope;
fanout and input-current limits imply 0.4 mA source/8 mA sink full-fanout loads,
independently corroborated by the SN74LS86A sheet, but neither source supplies
a nonlinear К555ЛП5 I/V curve. C94 stays absent. The result deliberately does
**not** pass the WP4 exit gate: the fixed-voltage source approximation requests
more high-state current than that exact-device derived envelope. A nonlinear
D34 source or hardware measurement remains necessary.

- Model the two D34 logic sources and their real output characteristics.
- Model R62/R63/R64, the KT315 emitter follower, R65, +5 V, and X7.
- Include an explicit 75-ohm monitor termination and an unterminated diagnostic
  run.
- Use a circuit solver or a documented numerical transistor approximation;
  preserve the model source and parameters.
- Sweep resistor tolerances, transistor beta, TTL high/low levels, supply
  tolerance, and load impedance.
- Keep C94 absent from the nominal netlist until its population, value, and
  endpoints are established; document sensitivity cases separately rather
  than guessing its connection.
- Export voltage-versus-time samples and a compact waveform summary.

Exit gate: X7 levels, source current, transistor operating region, and loaded
amplitude remain plausible across the declared tolerance sweep. This is still
a model result until checked against hardware.

### WP5 — End-to-end Juku receiver and CRT display

- Feed only WP4 X7 samples into the fork's baseband input.
- Add a named `juku-e5104` timing profile with provenance for every initial
  bound.
- Recover a stable monochrome frame and compare its active pixels with the
  independent framebuffer oracle.
- Render a neutral diagnostic view first: no curvature, noise, bloom, or
  phosphor persistence.
- Add optional CRT presentation only after the diagnostic view passes.
- Keep receiver lock metrics and the raw waveform accessible beside rendered
  images.

Exit gate: a clean end-to-end run locks from X7 samples, emits measured timing
and level data, and produces the expected active image.

### WP6 — Physical calibration

- Capture D34_SYNC, D34_SIG, VT2 base, and terminated X7 on a surviving board
  or staged replica using a documented probe/load setup.
- Record oscilloscope bandwidth, probe attenuation, sample rate, grounding,
  termination, firmware/screen state, and board identity.
- Compare measured and modeled polarity, pulse width, line/frame period,
  blank/video/sync levels, rise/fall time, and loading.
- Tune only parameters justified by component data or measurement; do not tune
  digital topology to make a screenshot look attractive.
- Preserve a short redistributable capture fixture or, if owner restrictions
  prevent that, preserve hashes and derived measurements.

Exit gate: the same receiver locks to both modeled and measured X7 captures,
with discrepancies recorded and bounded.

## Verification matrix

| Layer | Primary check | Independent oracle |
| --- | --- | --- |
| Upstream preservation | `synth_ntsc` and CTest | upstream fork-point result |
| Baseband ingestion | deterministic generated waveform | generator parameters |
| Sync receiver | measured lock/rate/pulse report | fixture timing, not framebuffer metadata |
| Digital Juku video | recovered active bits | guarded 9,640-byte framebuffer |
| Analog output | X7 voltage/current/tolerance report | circuit equations and component data |
| End-to-end display | decoded active-image hash | independent framebuffer hash |
| Physical calibration | measured-vs-modeled waveform report | oscilloscope capture |

Every generated evidence report must state which layer it proves. A passing
active-image comparison does not prove voltage levels; a plausible voltage
plot does not prove monitor synchronization.

## Proposed artifacts

In `famicom-rf-hackrf-decoder`:

- generic baseband sample source;
- parameterized timing profile and monochrome receiver;
- headless timing/lock JSON output;
- small generated baseband fixtures and tests; and
- `juku-e5104` profile only after its constants are evidence-linked.

In `8080-cosim`:

- HDL/event exporter for physical video contributors;
- X7 output-stage circuit model and parameter file;
- waveform-to-decoder integration script pinned to a fork commit;
- short deterministic input fixtures or generation recipes; and
- generated timing, voltage, lock, and image-comparison reports.

Do not vendor the whole decoder fork into this repository during initial
development. Pin its URL and commit in the integration script/report. Revisit a
submodule or vendored snapshot only if reproducible CI cannot otherwise be
maintained.

## Acceptance criteria

The task is complete only when all of the following hold:

- upstream Famicom RF/IQ regression remains green;
- raw float32 baseband input works without HackRF hardware;
- timing is profile-driven and measured rather than globally hard-coded to
  NTSC;
- the receiver locks to a Juku X7 waveform without framebuffer metadata;
- the decoded active pixels match the independent Juku framebuffer oracle;
- the X7 model includes the 75-ohm load and reports actual voltages;
- assumptions and unresolved C94/shared-DRAM boundaries remain explicit;
- a physical capture either corroborates the model or leaves a quantified
  discrepancy report; and
- the documentation never describes the abstract current `vid_out` bitstream
  as composite voltage.

## Immediate next actions

1. Keep the now-guarded fork baseline and RF/IQ CI green through receiver changes.
2. Keep the completed generic float32 baseband/headless E2E path green.
3. Keep explicit timing profiles, measured telemetry, and NTSC compatibility green.
4. Keep the completed non-NTSC positive/negative lock suite green.
5. In parallel with later decoder work, close the remaining Juku physical
   video-slot and D34 signal boundaries before calling any HDL waveform X7.
6. Replace the provisional fixed-pin-voltage D34 sources with a data- or
   measurement-backed К555ЛП5 driver, then connect the existing terminated VT2
   transfer model's samples to the decoder.
7. Calibrate against physical scope captures before promoting the result from
   a nominal model to verified monitor behavior.
