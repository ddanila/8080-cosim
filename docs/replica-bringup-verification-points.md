# Replica bring-up verification points

Status: **ENDPOINT COVERAGE FAILED**

This report is generated from `kicad/juku.board.json`. It turns the
remaining source-risk annotations into an explicit checklist for vendor
preview, owner continuity sessions, and staged bring-up. It does not mark
these points as independently verified; it makes the residual risks
visible and actionable before manufacturing and first power-on.

## Summary

- Source board JSON: `kicad/juku.board.json`
- Final PCB source: `kicad/juku.kicad_pcb`
- Routed PCB source: `kicad/juku_routed.kicad_pcb`
- Verification-point nets: `48`
- Verification-point endpoints checked in PCB: `238`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `1993`
- All board endpoints checked in routed PCB: `1993`
- Intentional off-board endpoints excluded: `34`
- Full PCB endpoint coverage: `FAIL`

| Category | Nets |
| --- | ---: |
| FDC | 3 |
| logic | 21 |
| memory/decode | 6 |
| sound/analog | 2 |
| timing/I/O | 5 |
| video/analog | 11 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the
fabrication source preserves the same residual-risk connectivity as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 238/238 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 238/238 net names matched |

## Full Board Endpoint Coverage

Every PCB-scoped `kicad/juku.board.json` endpoint is also checked against
the generated source PCB and the routed fabrication PCB. Bracket-mounted
`S1`, `X3`, `X8`, and `X9` are intentionally excluded because their cable
landings are separate `A*` PCB footprints. This is a
fabrication-source coverage gate, not a historical-source proof.

| PCB | Present | Matching net names | Result |
| --- | ---: | ---: | --- |
| `kicad/juku.kicad_pcb` | 1993/1993 | 1993/1993 | PASS |
| `kicad/juku_routed.kicad_pcb` | 1924/1993 | 1920/1993 | FAIL |

Missing endpoints in `kicad/juku_routed.kicad_pcb`:
- `A10: D2.1`
- `A12: D2.5`
- `A14: D2.3`
- `A15: D2.6`
- `A9: D2.7`
- `D13_4_D105_2: D11.20`
- `D94_D3: D94.4`
- `D94_D4: D94.5`
- `D94_D5: D94.6`
- `D94_D6: D94.7`
- `D94_D7: D94.9`
- `D94_EN_BOUNDARY: D94.15`
- `D98_Y1_R94: D98.3`
- `D98_Y1_R94: R94.1`
- `D98_Y3_S1_2: D98.7`
- `FDC_CS_N: D94.2`
- `FDC_RE_N: D94.1`
- `FDC_WE_N: D94.3`
- `GND: R30.2`
- `GND: A62.1`
- `KBD_CONTRDAT: A50.1`
- `KBD_CTRL: A51.1`
- `KBD_FK: A55.1`
- `KBD_K0: A57.1`
- `KBD_K1: A56.1`
- `KBD_K2: A58.1`
- `KBD_SC0: A48.1`
- `KBD_SC1: A47.1`
- `KBD_SC2: A46.1`
- `KBD_SC3: A45.1`
- `KBD_SHIFT: A52.1`
- `KBD_STB: A49.1`
- `M12V: A59.1`
- `P12V: A60.1`
- `P5V: D10.16`
- `P5V: A61.1`
- `P5V: R104.2`
- `P5V: A54.1`
- `P5V: A53.1`
- `RESET: D13.6`
- `RESET: D11.21`
- `RES_RC: A17.1`
- `SER_CTS_N: D104.12`
- `SER_CTS_N: D11.17`
- `SER_DSR_N: D104.11`
- `SER_DSR_N: D11.22`
- `SER_RXD: D104.13`
- `SER_TXD: D3.9`
- `SER_TXD: R18.2`
- `SER_TXD_INV: D3.8`
- `SER_TXD_INV: D12.2`
- `S_CTS: A25.1`
- `S_CTS: D104.5`
- `S_DSR: A26.1`
- `S_DSR: D104.6`
- `S_DTP: A31.1`
- `S_OC: R18.1`
- `S_OC: R30.1`
- `S_OC: A22.1`
- `S_OC: A32.1`
- `S_RTS: A30.1`
- `S_SIN: A24.1`
- `S_SIN: D104.4`
- `S_SOUT: A29.1`
- `S_TTL: A23.1`
- `X3_HARNESS_1: A21.1`
- `X3_HARNESS_1: R104.1`
- `X3_HARNESS_7: A27.1`
- `X3_HARNESS_8: A28.1`

Mismatched endpoints in `kicad/juku_routed.kicad_pcb`:
- D93.3: `CS_FDC` != `FDC_CS_N`
- D93.4: `IORD` != `FDC_RE_N`
- D93.2: `IOWR` != `FDC_WE_N`
- D12.1: `SER_TXD` != `SER_TXD_INV`

## Checklist

