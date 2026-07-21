# D99 trigger and timing reconstruction constraints

Status: **D99 TRIGGER/TIMING LOGIC CONSTRAINED / FIVE PINS MEASUREMENT-GATED**

D99 is the target-board К155АГ3 / SN74123-compatible dual retriggerable
monostable. Exact-revision sheet evidence closes both RC networks and the
local trigger pins; this report converts those facts into digital and
timing constraints without assigning the five remote conductors.

## Command

```sh
python3 scripts/report_d99_reconstruction_constraints.py
python3 kicad/check_d99_source_paths.py
sync/ag3_check.sh
```

## Evidence checks

| Check | Result |
| --- | --- |
| TI SN74LS123 PDF and validated D94 image hashes match | PASS |
| D99 all-pin board mapping matches the measured/source model | PASS |
| Five remote D99 pins remain separate singleton boundaries | PASS |
| D94 D1, both RC networks, and section-1 Q NC preserve exact endpoints | PASS |
| C17/C18/R97/R103 fitted values remain source-closed | PASS |
| Local D99 pinout records the exact clear/trigger contract | PASS |
| AG3 HDL/test preserves triggers, overriding clear, and complements | PASS |
| Physical D94 D1 is asserted exactly when A3 xor A2 | PASS |
| RC pulse and retrigger-inhibit predictions are exact | PASS |

## Exact pin disposition

| Pin | Device/board role | Board net | State |
| ---: | --- | --- | --- |
| 1 | 1A_N / GND | `GND` | CLOSED |
| 2 | 1B / isolated test landing | `D99_B_TEST_LANDING` | CLOSED |
| 3 | 1CLR_N / GND | `GND` | CLOSED |
| 4 | 1Q_N / constant-high boundary | `D99_Q1N_BOUNDARY` | MEASURE |
| 5 | 2Q boundary | `D99_Q2_BOUNDARY` | MEASURE |
| 6 | 2Cext / C17− | `D99_C2_TIMING` | CLOSED |
| 7 | 2Rext/Cext / C17+ / R97 | `D99_RC2_TIMING` | CLOSED |
| 8 | GND | `GND` | CLOSED |
| 9 | 2A_N / D94 D1 | `D94_D1_D99_A2N` | CLOSED |
| 10 | 2B / sheet-1 boundary | `D99_B2_SHEET1_BOUNDARY` | MEASURE |
| 11 | 2CLR_N boundary | `D99_CLR2_BOUNDARY` | MEASURE |
| 12 | 2Q_N boundary | `D99_Q2N_BOUNDARY` | MEASURE |
| 13 | 1Q / constant-low NC | `D99_Q1_NC` | CLOSED |
| 14 | 1Cext / C18− | `D99_C1_TIMING` | CLOSED |
| 15 | 1Rext/Cext / C18+ / R103 | `D99_RC1_TIMING` | CLOSED |
| 16 | +5 V | `P5V` | CLOSED |

## Section 1 is functionally constant

D99.3 `/CLR1` is physically grounded. The TI overriding-clear row
therefore fixes Q1/pin13 low and `/Q1`/pin4 high regardless of A1, B1,
or the fitted R103/C18 network. Pin13 is owner/drawing-closed NC; pin4
still leaves toward an unknown destination, but it is a constant-high
driver rather than a pulse source.

| /CLR1 | A1_N | B1 | Q1 pin13 | /Q1 pin4 |
| ---: | --- | --- | ---: | ---: |
| 0 | don't care | don't care | 0 | 1 |

This rules out D99 section 1 as the active raw-read conditioner and
gives a direct powered-probe expectation for pin4. It does not identify
pin4's remote conductor.

## Section 2 access trigger

D99.9 `2A_N` is owner-closed to open-collector D94 D1 with R89=6.2 kΩ
to +5 V. Exhaustive inspection of all 32 physical `.092` rows gives
`D1_active = A3 xor A2`, independent of A4 and BA1:BA0.

| Qualified /WR A3 | IORD A2 | D94 D1 / D99 A2_N | Cycle meaning when selected |
| ---: | ---: | --- | --- |
| 0 | 0 | released high | neither valid direction |
| 0 | 1 | asserted low | write |
| 1 | 0 | asserted low | read |
| 1 | 1 | released high | neither valid direction |

With the still-unknown B2/pin10 and `/CLR2`/pin11 both high, entry into
either selected read or write state makes A2_N fall and triggers Q2 high
with Q2_N low. B2 rising while A2_N is already low, or `/CLR2` rising
while A2_N is low and B2 high, also triggers/retriggers exactly as the
datasheet specifies. B2 low or `/CLR2` low prevents the D94 edge from
starting a pulse. D94's shared enable must also be asserted; a disabled
PROM releases D1 through R89.

## RC timing predictions

Using the model/datasheet typical `tW ≈ 0.45RC` and the datasheet
retrigger exclusion `0.22*Cext(pF) ns`:

| Section | Fitted network | Nominal pulse | Early-retrigger inhibit | Functional state |
| --- | --- | ---: | ---: | --- |
| 1 | R103 47 kΩ / C18 47 µF | 0.99405 s | 10.34 ms | held clear; pulse suppressed |
| 2 | R97 47 kΩ / C17 120 µF | 2.538 s | 26.4 ms | conditional access pulse |

These are nominal behavioral predictions. Electrolytic tolerance, leakage,
device threshold, temperature, and the actual B2/clear waveforms require
powered measurement before hardware release.

## Minimal closure sequence

1. With D99 removed, identify the remote endpoints of pins 4, 5, 10,
   11, and 12. Keep the five singleton nets separate until then.
2. Powered but current-limited, confirm pin4 remains high while pin13
   remains low; any pulse on pin4 contradicts the grounded-clear model.
3. Capture D94.2/A2_N, B2, `/CLR2`, Q2, and Q2_N together during both
   selected FDC reads and writes. A falling A2_N can trigger only with
   B2 and `/CLR2` high.
4. Measure the section-2 pulse and retrigger interval. Treat 2.538 s and
   26.4 ms as nominal targets, not pass/fail production limits.

## Reconstruction boundary

Closed automatically: package truth table, section-1 constant outputs,
D94-D1 access equation, both fitted RC networks, nominal timing, and exact
probe conditions. Still physical: pin4 destination, B2/pin10 source,
`/CLR2`/pin11 source, Q2/pin5 destination, Q2_N/pin12 destination, and
the installed analog timing waveform.
