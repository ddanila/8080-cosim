# Video analog boundary

Status date: 2026-07-12.

Status: **ANALOG VIDEO/RF HANDOFF GUARDED / BENCH MEASUREMENT PENDING**

This generated report isolates the sheet-2 analog video, RF, and
analog-corner sound-mix handoff. It guards the traced board endpoints
that feed the composite-video connector and RF output while keeping
electrical levels, RF tuning, and the unresolved R66.1 source as
bring-up or source-read boundaries.

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

## Package / Connector Checks

| Check | Result | Evidence |
| --- | --- | --- |
| VT2 video emitter follower is modeled | PASS | VT2 provenance: sheet-2 analog corner |
| VT3 RF/video stage is modeled | PASS | VT3 provenance: sheet-2 analog corner |
| VT4 RF oscillator/output stage is modeled | PASS | VT4 provenance: sheet-2 analog corner |
| L1 adjustable tank coil retains its separate 1/5 tap | PASS | L1.1/L1.2 are the tank ends; L1.3 feeds R76 through RF_TAP |
| VIDEO_OUT connector maps to X7 | PASS | X7.1 signal / X7.2 return |
| HF_OUT connector maps to X6 | PASS | X6.1 signal / X6.2 return |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| Analog-corner SOUND injection remains source-boundary only | PASS | R66.1 source is still not netted; do not merge with beeper SOUND without source evidence |
| Composite/RF electrical levels remain bench-only | PASS | transistor bias, RF tank tuning, and output level/current are not digital-netlist facts |
| X6/X7 connector identity remains assembly-drawing bounded | PASS | connector labels are guarded but need bring-up/photo confirmation for the .158 board |

## Current Analog-Corner Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D34_SYNC` | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D34_SIG` | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `VT2_BASE` | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VIDEO_OUT` | `R65.1, VT2.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delta possible) |
| `SOUND_CLAMP` | `R66.2, R67.1, VD3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R66.1 <- the "SOUND" PIT line [source pin pending]; VD3 KC147 clamp |
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

## Interpretation

- The digital video-readout guards prove byte-to-pixel behavior; this report
  is only the analog board handoff from D34 through VT2/VT3/VT4 and X6/X7.
- `VIDEO_OUT` and `HF_OUT` are routed to the modeled connectors, but real
  composite/RF amplitude, polarity margins, and tank adjustment still need
  bench capture during bring-up.
- The analog-corner `SOUND_CLAMP` path is not the same as the already guarded
  beeper speaker driver. R66.1 remains unnetted until source evidence proves
  the analog sound-mix input.
