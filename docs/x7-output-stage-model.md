# X7 output-stage static model

Status date: **2026-07-23**.

Status: **TOPOLOGY + DATA-BACKED LS86 COMPARISON DRIVER GUARDED / EXACT D34 CURVE + HARDWARE CALIBRATION OPEN**.

This generated report is the second evidence-bounded part of CVBS-plan WP4.
It solves the traced X7 emitter-follower topology with the official TI
SN74LS86A PSpice model's supply-dependent output resistances instead of fixed
D34 pin voltages. TI describes that driver as data-sheet-generated typical
25 C behavior. It is comparison evidence, not proof of exact К555ЛП5 I/V
behavior, a physical D34 waveform, monitor timing, edge shape, or the installed
КТ315Б parameters.

## Commands

```sh
python3 scripts/model_x7_output_stage.py
python3 scripts/model_x7_output_stage.py --fixture-dir /tmp/juku-x7-static
```

The optional fixture is a little-endian float32 stepped-voltage diagnostic,
not a video waveform. Its sidecar records the current source commit, sample
rate, load, state schedule, model hash, and sample hash.

## Guarded topology and model checks

| Check | Result | Evidence |
| --- | --- | --- |
| D34_SYNC endpoint contract | PASS | D34.8, R62.1 |
| D34_SIG endpoint contract | PASS | D34.11, R63.1 |
| VT2_BASE endpoint contract | PASS | R62.2, R63.2, R64.1, VT2.3 |
| VIDEO_OUT endpoint contract | PASS | R65.1, VT2.1, X7.1 |
| R64 and R65 fitted returns are grounded | PASS | R64.2 + R65.2 on GND |
| VT2 collector is on +5 V | PASS | VT2.2 on P5V |
| VT2 device and E-C-B mapping are guarded | PASS | VT2 = КТ315; 1=E, 2=C, 3=B |
| Exact-revision D34 identity is К555ЛП5 | PASS | ДГШ5.109.009 ПЭЗ census D34 + board LP5_XOR type |
| Fitted resistor identities and model values agree | PASS | R62=2 kΩ, R63=1 kΩ, R64=5.1 kΩ, R65=430 Ω |
| C94 is absent from the nominal model | PASS | unresolved population/value/endpoints retained as a boundary |
| Preserved exact-device К555ЛП5 datasheet hash and limits match | PASS | К555ЛП5: VOH >=2.7 V, VOL <=0.5 V; fanout-derived 0.4 mA source/8 mA sink; no output I/V curve |
| Preserved SN74LS86A current-comparison datasheet hash matches | PASS | TI SDLS124 page 4; current threshold only, not К555ЛП5 equivalence |
| Official SN74LS86A comparison-driver model and coefficients match | PASS | TI SDLM061 rev 2.0; typical 25 C; supply-dependent ROH/ROL; comparison only |
| Preserved КТ315Б datasheet hash, package, and model limits match | PASS | owner marking Б/8901; old KT-13 E-C-B; hFE 50..350; VCE(sat) <=0.4 V |
| Nominal base drive is ordered and emitter output is nondecreasing | PASS | base: 00 < sync-only < signal-only < 11; X7 may remain off below VBE |
| A 75-ohm termination never raises the nominal emitter voltage | PASS | terminated output <= unterminated output for all four states |
| Declared DC corners remain outside transistor saturation | PASS | 1296 terminated + 432 unterminated parameter corners per logic state |
| Declared DC corners remain inside published КТ315Б absolute limits | PASS | Ic <=100 mA, P <=150 mW at 25 C, VCE <=20 V |

## D34 comparison-driver boundary

The preserved exact-device К555ЛП5 sheet guarantees VOH >=2.7 V,
VOL <=0.5 V, and fanout 10, but omits output-current test conditions and
nonlinear I/V curves. Its stated input currents under the standard fanout
meaning imply 0.4 mA high-state source and 8 mA low-state sink
full-fanout loads. The independent TI SN74LS86A sheet
corroborates those values but does not supply К555ЛП5 curves.

TI's official SDLM061 SN74LS86A PSpice package is data-sheet-generated
typical 25 C behavior. Its push-pull output is VCC through 5,000–4,878 Ω
when high and ground through 62.5–43.75 Ω when low across 4.5–5.5 V.
This model now participates in the coupled KCL solve, so D34 pin voltage
droops with load instead of remaining artificially fixed. It remains an
explicit comparison driver, not К555ЛП5 equivalence evidence.

| State | Pin | Mode | Relevant current (mA) | Fanout-derived limit (mA) | Result |
| --- | --- | --- | ---: | ---: | --- |
| sync=0,signal=0 | sync | sink | 0.000 | 8.000 | WITHIN |
| sync=0,signal=0 | signal | sink | 0.000 | 8.000 | WITHIN |
| sync=0,signal=1 | sync | sink | 0.460 | 8.000 | WITHIN |
| sync=0,signal=1 | signal | source | 0.683 | 0.400 | EXCEEDS |
| sync=1,signal=0 | sync | source | 0.640 | 0.400 | EXCEEDS |
| sync=1,signal=0 | signal | sink | 0.531 | 8.000 | WITHIN |
| sync=1,signal=1 | sync | source | 0.358 | 0.400 | WITHIN |
| sync=1,signal=1 | signal | source | 0.418 | 0.400 | EXCEEDS |

