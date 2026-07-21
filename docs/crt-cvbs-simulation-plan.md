# Juku X7 composite-video and CRT simulation task plan

Status date: **2026-07-21**.

Status: **PLANNED / NO RAW-X7 RECEIVER CLAIM YET**.

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
- X7 is the VIDEO_OUT/GND connector.

Not yet proved:

- the exact shared-DRAM video-read slot schedule;
- a faithful physical D34 picture/sync waveform in the runnable HDL;
- X7 voltage levels and edge shape under a 75-ohm monitor load;
- the installed KT315 device parameters and tolerance spread;
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

- Record upstream and fork remotes and the fork point in the decoder README.
- Build the unmodified fork on the development host.
- Run `synth_ntsc` and upstream CTest before changing the pipeline.
- Add CI for the existing RF/IQ path and the future baseband path.
- Define a small deterministic fixture policy; do not commit multi-gigabyte
  captures.

Exit gate: the fork builds and its upstream tests pass from a clean checkout.

### WP1 — Generic baseband input

- Add an explicit baseband file/source mode, for example:

  ```text
  --input baseband-f32 --file x7.f32 --rate HZ --mode gray
  ```

- Bypass RF-only DC/NCO/channel-filter/AM stages in this mode.
- Retain optional polarity, gain, offset, and AGC controls.
- Make headless frame dumping work with baseband input.
- Reject missing sample-rate and malformed/truncated input clearly.
- Add a generated grayscale composite fixture independent of Juku.

Exit gate: a synthetic baseband fixture locks and produces a deterministic
frame without passing through RF modulation or HackRF code.

### WP2 — Parameterized synchronization receiver

- Replace hard-coded NTSC constants with a `VideoTimingProfile` or equivalent.
- Parameterize acquisition bounds for line period, sync width, frame length,
  active-line count, and active-window position.
- Retain measured line-PLL state and lost-lock/coast reporting.
- Support broad-pulse vertical sync without requiring NTSC equalizing pulses.
- Provide a monochrome-only decode path that does not run chroma filters.
- Report measured line rate, frame rate, sync width, blank level, and video
  range in machine-readable output.
- Add negative fixtures: reversed polarity, missing horizontal pulses,
  malformed vertical sync, clipped levels, and excessive period error.

Exit gate: both the original synthetic NTSC test and a non-NTSC monochrome
fixture pass, and failures identify loss of lock rather than silently rendering
a framebuffer.

### WP3 — Juku digital waveform source

- Add explicit HDL probes for the physical pixel and sync contributors instead
  of using the current abstract `vid_out` as X7.
- Drive D54/D55/D56/D34 through the physical structural path where evidence is
  complete.
- Export timestamped logic events or a uniformly sampled ideal-level waveform.
- Initially use a synthetic known-good Juku timing fixture to develop the
  receiver; keep it visibly distinct from the physical HDL result.
- Replace the simulation-only framebuffer read port only after the
  shared-DRAM video-slot schedule is evidence-complete.

Exit gate: the exported digital waveform contains independently measurable
horizontal sync, vertical sync, blanking, and picture intervals, and its active
pixels reconstruct the guarded framebuffer without metadata assistance.

### WP4 — X7 output-stage model

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

1. Clone/build the decoder fork and preserve the upstream `synth_ntsc` result.
2. Implement the generic float32 baseband input and headless output first.
3. Refactor synchronization constants into profiles while keeping NTSC green.
4. Generate a synthetic non-NTSC monochrome fixture and prove receiver lock.
5. In parallel with later decoder work, close the remaining Juku physical
   video-slot and D34 signal boundaries before calling any HDL waveform X7.
6. Add the terminated VT2 circuit model and connect its sample output to the
   decoder.
7. Calibrate against physical scope captures before promoting the result from
   a nominal model to verified monitor behavior.
