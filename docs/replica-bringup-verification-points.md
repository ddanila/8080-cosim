# Replica bring-up verification points

Status: **ENDPOINT COVERAGE FAILED / RISKS UNRESOLVED**

This report is generated from `kicad/juku.board.json`. It turns the
remaining source-risk annotations into an explicit checklist for vendor
preview, owner continuity sessions, and staged bring-up. It does not mark
these points as independently verified; it makes the residual risks
visible and actionable before manufacturing and first power-on.
Risk rows come from explicit source-risk flags and keyword matching in
source notes; this is not an exhaustive physical failure inventory.
Refresh with `python3 kicad/report_replica_bringup_verification.py`.
Successful generation does not require endpoint coverage or risk closure.

## Summary

- Source board JSON: `kicad/juku.board.json`
- Source board JSON SHA-256: `98864ba47523a05d05afea6a7ed11591e68a2c3de7a46e39cf00e60b880fb13c`
- Final PCB source: `kicad/juku.kicad_pcb`
- Final PCB source SHA-256: `c1fbfcdeae9a859f76d9c46f79c570f83e7d1a98a5a136ef60e818d801482b97`
- Routed PCB source: `kicad/juku_routed.kicad_pcb`
- Routed PCB source SHA-256: `f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a`
- Verification-point nets: `55`
- Verification-point endpoints checked in PCB: `271`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `2320`
- All board endpoints checked in routed PCB: `2320`
- Intentional non-PCB or placement-pending endpoints excluded: `155`
- Full PCB endpoint coverage: `FAIL`

| Category | Nets |
| --- | ---: |
| FDC | 3 |
| logic | 29 |
| memory/decode | 1 |
| power | 13 |
| timing/I/O | 2 |
| video/analog | 7 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. Matching rows show
that the source PCB preserves the same modeled pad-net assignments as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 271/271 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 271/271 net names matched |

## Full Board Endpoint Coverage

Every PCB-scoped `kicad/juku.board.json` endpoint is also checked against
the generated source PCB and the routed fabrication PCB. Bracket-mounted
`S1`, `S4`, `X3`, `X4`, `X6`, `X8`, and `X9` are excluded, as are all
components marked `pcb_dnp` or `pcb_placement_pending` in the board JSON.
Assembly-DNP C63 remains in scope
because its provisional footprint is retained in the modeled PCB grid. Registered
photo features are DRAM contacts, not proof of independent capacitor holes;
C63 pad identity remains held and is distinct from the absent `.009` C83 callout
between D41/D40. See [capacitor fidelity](decap-value-fidelity.md). Pending
placements require evidence of their target location and population;
fit-to-space coordinates are not fabrication evidence. This is a
fabrication-source coverage gate, not a historical-source proof.

| PCB | Present | Matching net names | Result |
| --- | ---: | ---: | --- |
| `kicad/juku.kicad_pcb` | 2320/2320 | 2320/2320 | PASS |
| `kicad/juku_routed.kicad_pcb` | 2316/2320 | 2313/2320 | FAIL |

Missing endpoints in `kicad/juku_routed.kicad_pcb`:
- `INT6_RAW: R10.1`
- `INT7_RAW: R9.1`
- `P5V: R9.2`
- `P5V: R10.2`

Mismatched endpoints in `kicad/juku_routed.kicad_pcb`:
- C21.2: `GND` != `C21_R20_SERIES`
- R20.1: `RESIN` != `C21_R20_SERIES`
- R20.2: `P5V` != `R20_RETURN_SOURCE_HOLD`

## Checklist

