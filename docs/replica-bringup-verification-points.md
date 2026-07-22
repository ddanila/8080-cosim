# Replica bring-up verification points

Status: **EVIDENCE INDEX READY / RISKS UNRESOLVED**

This report is generated from `kicad/juku.board.json`. It turns the
remaining source-risk annotations into an explicit checklist for vendor
preview, owner continuity sessions, and staged bring-up. It does not mark
these points as independently verified; it makes the residual risks
visible and actionable before manufacturing and first power-on.

## Summary

- Source board JSON: `kicad/juku.board.json`
- Source board JSON SHA-256: `c94c6ebef9c18a6eec5731665be896de2f04ac1610e6c44e4c4bc743e370983c`
- Final PCB source: `kicad/juku.kicad_pcb`
- Final PCB source SHA-256: `bfeff14f3998237b95b09284171cdeae3c42aa6faaca0f200dbee1e3579e03d1`
- Routed PCB source: `kicad/juku_routed.kicad_pcb`
- Routed PCB source SHA-256: `964795d21c02092b4adb4efbfb2707905b89ea5bb598bb6d389e5e7d715730bf`
- Verification-point nets: `44`
- Verification-point endpoints checked in PCB: `54`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `2295`
- All board endpoints checked in routed PCB: `2295`
- Intentional non-PCB or placement-pending endpoints excluded: `75`
- Full PCB endpoint coverage: `PASS`

| Category | Nets |
| --- | ---: |
| logic | 22 |
| memory/decode | 1 |
| sound/analog | 1 |
| timing/I/O | 1 |
| video/analog | 19 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the
fabrication source preserves the same residual-risk connectivity as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 54/54 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 54/54 net names matched |

## Full Board Endpoint Coverage

Every PCB-scoped `kicad/juku.board.json` endpoint is also checked against
the generated source PCB and the routed fabrication PCB. Bracket-mounted
`S1`, `X3`, `X4`, `X6`, `X8`, and `X9` are intentionally excluded because their cable
landings are separate `A*` PCB footprints. Assembly-DNP C63 remains in scope
because the complete inherited 4×8 grid artwork is photo-registered; its bare
landing is distinct from the absent `.009` callout between D41/D40. C51-C53 and C70-C72 are
also excluded until evidence fixes their target placement and population;
their former fit-to-space coordinates are not fabrication evidence. This is a
fabrication-source coverage gate, not a historical-source proof.

| PCB | Present | Matching net names | Result |
| --- | ---: | ---: | --- |
| `kicad/juku.kicad_pcb` | 2295/2295 | 2295/2295 | PASS |
| `kicad/juku_routed.kicad_pcb` | 2295/2295 | 2295/2295 | PASS |

## Checklist