| Net | Category | Endpoints | Source risk | Bring-up action |
| --- | --- | --- | --- | --- |
| `CPU_WAIT_STATUS` | logic | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `CS_FDC` | logic | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch | Cross-check against hardware when the peripheral path is exercised. |
| `D105_GATE1_Y` | logic | `D105.3` | traced sheet-1: D105 gate pins 1,2 -> 3; output destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D105_WAIT_PREINV` | logic | `D105.6` | traced sheet-1 .006: D105 pin 6 feeds D95 inverter pin 1, whose pin 2 is -WAIT/E8-1; .009 reassigns D95 to an FDC KP12, so the target-revision destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D25_T` | logic | `D7.6, D25.11` | traced sheet-1 300dpi (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; section inputs = next hop west [un... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC5_TAG4` | logic | `D26.12` | traced sheet-1 full-resolution: D26 PC5/pin12 exits as mode-bundle tag4; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC6_TAG5` | logic | `D26.11` | traced sheet-1 full-resolution: D26 PC6/pin11 exits as mode-bundle tag5; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC7_TAG6` | logic | `D26.10` | traced sheet-1 full-resolution: D26 PC7/pin10 exits as mode-bundle tag6; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D30B_D_PRE_N` | logic | `D30.10, D30.12` | traced sheet-1: D30 section-B /PRE2 pin 10 and D2 pin 12 are visibly tied by the local U-shaped wire; the shared upstream source remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); tied NAND pair = CAS-driver input; west source line [pending] | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D39_MEMCYC` | memory/decode | `D39.3, D39.4` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); out3 also drives rail 4 [rail dests pending] | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D56_QN` | timing/I/O | `D56.4` | traced sheet-2 (crop s2_dotclk_bend): D56.Q_N (pin 4) corners SOUTH at x~6074 — destination unread [chase]; the old "16MHz astable source" attribution retired | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D3` | logic | `D94.4` | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) mm; far-side destinat... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D4` | logic | `D94.5` | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D5` | logic | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D6` | logic | `D94.7` | July-2026 registered component fit and full-resolution photo prove copper from D94 output pin 7 to a distinct plated handoff near (1915,1676) px in PXL_20260710_200402344.jpg; f... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D7` | logic | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `FDC_DDEN` | FDC | `D26.13, D93.37, D6.15` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15; .009/MAME PC4 is also FDC density -> D93.37. July-2026 two-sided local D93 fit identifies pin37 and its l... | Confirm density-control level against drive/emulator behavior. |
| `FDC_DRQ` | FDC | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FDC_INTRQ` | FDC | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FRAME_INT` | timing/I/O | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (D55.OUT1 export, cro... | Cross-check against hardware when the peripheral path is exercised. |
| `HF_OUT` | video/analog | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delt... | Scope/capture video or timing node during video bring-up. |
| `IORD` | logic | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, ... (+4)` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed); D93.4 removed after local photo fit proved its direct D94.1-only branch | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `IOWR` | logic | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, ... (+4)` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed); D93.2 removed after local photo fit proved its direct D94.3-only branch | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `LATCH_B` | timing/I/O | `D40.11, D37.2, D54.9, D54.15, D54.18` | scan+mame; +D54 CLK0/1/2: the drawn 1MHz rail = the D40.QD /16 tap (HDL+MAME concur; rail tag read pending) | Cross-check against hardware when the peripheral path is exercised. |
| `PHI2TTL` | logic | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_T) + "(1)" exit to s... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PIT_BAUD` | timing/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V (power corner) | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PROM_EN` | logic | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed u... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `RAIL_E` | memory/decode | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members: DRAM pin 16 x32, b... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `RAM_SEL` | memory/decode | `D6.11, D92.5, R12.2` | scan sheet-2 (bite-2: -RAM SEL arrival -> D92.5 write-strobe NOR; source D6.11 RAM_N per sheet-1 "(1)" label). D53.6/G3 detached: its drawn feed = long west line [pending]; +R12... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `REV` | logic | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder region enable (G2A_N+G... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `RF_RAIL` | video/analog | `VT3.3, C9.2, R72.2, C10.1, R73.1, C11.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed | Scope/capture video or timing node during video bring-up. |
| `RF_TANK` | video/analog | `VT4.3, C11.2, C12.1, L1.1, R76.1, C15.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; L1 tap simplification (1/5 turns, tap -> R76) | Scope/capture video or timing node during video bring-up. |
| `ROE` | memory/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merged factory wire W13... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `SND_MIX` | sound/analog | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Bench-check waveform/current path with speaker disconnected first. |
| `SOUND_CLAMP` | sound/analog | `R66.2, VD3.2, R67.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R66.1 <- the "SOUND" PIT line [source pin pending]; VD3... | Bench-check waveform/current path with speaker disconnected first. |
| `SSTB_N` | logic | `D30.1` | sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `VIDEO_OUT` | video/analog | `VT2.1, R65.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_emaplaat.pdf, board... | Scope/capture video or timing node during video bring-up. |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `VT3_BASE` | video/analog | `R68.2, R69.2, R70.2, R71.1, C13.1, VT3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout | Scope/capture video or timing node during video bring-up. |
| `VT3_E` | video/analog | `VT3.1, R74.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `VT4_B` | video/analog | `R73.2, VT4.2, C10.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R73 4.7k drawn adjustable | Scope/capture video or timing node during video bring-up. |
| `VT4_E` | video/analog | `VT4.1, R75.1, C14.1, C15.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout | Scope/capture video or timing node during video bring-up. |
| `W_RAIL16` | memory/decode | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, ... (+27)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: the sim cannot reprodu... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `XACK_N` | logic | `D2.2` | traced sheet-1: label -XACK enters D2 A5/pin 2 from edge code 106C; the existing X1.106C transcription says IORC_N, so the connector merge remains an explicit conflict boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `XTAL16M` | timing/I/O | `D103.2, D42.9, D43.9` | traced sheet-2 (crop s2_dotclk_bend): the 16MHz crystal rail (bundle tag 14) is a SEPARATE net from D56.Q_N; it clocks D103 + the ИР16 shifters. Likely = the OSC net continuatio... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |

## Design-release disposition

- Endpoint coverage proves that modeled nets survive into both PCB files;
  it does not prove that the modeled net is historically correct or that
  omitted functional pins are safe.
- The 9 official IC footprints with no board-JSON pin model are tracked
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