The supply-dependent TI SN74LS86A comparison driver self-consistently droops under the traced load, but still sources more current than the exact К555ЛП5 sheet's fanout-derived high-state envelope in at least one nominal state. TI labels the model typical 25 C behavior, not К555ЛП5 equivalence evidence; physical X7 voltages still require an exact-device curve or measurement.

## Nominal DC transfer

Positive D34 pin current means current sourced out of that output; negative
means that output is sinking current from the summing node. The reported D34
pin voltages are solved between the TI comparison resistance and R62/R63.

| Load | D34 sync | D34 signal | Region | Sync pin (V) | Signal pin (V) | Base (V) | X7 (V) | Ic (mA) | Sync pin (mA) | Signal pin (mA) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 75 Ω | 0 | 0 | off | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| 75 Ω | 0 | 1 | active | 0.0244 | 1.6271 | 0.9442 | 0.2442 | 3.786 | -0.460 | 0.683 |
| 75 Ω | 1 | 0 | off | 1.8388 | 0.0282 | 0.5587 | 0.0000 | 0.000 | 0.640 | -0.531 |
| 75 Ω | 1 | 1 | active | 3.2334 | 2.9359 | 2.5180 | 1.8180 | 28.186 | 0.358 | 0.418 |
| unterminated | 0 | 0 | off | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| unterminated | 0 | 1 | active | 0.0254 | 1.6578 | 0.9811 | 0.2811 | 0.647 | -0.478 | 0.677 |
| unterminated | 1 | 0 | off | 1.8388 | 0.0282 | 0.5587 | 0.0000 | 0.000 | 0.640 | -0.531 |
| unterminated | 1 | 1 | active | 3.5547 | 3.3114 | 2.9695 | 2.2695 | 5.226 | 0.293 | 0.342 |

## Declared corner sweep

The terminated sweep evaluates **1,296**
corners per logic state: all independent ±5% resistor corners crossed with
the +5 V supply, TI comparison-driver resistance interpolation, 75 Ω load,
beta, and VBE values.
The unterminated diagnostic evaluates **432**
corners per state with only fitted R65 loading the emitter.

The two final columns count corners that exceed the exact sheet's
fanout-derived loads. The comparison driver now predicts its own resistive
droop, but those warnings still mark operation outside the exact device's
stated same-family load envelope.

| Load | State | X7 range (V) | Base range (V) | Max Ic (mA) | Max /D34 sync/ (mA) | Max /D34 signal/ (mA) | Min saturation margin (V) | Sync warnings | Signal warnings |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 75 Ω | sync=0,signal=0 | 0.0000–0.0000 | 0.0000–0.0000 | 0.000 | 0.000 | 0.000 | 4.350 | 0 | 0 |
| 75 Ω | sync=0,signal=1 | 0.0320–0.5119 | 0.8031–1.0770 | 8.174 | 0.524 | 0.745 | 3.942 | 0 | 1296 |
| 75 Ω | sync=1,signal=0 | 0.0000–0.0675 | 0.5014–0.6198 | 1.078 | 0.688 | 0.578 | 4.340 | 1296 | 0 |
| 75 Ω | sync=1,signal=1 | 1.2357–2.5369 | 1.9718–3.1107 | 40.448 | 0.450 | 0.524 | 2.114 | 250 | 760 |
| unterminated | sync=0,signal=0 | 0.0000–0.0000 | 0.0000–0.0000 | 0.000 | 0.000 | 0.000 | 4.350 | 0 | 0 |
| unterminated | sync=0,signal=1 | 0.0411–0.5349 | 0.8757–1.0872 | 1.305 | 0.528 | 0.728 | 3.924 | 0 | 432 |
| unterminated | sync=1,signal=0 | 0.0000–0.0695 | 0.5014–0.6198 | 0.170 | 0.688 | 0.578 | 4.340 | 432 | 0 |
| unterminated | sync=1,signal=1 | 1.8224–2.7219 | 2.6467–3.2756 | 6.636 | 0.338 | 0.394 | 1.950 | 0 | 0 |

## Model boundary

The following are deliberately not inferred by this result:

- C94, whose population, value, and endpoints are unresolved
- frequency-dependent transistor behavior and cable/probe capacitance
- exact К555ЛП5 nonlinear output behavior, edge shape, and propagation delay
- physical D34 logic polarity and video timing
- installed-part calibration

The data-backed TI SN74LS86A comparison driver replaces the fixed TTL
pin-voltage approximation, but it is not an exact nonlinear К555ЛП5 output
model. Beta and VBE are sensitivity bounds; only beta endpoints are exact-grade
data, not installed-part measurements.
C94 remains absent. Consequently the
stepped fixture has ideal discontinuities and must not be used as evidence of
rise/fall time, bandwidth, actual composite polarity, or receiver lock.

## Next evidence

- Obtain a К555ЛП5 nonlinear output curve or measure D34 under the traced
  load, then promote or replace the explicitly comparative TI driver.
- Feed independently timed D34_SYNC/D34_SIG events into this transfer model only
  after the physical video-slot and D34 waveform boundaries close.
- Inspect C94 and capture terminated X7 plus VT2 base on hardware before adding
  any dynamic component or promoting model voltages to calibrated results.
