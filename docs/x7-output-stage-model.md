# X7 output-stage static model

Status date: **2026-07-22**.

Status: **TOPOLOGY GUARDED / D34 DRIVE MODEL AND HARDWARE CALIBRATION OPEN**.

This generated report is the first evidence-bounded part of CVBS-plan WP4.
It proves only the DC transfer of the traced X7 emitter-follower topology; it
does not prove a physical D34 waveform, monitor timing, edge shape, or the
installed KT315Б parameters.

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
| Preserved SN74LS86A comparison datasheet hash matches | PASS | TI SDLS124 page 4; comparison only, not К555ЛП5 equivalence |
| Nominal four-state transfer is ordered by the traced resistor weights | PASS | 00 < sync-only < signal-only < 11 |
| A 75-ohm termination never raises the nominal emitter voltage | PASS | terminated output <= unterminated output for all four states |
| Declared DC corners remain outside transistor saturation | PASS | 7776 terminated + 2592 unterminated parameter corners per logic state |

## D34 drive-current boundary

D34 is the exact-revision К555ЛП5. The preserved TI SN74LS86A
datasheet is only a closest-family comparison: it characterizes a high output
at 0.4 mA source current and a low output at up to 8 mA sink current. It does
not prove identical К555ЛП5 curves.

| State | Pin | Mode | Relevant current (mA) | Comparison condition (mA) | Result |
| --- | --- | --- | ---: | ---: | --- |
| sync=0,signal=0 | sync | sink | 0.000 | 8.000 | WITHIN |
| sync=0,signal=0 | signal | sink | 0.000 | 8.000 | WITHIN |
| sync=0,signal=1 | sync | sink | 0.856 | 8.000 | WITHIN |
| sync=0,signal=1 | signal | source | 1.437 | 0.400 | EXCEEDS |
| sync=1,signal=0 | sync | source | 1.144 | 0.400 | EXCEEDS |
| sync=1,signal=0 | signal | sink | 0.862 | 8.000 | WITHIN |
| sync=1,signal=1 | sync | source | 0.293 | 0.400 | WITHIN |
| sync=1,signal=1 | signal | source | 0.586 | 0.400 | EXCEEDS |

The fixed-pin-voltage approximation requests more high-state source current than the comparison device's characterized condition; physical X7 voltages require a nonlinear К555ЛП5 driver model or measurement.

## Nominal DC transfer

Positive D34 pin current means current sourced out of that output; negative
means that output is sinking current from the summing node.

| Load | D34 sync | D34 signal | Region | Base (V) | X7 (V) | Ic (mA) | Sync pin (mA) | Signal pin (mA) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 75 Ω | 0 | 0 | off | 0.2211 | 0.0000 | 0.000 | 0.014 | 0.029 |
| 75 Ω | 0 | 1 | active | 1.9629 | 1.2629 | 19.580 | -0.856 | 1.437 |
| 75 Ω | 1 | 0 | active | 1.1120 | 0.4120 | 6.388 | 1.144 | -0.862 |
| 75 Ω | 1 | 1 | active | 2.8137 | 2.1137 | 32.771 | 0.293 | 0.586 |
| unterminated | 0 | 0 | off | 0.2211 | 0.0000 | 0.000 | 0.014 | 0.029 |
| unterminated | 0 | 1 | active | 2.0599 | 1.3599 | 3.131 | -0.905 | 1.340 |
| unterminated | 1 | 0 | active | 1.1437 | 0.4437 | 1.022 | 1.128 | -0.894 |
| unterminated | 1 | 1 | active | 2.9760 | 2.2760 | 5.241 | 0.212 | 0.424 |

## Declared corner sweep

The terminated sweep evaluates **7,776**
corners per logic state: all independent ±5% resistor corners crossed with
the declared TTL pin levels, +5 V supply, 75 Ω load, beta, and VBE values.
The unterminated diagnostic evaluates **2,592**
corners per state with only fitted R65 loading the emitter.

The two final columns count corners that exceed the SN74LS86A
comparison current condition; they are warnings, not К555ЛП5 pass/fail limits.

| Load | State | X7 range (V) | Base range (V) | Max Ic (mA) | Max /D34 sync/ (mA) | Max /D34 signal/ (mA) | Min saturation margin (V) | Sync warnings | Signal warnings |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 75 Ω | sync=0,signal=0 | 0.0000–0.0000 | 0.2184–0.4471 | 0.000 | 0.032 | 0.063 | 4.550 | 0 | 0 |
| 75 Ω | sync=0,signal=1 | 0.6119–1.6175 | 1.4053–2.1778 | 25.819 | 0.952 | 1.681 | 2.932 | 0 | 7776 |
| 75 Ω | sync=1,signal=0 | 0.0348–0.7818 | 0.8295–1.3424 | 12.479 | 1.241 | 0.950 | 3.768 | 7776 | 0 |
| 75 Ω | sync=1,signal=1 | 1.2176–2.4074 | 2.0096–2.9674 | 38.428 | 0.461 | 0.900 | 2.143 | 810 | 6543 |
| unterminated | sync=0,signal=0 | 0.0000–0.0000 | 0.2184–0.4471 | 0.000 | 0.032 | 0.063 | 4.550 | 0 | 0 |
| unterminated | sync=0,signal=1 | 0.7283–1.6664 | 1.5680–2.2179 | 4.061 | 0.971 | 1.443 | 2.884 | 0 | 2592 |
| unterminated | sync=1,signal=0 | 0.0412–0.8061 | 0.8812–1.3577 | 1.964 | 1.195 | 0.959 | 3.744 | 2592 | 0 |
| unterminated | sync=1,signal=1 | 1.4560–2.4780 | 2.2954–3.0295 | 6.039 | 0.263 | 0.511 | 2.072 | 0 | 1089 |

## Model boundary

The following are deliberately not inferred by this result:

- C94, whose population, value, and endpoints are unresolved
- frequency-dependent transistor behavior and cable/probe capacitance
- D34 edge shape, output impedance, and propagation delay
- physical D34 logic polarity and video timing
- installed-part calibration

The fixed TTL pin-voltage approximation exposes the D34 source/sink currents
but is not yet a nonlinear К555ЛП5 output model. Beta and VBE are sensitivity
bounds, not installed-part measurements. C94 remains absent. Consequently the
stepped fixture has ideal discontinuities and must not be used as evidence of
rise/fall time, bandwidth, actual composite polarity, or receiver lock.

## Next evidence

- Link D34 output characteristics and KT315Б limits to primary component data,
  then replace or qualify the fixed pin-voltage approximation.
- Feed independently timed D34_SYNC/D34_SIG events into this transfer model only
  after the physical video-slot and D34 waveform boundaries close.
- Inspect C94 and capture terminated X7 plus VT2 base on hardware before adding
  any dynamic component or promoting model voltages to calibrated results.
