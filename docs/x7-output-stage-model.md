# X7 output-stage static model

Status date: **2026-07-22**.

Status: **TOPOLOGY + DEVICE LIMITS GUARDED / D34 DRIVE CURVE AND HARDWARE CALIBRATION OPEN**.

This generated report is the first evidence-bounded part of CVBS-plan WP4.
It proves only the DC transfer of the traced X7 emitter-follower topology; it
does not prove a physical D34 waveform, monitor timing, edge shape, or the
installed KT315Б parameters. The published КТ315Б grade limits are guarded,
but they do not measure the individual transistor.

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
| Preserved exact-device К555ЛП5 datasheet hash and limits match | PASS | К555ЛП5: 5 V +/-5%, VOH >=2.7 V, VOL <=0.5 V, fanout 10; no output I/V curve |
| Preserved SN74LS86A current-comparison datasheet hash matches | PASS | TI SDLS124 page 4; current threshold only, not К555ЛП5 equivalence |
| Preserved КТ315Б datasheet hash, package, and model limits match | PASS | owner marking Б/8901; old KT-13 E-C-B; hFE 50..350; VCE(sat) <=0.4 V |
| Nominal four-state transfer is ordered by the traced resistor weights | PASS | 00 < sync-only < signal-only < 11 |
| A 75-ohm termination never raises the nominal emitter voltage | PASS | terminated output <= unterminated output for all four states |
| Declared DC corners remain outside transistor saturation | PASS | 7776 terminated + 2592 unterminated parameter corners per logic state |
| Declared DC corners remain inside published КТ315Б absolute limits | PASS | Ic <=100 mA, P <=150 mW at 25 C, VCE <=20 V |

## D34 drive-current boundary

The preserved exact-device К555ЛП5 sheet guarantees VOH >=2.7 V,
VOL <=0.5 V, and fanout 10, but omits output-current test conditions and
nonlinear I/V curves. The independent TI SN74LS86A sheet supplies only a
comparison threshold: 0.4 mA high-state source and 8 mA low-state sink.

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

The fixed-pin-voltage approximation requests more high-state source current than the independent comparison device's characterized condition. The exact К555ЛП5 sheet confirms the voltage/fanout envelope but omits output-current conditions and curves; physical X7 voltages still require a nonlinear driver source or measurement.

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

The two final columns count corners that exceed the independent SN74LS86A
current condition. They are warnings, not invented К555ЛП5 current limits.

| Load | State | X7 range (V) | Base range (V) | Max Ic (mA) | Max /D34 sync/ (mA) | Max /D34 signal/ (mA) | Min saturation margin (V) | Sync warnings | Signal warnings |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 75 Ω | sync=0,signal=0 | 0.0000–0.0000 | 0.2184–0.4471 | 0.000 | 0.032 | 0.063 | 4.350 | 0 | 0 |
| 75 Ω | sync=0,signal=1 | 0.6354–1.6335 | 1.4382–2.1909 | 26.116 | 0.959 | 1.632 | 2.717 | 0 | 7776 |
| 75 Ω | sync=1,signal=0 | 0.0361–0.7897 | 0.8400–1.3474 | 12.626 | 1.232 | 0.953 | 3.560 | 7776 | 0 |
| 75 Ω | sync=1,signal=1 | 1.2655–2.4305 | 2.0671–2.9877 | 38.859 | 0.421 | 0.821 | 1.920 | 162 | 6480 |
| unterminated | sync=0,signal=0 | 0.0000–0.0000 | 0.2184–0.4471 | 0.000 | 0.032 | 0.063 | 4.350 | 0 | 0 |
| unterminated | sync=0,signal=1 | 0.7332–1.6688 | 1.5749–2.2199 | 4.072 | 0.972 | 1.433 | 2.681 | 0 | 2592 |
| unterminated | sync=1,signal=0 | 0.0415–0.8073 | 0.8834–1.3585 | 1.970 | 1.193 | 0.959 | 3.543 | 2592 | 0 |
| unterminated | sync=1,signal=1 | 1.4661–2.4815 | 2.3076–3.0326 | 6.055 | 0.255 | 0.495 | 1.868 | 0 | 1035 |

## Model boundary

The following are deliberately not inferred by this result:

- C94, whose population, value, and endpoints are unresolved
- frequency-dependent transistor behavior and cable/probe capacitance
- D34 edge shape, output impedance, and propagation delay
- physical D34 logic polarity and video timing
- installed-part calibration

The fixed TTL pin-voltage approximation exposes the D34 source/sink currents
but is not yet a nonlinear К555ЛП5 output model. Beta and VBE are sensitivity
bounds; only beta endpoints are exact-grade data, not installed-part measurements.
C94 remains absent. Consequently the
stepped fixture has ideal discontinuities and must not be used as evidence of
rise/fall time, bandwidth, actual composite polarity, or receiver lock.

## Next evidence

- Obtain a К555ЛП5 nonlinear output curve or measure D34 under the traced
  load, then replace the fixed pin-voltage approximation.
- Feed independently timed D34_SYNC/D34_SIG events into this transfer model only
  after the physical video-slot and D34 waveform boundaries close.
- Inspect C94 and capture terminated X7 plus VT2 base on hardware before adding
  any dynamic component or promoting model voltages to calibrated results.