| Net | Category | Endpoints | Source risk | Bring-up action |
| --- | --- | --- | --- | --- |
| `C10_1_BOUNDARY` | power | `C10.1` | .009 C10 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C10_2_BOUNDARY` | power | `C10.2` | .009 C10 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-base assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C11_1_BOUNDARY` | power | `C11.1` | .009 C11 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C11_2_BOUNDARY` | power | `C11.2` | .009 C11 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF tank assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C12_1_BOUNDARY` | power | `C12.1` | .009 C12 bypass and later July owner photo prove a +5 V/GND lap-lead pair at the factory site (D100.20/D94.8). This provisional replica through-hole pad1 has no proved correspon... | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C12_2_BOUNDARY` | power | `C12.2` | .009 C12 bypass and later July owner photo prove a +5 V/GND lap-lead pair at the factory site (D100.20/D94.8). This provisional replica through-hole pad2 has no proved correspon... | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C15_1_BOUNDARY` | power | `C15.1` | .009 C15 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 VT4-collector assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C15_2_BOUNDARY` | power | `C15.2` | .009 C15 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-emitter assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C94_1_BOUNDARY` | power | `C94.1` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 holes and pin1 rail rem... | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C94_2_BOUNDARY` | power | `C94.2` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 holes and pin2 rail rem... | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C9_1_BOUNDARY` | power | `C9.1` | .009 C9 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF ground assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `C9_2_BOUNDARY` | power | `C9.2` | .009 C9 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded | With power off, identify the physical capacitor leads and check each to known +5 V/GND; keep provisional pad assignments open until measured. |
| `CPU_WAIT_STATUS` | logic | `D1.24` | exact .009 full-sheet photo 101754468 traces D1.24 WAIT through lower filled junction and fold to D105.1; older .006 scan corroborates. Owner continuity 2026-07-19 independently... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D100_CONTROL_SHEET1_BOUNDARY` | logic | `D100.11` | Exact .009 Э3 sheet-3 detail PXL_20260718_101641055.jpg: D100 T/pin11 runs left to its own quoted sheet-1 continuation; it crosses nearby descending conductors without marked ju... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D02_R92_R99` | logic | `D101.3, D101.4, D101.5, D101.6, R92.1, R99.2, ... (+1)` | July-2026 calibrated component photo PXL_20260710_200418174.jpg shows uninterrupted target-board copper joining D101 К555КП12 pin4 D02 to R99.2 and R92.1. Exact .009 Э3 sheet-3... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D14_I2_BOUNDARY` | logic | `D14.2` | factory IC census and owner package identify D14 as К170АП2; pin2 I2 is a package-model role, while exact .009 E3 sheet-1 serial detail has no traceable D14.2 wire. Its remote s... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D14_O7_BOUNDARY` | logic | `D14.7` | factory IC census and owner package identify D14 as К170АП2; pin7 O7 is a package-model role, while exact .009 E3 sheet-1 serial detail has no traceable D14.7 wire. Its remote d... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PB5_E8_2_BOUNDARY` | logic | `D26.23` | Exact .009 sheet-1 detail PXL_20260718_101824181.MP.jpg sends D26 PB5/pin23 to E8.2, distinct from PB4/pin22 at E8.3 and CONTRDAT at E8.4. The .009 assembly and owner front phot... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC0_D3_I5` | logic | `D26.14, D3.5, R15.1` | direct .009 owner continuity 2026-07-14: D26 PC0/pin14 reaches D3 inverter input pin5 and owner reports a resistor path to +5 V; exact .009 sheet-1 photo PXL_20260718_101809608.... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC1_D3_I3` | logic | `D26.15, D3.3, R16.1` | direct .009 owner continuity 2026-07-14: D26 PC1/pin15 reaches D3 inverter input pin3 and owner reports a resistor path to +5 V; exact .009 sheet-1 photo PXL_20260718_101809608.... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D58_STB_TAG5` | logic | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D59_O10_TAG10` | timing/I/O | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled... | With power off, trace the remote endpoint of D59.10; keep it separate from SOUND and assembly wire W10. |
| `D94_D0_BOUNDARY` | logic | `D94.1, R8.1` | exact .009 E3 sheet 1 PXL_20260718_101817644.jpg draws R8=2k from +5 V to -WREQ; sheet 3 PXL_20260718_101633062.jpg traces D94.1 through the top bundle to WREQ (1), establishing... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_B2_SHEET1_BOUNDARY` | logic | `D99.10, D96.13` | exact .009 Э3 sheet-3 photo PXL_20260718_101641055.jpg joins D99 B2/pin10 to D96 section-2 active-low clear/pin13 at a marked junction; their shared conductor continues to sheet... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2N_BOUNDARY` | logic | `D99.12, D100.9` | Exact .009 Э3 sheet-3 detail PXL_20260718_101641055.jpg: D99 section-2 Q_N/pin12 descends and turns left to D100 OE_N/pin9. This line crosses D100 T/pin11 without a junction dot... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `FDC_HLD_TO_D100` | FDC | `D93.28, D100.3, D99.2` | recovered .009 Э3 sheet 3 photo PXL_20260718_101641055.jpg: D93 HLD/pin28 drives D100 A6/pin3 and E12 post 3; drawn E12 2-3 bridge connects D99 B1/pin2. Original-board E12 popul... | With power off, continuity-check the listed endpoints and any intervening jumper before drive bring-up. |
| `FDC_IMDRG` | FDC | `D26.38, D101.1` | Exact .009 Э3 sheet-1 native PXL_20260718_101824181.MP.jpg labels D26 PA6/pin38 IMDRG with sheet-3 continuation (3); sheet-3 PXL_20260718_101648508.jpg labels the arriving condu... | With power off, continuity-check the listed endpoints and any intervening jumper before drive bring-up. |
| `FDC_MOTOR_EN` | FDC | `D26.16, D99.11` | Exact .009 Э3 sheet 1 MOTOR EN continuation from D26 PC2/pin16 enters D99 CLR2_N/pin11 on sheet 3; D100 A7/pin7 is driven separately by D99 Q2/pin5. Original-board D26.16-D99.11... | With power off, continuity-check the listed endpoints and any intervening jumper before drive bring-up. |
| `INHIB_STATUS_BOUNDARY` | logic | `D7.5, D29.3` | Exact .009 sheet-1 crop PXL_20260718_101813438.jpg (850,2900)-(1850,3650): D7 NAND input pin5 joins D29 physical input pin3 at a filled T junction. The shared westbound conducto... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `INT4_RAW` | logic | `X1.114C, D12.6, D12.7` | Exact .009 sheet-1 PXL_20260718_101817644.jpg: -INT4 at X1.114C branches to both D12 LA18 gate inputs pins6 and7; D12.5 open-collector output reaches X2.214/IRQ0 through separat... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `KBD_CONTRDAT` | logic | `D26.22, X9.9, A50.1` | Exact .009 sheet-1 detail PXL_20260718_101824181.MP.jpg sends D26.22/PB4 to E8.3 and E8.4 to CONTRDAT continuation 909; .009 assembly and owner front photo show E8.3-4 jumper fi... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `P5V` | power | `R78.2, D10.16, D1.20, D4.11, D107.11, D44.4, ... (+223)` | scan; sheet-1 arrow-A rail ties address-buffer direction pins D4.11/D107.11 and PIC master strap D10.16 high; native sheet-2 power corner continues +5 V rail A to rail F and C34... | With power off, verify the source-risk supply branches against a known +5 V landing. |
| `PHI1_D35` | logic | `D35.10, W7.2, R37.2` | factory wire А:7 D35 clock-source-side copper island D35.10 reaches the candidate A7B plated through-joint under mastic; the W7 insulated-wire termination remains pending confir... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PHI2_D35` | logic | `D35.12, W14.2, R36.2` | factory wire А:14 D35 clock-source-side copper island D35.12 reaches the candidate A14B plated through-joint under mastic; the W14 insulated-wire termination remains pending con... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R20_RETURN_SOURCE_HOLD` | logic | `R20.2` | exact .009 sheet-1 detail PXL_20260718_101801729.jpg plus full-sheet 101754468: R20 far symbol lead descends, crosses D50.5/R29 without a junction, and continues into the lower... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R21_D8_OUTPUT_HOLD` | logic | `R21.2` | R21...R28 collective source output branch; R21 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R22_D8_OUTPUT_HOLD` | logic | `R22.2` | R21...R28 collective source output branch; R22 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R23_D8_OUTPUT_HOLD` | logic | `R23.2` | R21...R28 collective source output branch; R23 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R24_D8_OUTPUT_HOLD` | logic | `R24.2` | R21...R28 collective source output branch; R24 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R25_D8_OUTPUT_HOLD` | logic | `R25.2` | R21...R28 collective source output branch; R25 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R26_D8_OUTPUT_HOLD` | logic | `R26.2` | R21...R28 collective source output branch; R26 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R27_D8_OUTPUT_HOLD` | logic | `R27.2` | R21...R28 collective source output branch; R27 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R28_D8_OUTPUT_HOLD` | logic | `R28.2` | R21...R28 collective source output branch; R28 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds the mapping pending... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Exact .009 E3 sheet-2 frame PXL_20260718_... | Scope/capture video or timing node during video bring-up. |
| `S1_3_BOUNDARY` | logic | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not identified, so it remains... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `SYNC_B` | video/analog | `D57.17` | exact-revision .009 E3 sheet 2 and direct owner continuity 2026-07-21 disprove the older scan chase that joined D57.OUT2/pin17 to both D56 triggers; D57.OUT2 remains the separat... | Scope/capture video or timing node during video bring-up. |
| `TAPE_RUN_INT` | timing/I/O | `D10.22` | recovered .009 Э3 sheet 1 explicitly labels D10 IR4/pin22 as continuation (3) TAPE RUN INT, but the complete recovered .009 sheet 3 is the replacement FDC circuit and contains n... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TIMING_TAG17` | logic | `D36.2, D41.6` | scan sheet-2 full-resolution (D41 control-bundle crop): numbered timing rail 17 has direct junctions to D41 load pin6 and D36 second NAND input pin2; the unique remote driver re... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TIMING_TAG2` | logic | `D38.4, D34.4` | Exact .009 sheet-2 PXL_20260718_101911242.jpg draws D34.4 upward to top conductor 2; overlapping exact .009 PXL_20260718_101908284.jpg crop (950,3200)-(2350,4000) shows numbered... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.3` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `X6_A3_BOUNDARY` | video/analog | `AX603.1, X6.1` | Factory .009 assembly wire table item 151 proves A:3 to bracket X6.1; independent system drawing ДГШ3.031.011 Э6 identifies X6 as the display cable; exact .009 Э3 sheet 2 labels... | With power off, check A:3 to VT2.1/R65.1; keep VIDEO_OUT separate until continuity proves the join. |
| `XTAL16M` | video/analog | `D39.10, D103.2, D42.9, D43.9, D37.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate fr... | Scope/capture video or timing node during video bring-up. |

## Design-release disposition

- Endpoint coverage compares modeled pad-net assignments in each PCB;
  missing or mismatched endpoints remain blockers. Matching assignments
  do not establish routed connectivity, historical correctness, or safety
  of omitted functional pins.
- The 4 official FDC devices with remaining source-risk pins are tracked in
  [the footprint inventory](unmodeled-footprint-inventory.md). Their
  modeled net endpoints participate in the counts above; matching PCB
  net names does not close their remaining physical evidence holds.
- Any row affecting boot, memory, bus direction, interrupts, or video
  timing must be measured, source-proven, or explicitly redesigned before
  fabrication release. Socketing and possible bodge wires are not a
  substitute for completing the design.
- Save any vendor-preview, owner-continuity, oscilloscope, or logic-analyzer
  evidence against this checklist as bring-up progresses.
- If a point is corrected in source, update `kicad/juku.board.json` first
  and regenerate this report through the manufacturing readiness gate.