| Net | Category | Endpoints | Source risk | Bring-up action |
| --- | --- | --- | --- | --- |
| `AMW_N` | logic | `D7.3` | D7 NAND output pin3 remains a boundary. Owner continuity 2026-07-19 disproves the earlier sheet interpretation that joined it to D29.5; D29.5 instead belongs to qualified periph... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C10_1_BOUNDARY` | video/analog | `C10.1` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C10_2_BOUNDARY` | video/analog | `C10.2` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 VT4-base assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C11_1_BOUNDARY` | video/analog | `C11.1` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C11_2_BOUNDARY` | video/analog | `C11.2` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF tank assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C12_1_BOUNDARY` | video/analog | `C12.1` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C12_2_BOUNDARY` | video/analog | `C12.2` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C15_1_BOUNDARY` | video/analog | `C15.1` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-collector assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C15_2_BOUNDARY` | video/analog | `C15.2` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-emitter assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C99_FAR` | logic | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity boundary because an RC deg... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C9_1_BOUNDARY` | video/analog | `C9.1` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF ground assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C9_2_BOUNDARY` | video/analog | `C9.2` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `CPU_WAIT_STATUS` | logic | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `CS_FDC` | logic | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 remains the physical... | Cross-check against hardware when the peripheral path is exercised. |
| `D101_D00_BOUNDARY` | logic | `D101.6` | July-2026 validated component and solder package fits identify D101 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D01_BOUNDARY` | logic | `D101.5` | July-2026 validated component and solder package fits identify D101 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D03_BOUNDARY` | logic | `D101.3` | July-2026 validated component and solder package fits identify D101 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_OE0_BOUNDARY` | logic | `D101.1` | July-2026 validated component and solder package fits identify D101 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D104_X4_IN_BOUNDARY` | logic | `D104.7` | owner resistance 2026-07-19 measures approximately 84 kohm between D104.7 and D94.13, disproving the former direct-net claim; D104 receiver input pin7 remains an independent bou... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D14_I2_BOUNDARY` | video/analog | `D14.2` | sheet-1 full-resolution К170АП2 package census identifies D14 input pin2; its remote serial-interface source is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D14_O7_BOUNDARY` | video/analog | `D14.7` | sheet-1 full-resolution К170АП2 package census identifies D14 output pin7; its remote serial-interface destination is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D26_PA6_PREN_BOUNDARY` | logic | `D26.38` | sheet-1 full-resolution: D26 PA6 pin38 leaves on the conductor labeled PREN with off-sheet marker (3); the far destination is unread, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PB4_BOUNDARY` | logic | `D26.22` | sheet-1 full-resolution: D26 PB4 pin22 enters the E8 CONTRDAT selector region, but the absent switch symbol prevents a proved remote endpoint, so this remains a measurement boun... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D29_AIN1_BOUNDARY` | logic | `D29.2` | sheet-1 native 5150x3603 command-buffer chase identifies semantic command A1/CCLCK on D29 physical A1 pin2; its westbound conductor enters the dense D5/D105 crossing bundle, whe... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_A1_TAG2` | logic | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in that boundary domai... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D58_STB_TAG5` | logic | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled... | Bench-check waveform/current path with speaker disconnected first. |
| `D94_D0_BOUNDARY` | logic | `D94.1, R8.1` | owner continuity 2026-07-19: D94.1 joins R8 through approximately 2 kohm to +5 V; no other connection was found | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_CLR2_BOUNDARY` | logic | `D99.11` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q1N_BOUNDARY` | logic | `D99.4` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin4 Q_N; the SN74123 contract plus physically grounded CLR1/pin3 constrains this output hig... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2N_BOUNDARY` | logic | `D99.12` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2_BOUNDARY` | logic | `D99.5` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `INHIB_STATUS_BOUNDARY` | logic | `D7.5, D29.3` | sheet-1 native 5150x3603 direct-junction chase: D7 data-turnaround NAND input pin5 and semantic D29 command A0 on physical package channel A2/pin3 meet at an explicit junction d... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Registered July and May component views e... | Scope/capture video or timing node during video bring-up. |
| `READY_PRE_N` | video/analog | `D30.4` | D30 section-A asynchronous preset pin4 remains a target-board continuity boundary after owner measurements moved R5 to D30.10/.12 | Scope/capture video or timing node during video bring-up. |
| `S1_3_BOUNDARY` | logic | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not identified, so it remains... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `SYNC_B` | video/analog | `D57.17` | exact-revision .009 E3 sheet 2 and direct owner continuity 2026-07-21 disprove the older scan chase that joined D57.OUT2/pin17 to both D56 triggers; D57.OUT2 remains the separat... | Scope/capture video or timing node during video bring-up. |
| `TAPE_RUN_INT` | timing/I/O | `D10.22` | recovered .009 Э3 sheet 1 explicitly labels D10 IR4/pin22 as continuation (3) TAPE RUN INT, but the complete recovered .009 sheet 3 is the replacement FDC circuit and contains n... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TIMING_TAG2` | logic | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's same-number top-edg... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.3` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `XTAL16M` | video/analog | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate fr... | Scope/capture video or timing node during video bring-up. |

## Design-release disposition

- Endpoint coverage proves that modeled nets survive into both PCB files;
  it does not prove that the modeled net is historically correct or that
  omitted functional pins are safe.
- The 3 official FDC devices with remaining source-risk pins are tracked
  separately in `docs/unmodeled-footprint-inventory.md`; they are outside
  every endpoint count above and remain design-release blockers.
- Any row affecting boot, memory, bus direction, interrupts, or video
  timing must be measured, source-proven, or explicitly redesigned before
  fabrication release. Socketing and possible bodge wires are not a
  substitute for completing the design.
- Save any vendor-preview, owner-continuity, oscilloscope, or logic-analyzer
  evidence against this checklist as bring-up progresses.
- If a point is corrected in source, update `kicad/juku.board.json` first
  and regenerate this report through the manufacturing readiness gate.
