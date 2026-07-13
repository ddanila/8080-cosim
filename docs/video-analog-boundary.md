# Video analog boundary

Status date: 2026-07-12.

Status: **ANALOG VIDEO/RF HANDOFF GUARDED / BENCH MEASUREMENT PENDING**

This generated report isolates the sheet-2 analog video, RF, and
analog-corner sound-mix handoff. It guards the traced board endpoints
that feed the composite-video connector and RF output while keeping
electrical levels and RF tuning as bring-up boundaries. R66.1 is
source-proved on the sheet's B (+12 V) rail.

## Command

```sh
python3 scripts/report_video_analog_boundary.py
```

## Guarded Net Checks

| Check | Result | Evidence |
| --- | --- | --- |
| `D34_SYNC` carries the traced analog-corner endpoints | PASS | `D34.8, R62.1` |
| `D34_SIG` carries the traced analog-corner endpoints | PASS | `D34.11, R63.1, R69.1` |
| `VT2_BASE` carries the traced analog-corner endpoints | PASS | `R62.2, R63.2, R64.1, VT2.2` |
| `VIDEO_OUT` carries the traced analog-corner endpoints | PASS | `R65.1, VT2.1, X7.1` |
| `SOUND_CLAMP` carries the traced analog-corner endpoints | PASS | `R66.2, R67.1, VD3.2` |
| `SND_MIX` carries the traced analog-corner endpoints | PASS | `R67.2, R68.1` |
| `VT3_BASE` carries the traced analog-corner endpoints | PASS | `C13.1, R68.2, R69.2, R70.2, R71.1, VT3.2` |
| `RF_RAIL` carries the traced analog-corner endpoints | PASS | `C10.1, C11.1, C9.2, R72.2, R73.1, VT3.3` |
| `VT3_E` carries the traced analog-corner endpoints | PASS | `R74.1, VT3.1` |
| `VT4_B` carries the traced analog-corner endpoints | PASS | `C10.2, R73.2, VT4.2` |
| `RF_TANK` carries the traced analog-corner endpoints | PASS | `C11.2, C12.1, L1.1` |
| `VT4_C` carries the traced analog-corner endpoints | PASS | `C12.2, C15.1, L1.2, VT4.3` |
| `RF_TAP` carries the traced analog-corner endpoints | PASS | `L1.3, R76.1` |
| `HF_OUT` carries the traced analog-corner endpoints | PASS | `R76.2, R77.1, X6.1` |
| `VT4_E` carries the traced analog-corner endpoints | PASS | `C14.1, C15.2, R75.1, VT4.1` |
| `C94_1_BOUNDARY` carries the traced analog-corner endpoints | PASS | `C94.1` |
| `C94_2_BOUNDARY` carries the traced analog-corner endpoints | PASS | `C94.2` |

## Package / Connector Checks

| Check | Result | Evidence |
| --- | --- | --- |
| VT2 video emitter follower is modeled | PASS | VT2 provenance: sheet-2 analog corner |
| VT3 RF/video stage is modeled | PASS | VT3 provenance: sheet-2 analog corner |
| VT4 RF oscillator/output stage is modeled | PASS | VT4 provenance: sheet-2 analog corner |
| L1 adjustable tank coil retains its separate 1/5 tap | PASS | L1.1/L1.2 are the tank ends; L1.3 feeds R76 through RF_TAP |
| R66 clamp input is fed from the sheet-2 B (+12 V) rail | PASS | sheet-2 B-arrow enters R66.1; power legend defines B (+12) |
| R73 RF-bias trimmer retains its grounded third terminal | PASS | sheet-2: top end RF_RAIL, wiper VT4_B, bottom end GND |
| Target-revision C94 680 pF capacitor is physically modeled | PASS | .009 factory drawing identity plus registered populated 680п owner-photo body |
| VIDEO_OUT connector maps to X7 | PASS | X7.1 signal / X7.2 return |
| HF_OUT connector maps to X6 | PASS | X6.1 signal / X6.2 return |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| Composite/RF electrical levels remain bench-only | PASS | transistor bias, RF tank tuning, and output level/current are not digital-netlist facts |
| X6/X7 connector identity remains assembly-drawing bounded | PASS | connector labels are guarded but need bring-up/photo confirmation for the .158 board |
| C94 electrical destinations remain explicit continuity boundaries | PASS | physical presence/value/position are proved; neither lead destination is yet readable |

## Current Analog-Corner Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D34_SYNC` | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D34_SIG` | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `VT2_BASE` | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VIDEO_OUT` | `R65.1, VT2.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delta possible) |
| `SOUND_CLAMP` | `R66.2, R67.1, VD3.2` | scan sheet-2 analog corner: R66.2 joins VD3.2/R67.1; R66.1 is separately source-proved on power rail B(+12); VD3 is КС147Г clamp |
| `SND_MIX` | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT3_BASE` | `C13.1, R68.2, R69.2, R70.2, R71.1, VT3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `RF_RAIL` | `C10.1, C11.1, C9.2, R72.2, R73.1, VT3.3` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed |
| `VT3_E` | `R74.1, VT3.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT4_B` | `C10.2, R73.2, VT4.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R73 4.7k drawn adjustable |
| `RF_TANK` | `C11.2, C12.1, L1.1` | scan sheet-2 full-resolution analog corner: C11.2 feeds the parallel C12/L1 tank top |
| `VT4_C` | `C12.2, C15.1, L1.2, VT4.3` | scan sheet-2 full-resolution analog corner: C12/L1 tank return joins VT4 collector and C15 top |
| `RF_TAP` | `L1.3, R76.1` | scan sheet-2 full-resolution analog corner: L1 adjustable-coil 1/5 tap feeds series R76 then HF output |
| `HF_OUT` | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delta possible) |
| `VT4_E` | `C14.1, C15.2, R75.1, VT4.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `C94_1_BOUNDARY` | `C94.1` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 1 remains an explicit continuity boundary because its destination is not readable through the component/fanout cluster |
| `C94_2_BOUNDARY` | `C94.2` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 2 remains an explicit continuity boundary because its destination is not readable through the component/fanout cluster |

## Interpretation

- The digital video-readout guards prove byte-to-pixel behavior; this report
  is only the analog board handoff from D34 through VT2/VT3/VT4 and X6/X7.
- `VIDEO_OUT` and `HF_OUT` are routed to the modeled connectors, but real
  composite/RF amplitude, polarity margins, and tank adjustment still need
  bench capture during bring-up.
- The analog-corner `SOUND_CLAMP` path is not the same as the already guarded
  beeper speaker driver. Sheet 2 instead proves R66.1 is biased from B (+12 V).
- `.009` C94 is no longer omitted or conflated with L1: its 680 pF body and
  placement are source-proved, while both electrical endpoints remain boundaries.
