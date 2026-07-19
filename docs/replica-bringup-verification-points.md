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
- Verification-point nets: `49`
- Verification-point endpoints checked in PCB: `58`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `2290`
- All board endpoints checked in routed PCB: `2290`
- Intentional non-PCB or placement-pending endpoints excluded: `77`
- Full PCB endpoint coverage: `FAIL`

| Category | Nets |
| --- | ---: |
| logic | 27 |
| memory/decode | 2 |
| sound/analog | 1 |
| timing/I/O | 1 |
| video/analog | 18 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the
fabrication source preserves the same residual-risk connectivity as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 58/58 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 58/58 net names matched |

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
| `kicad/juku.kicad_pcb` | 2290/2290 | 2290/2290 | PASS |
| `kicad/juku_routed.kicad_pcb` | 1871/2290 | 1754/2290 | FAIL |

Missing endpoints in `kicad/juku_routed.kicad_pcb`:
- `A10: D2.1`
- `A12: D2.5`
- `A14: D2.3`
- `A15: D2.6`
- `A9: D2.7`
- `AMW_N: D7.3`
- `C12_2_BOUNDARY: C12.2`
- `C94_1_BOUNDARY: C94.1`
- `C94_2_BOUNDARY: C94.2`
- `CAS: D38.1`
- `CLK_123M: D57.9`
- `CLK_123M: D34.12`
- `D100_CONTROL_SHEET1_BOUNDARY: D100.9`
- `D100_CONTROL_SHEET1_BOUNDARY: D100.11`
- `D101_D00_BOUNDARY: D101.6`
- `D101_D01_BOUNDARY: D101.5`
- `D101_D02_R92_R99: D101.4`
- `D101_D02_R92_R99: R92.1`
- `D101_D02_R92_R99: R99.2`
- `D101_D03_BOUNDARY: D101.3`
- `D101_OE0_BOUNDARY: D101.1`
- `D102_C1_C22: D102.14`
- `D102_C1_C22: C22.1`
- `D102_C2_C20: D102.6`
- `D102_C2_C20: C20.1`
- `D102_RC1_C22_R102: D102.15`
- `D102_RC1_C22_R102: C22.2`
- `D102_RC1_C22_R102: R102.1`
- `D102_RC2_C20_R108: D102.7`
- `D102_RC2_C20_R108: C20.2`
- `D102_RC2_C20_R108: R108.1`
- `D104_X4_IN_BOUNDARY: D104.7`
- `D104_X4_OUT_BOUNDARY: D104.10`
- `D105_10_H: D13.13`
- `D105_10_H: X1.107B`
- `D105_10_H: R1.2`
- `D106_PRESET_HIGH: D106.1`
- `D106_PRESET_HIGH: D106.5`
- `D106_PRESET_HIGH: D106.9`
- `D106_PRESET_HIGH: D106.10`
- `D106_PRESET_HIGH: D106.15`
- `D106_PRESET_HIGH: R78.1`
- `D13_4_D105_2: D11.20`
- `D13_4_D105_2: D30.11`
- `D14_I2_BOUNDARY: D14.2`
- `D14_O7_BOUNDARY: D14.7`
- `D26_PA6_PREN_BOUNDARY: D26.38`
- `D26_PB4_BOUNDARY: D26.22`
- `D26_PC0_D3_I5: D26.14`
- `D26_PC0_D3_I5: D3.5`
- `D26_PC1_D3_I3: D26.15`
- `D26_PC1_D3_I3: D3.3`
- `D29_AIN1_BOUNDARY: D29.2`
- `D30_Q2N_D29_AIN7: D30.8`
- `D33_CLK_RC: R46.2`
- `D33_CLK_RC: C6.1`
- `D33_CLK_RC: D33.9`
- `D34_A1_TAG2: D34.4`
- `D34_RC_DRIVE: D34.6`
- `D34_RC_DRIVE: C5.1`
- `D34_RC_NODE: C5.2`
- `D34_RC_NODE: R33.1`
- `D34_RC_NODE: D34.2`
- `D39_MEMCYC: D38.5`
- `D3_O4_D6_A6: D3.4`
- `D3_O6_D6_A5: D3.6`
- `D40Q1_D39: D95.11`
- `D40Q1_D39: D95.12`
- `D40Q1_D39: D95.13`
- `D40Q2_D33: D95.3`
- `D40Q2_D33: D95.4`
- `D40QA: R46.1`
- `D40QA: D95.10`
- `D40_CTRL_PULL: R34.2`
- `D40_CTRL_PULL: D40.1`
- `D40_CTRL_PULL: D40.9`
- `D56_Q2N_TAG16: D56.12`
- `D56_Q2_D34: D56.5`
- `D56_Q2_D34: D34.9`
- `D56_QN_D34: D34.10`
- `D58_STB_TAG5: D58.11`
- `D59_O10_TAG10: D59.10`
- `D6_V_ENABLE: D6.13`
- `D6_V_ENABLE: D6.14`
- `D6_V_ENABLE: D13.12`
- `D93_1_OPEN_STUB: D93.1`
- `D93_RG_NC: D93.25`
- `D93_TEST_WF_VFOE: D93.22`
- `D93_TEST_WF_VFOE: D93.33`
- `D94_A4_D101_Q0: D101.7`
- `D94_D0_BOUNDARY: D94.1`
- `D94_D1_D99_A2N: D94.2`
- `D94_D1_D99_A2N: D99.9`
- `D94_D1_D99_A2N: R89.1`
- `D94_D5: D94.6`
- `D94_D6: D94.7`
- `D94_D7: D94.9`
- `D96_IRQ_CLOCK_SHEET1_BOUNDARY: D96.11`
- `D96_IRQ_Q_SHEET1_BOUNDARY: D96.9`
- `D96_Q2_N_TEST_LANDING: D96.8`
- `D96_TOGGLE_FEEDBACK: D96.2`
- `D96_TOGGLE_FEEDBACK: D96.6`
- `D97_C1_C16: D97.14`
- `D97_C1_C16: C16.2`
- `D97_C2_C19_R86_TARGET: D97.6`
- `D97_C2_C19_R86_TARGET: C19.2`
- `D97_C2_C19_R86_TARGET: R86.1`
- `D97_RC1_C16: D97.15`
- `D97_RC1_C16: C16.1`
- `D97_RC2_C19_R100: D97.7`
- `D97_RC2_C19_R100: C19.1`
- `D97_RC2_C19_R100: R100.1`
- `D98_Y1_R94: D98.3`
- `D98_Y1_R94: R94.1`
- `D98_Y1_R94: D28.5`
- `D98_Y3_S1_2: D98.7`
- `D98_Y3_S1_2: D97.2`
- `D99_B2_SHEET1_BOUNDARY: D99.10`
- `D99_B_TEST_LANDING: D99.2`
- `D99_C1_TIMING: D99.14`
- `D99_C1_TIMING: C18.2`
- `D99_C2_TIMING: D99.6`
- `D99_C2_TIMING: C17.2`
- `D99_CLR2_BOUNDARY: D99.11`
- `D99_Q1N_BOUNDARY: D99.4`
- `D99_Q1_NC: D99.13`
- `D99_Q2N_BOUNDARY: D99.12`
- `D99_Q2_BOUNDARY: D99.5`
- `D99_RC1_TIMING: D99.15`
- `D99_RC1_TIMING: C18.1`
- `D99_RC1_TIMING: R103.1`
- `D99_RC2_TIMING: D99.7`
- `D99_RC2_TIMING: C17.1`
- `D99_RC2_TIMING: R97.1`
- `FDC_CLK: D95.7`
- `FDC_CLK: D93.24`
- `FDC_CS_N: D94.15`
- `FDC_DDEN: D95.14`
- `FDC_DDEN: R92.2`
- `FDC_DIR_TO_D100: D93.16`
- `FDC_DRIVE_SIZE_5_8: D95.2`
- `FDC_DRQ: D28.11`
- `FDC_DSEL_IN: D28.1`
- `FDC_EARLY_SEL: D93.17`
- `FDC_EARLY_SEL: D101.2`
- `FDC_HLD_TO_D100: D93.28`
- `FDC_INDEX_STATUS: D98.5`
- `FDC_INDEX_STATUS: D93.35`
- `FDC_INTRQ: D28.13`
- `FDC_INTRQ: R93.1`
- `FDC_IRQ_CONDITIONED_N: D28.10`
- `FDC_IRQ_CONDITIONED_N: D28.12`
- `FDC_IRQ_CONDITIONED_N: D96.10`
- `FDC_IRQ_CONDITIONED_N: D96.12`
- `FDC_IRQ_CONDITIONED_N: R95.1`
- `FDC_LATE_SEL: D93.18`
- `FDC_LATE_SEL: D101.14`
- `FDC_PRECOMP_WRDATA: D101.9`
- `FDC_RAW_READ: D97.4`
- `FDC_RAW_READ: D93.27`
- `FDC_RAW_READ: D106.11`
- `FDC_RCLK: D96.5`
- `FDC_RCLK: D93.26`
- `FDC_READY: D28.6`
- `FDC_READY: D93.23`
- `FDC_READY: D93.32`
- `FDC_READY: R84.1`
- `FDC_RE_N: D94.3`
- `FDC_RE_N: R88.1`
- `FDC_SEPARATOR_CLOCK: D95.9`
- `FDC_SEPARATOR_CLOCK: D106.4`
- `FDC_STEP_TO_D100: D93.15`
- `FDC_TG43_TO_D100: D93.29`
- `FDC_TR00_STATUS: D98.11`
- `FDC_TR00_STATUS: D93.34`
- `FDC_WDATA_DELAY_IN: D93.31`
- `FDC_WDATA_DELAY_IN: D97.10`
- `FDC_WE_N: D94.4`
- `FDC_WE_N: R87.1`
- `FDC_WG_TO_D100: D93.30`
- `FDC_WPRT_STATUS: D98.13`
- `FDC_WPRT_STATUS: D93.36`
- `FRAME_INT: D35.8`
- `GND: D106.14`
- `GND: R30.2`
- `GND: R105.2`
- `GND: R107.2`
- `GND: D43.1`
- `GND: D39.2`
- `GND: D38.2`
- `GND: D14.1`
- `GND: A62.1`
- `GND: D56.1`
- `GND: D56.9`
- `GND: D34.5`
- `GND: R33.2`
- `GND: C6.2`
- `GND: D41.2`
- `GND: D41.3`
- `GND: D41.4`
- `GND: D41.5`
- `GND: AX604.1`
- `GND: AX406.1`
- `GND: D97.1`
- `GND: D97.9`
- `GND: D102.1`
- `GND: D102.9`
- `GND: D95.1`
- `GND: D95.15`
- `GND: D98.1`
- `GND: D98.15`
- `GND: D101.13`
- `GND: D101.15`
- `GND: D99.3`
- `GND: D99.1`
- `GND: R99.1`
- `HOR_RTR: D54.13`
- `INHIB_STATUS_BOUNDARY: D7.5`
- `INHIB_STATUS_BOUNDARY: D29.3`
- `IORD: D7.9`
- `IOWR_RAW_N: D7.10`
- `IO_CYCLE_H: D7.8`
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
- `LATCH_B: D95.5`
- `LATCH_B: D95.6`
- `LATCH_SIG: D33.12`
- `LATCH_SIG: D39.9`
- `M12V: A59.1`
- `MA6: E1.3`
- `MEMR: D29.6`
- `MEMR: W11.1`
- `MEMR_D7: W11.2`
- `MEMW: D29.1`
- `MEMW: W19.1`
- `MEMW: D7.4`
- `MEMW_D7P2: W19.2`
- `OSC: C73.2`
- `OSC_FB: D59.9`
- `OSC_FB: R31.1`
- `OSC_FB: R32.1`
- `OSC_FB: Z1.1`
- `OSC_PRE: D59.8`
- `OSC_PRE: D59.1`
- `OSC_PRE: R31.2`
- `P12V: D93.40`
- `P12V: A60.1`
- `P12V: R66.1`
- `P5V: R78.2`
- `P5V: D10.16`
- `P5V: A61.1`
- `P5V: R1.1`
- `P5V: D40.7`
- `P5V: D40.10`
- `P5V: D41.1`
- `P5V: D41.8`
- `P5V: VD1.1`
- `P5V: R34.1`
- `P5V: D34.13`
- `P5V: D57.11`
- `P5V: R104.2`
- `P5V: A54.1`
- `P5V: A53.1`
- `P5V: AX412.1`
- `P5V: AX413.1`
- `P5V: R87.2`
- `P5V: R88.2`
- `P5V: R89.2`
- `P5V: R79.2`
- `P5V: R80.2`
- `P5V: R81.2`
- `P5V: R82.2`
- `P5V: R83.2`
- `P5V: R84.2`
- `P5V: R85.2`
- `P5V: R98.2`
- `P5V: R100.2`
- `P5V: R102.2`
- `P5V: R108.2`
- `P5V: R86.2`
- `P5V: R97.2`
- `P5V: R103.2`
- `P5V: R93.2`
- `P5V: R95.2`
- `PHI1: W7.1`
- `PHI1_D35: W7.2`
- `POF: D35.3`
- `PRECOMP_CASCADE_1: D97.12`
- `PRECOMP_CASCADE_1: D102.10`
- `PRECOMP_CASCADE_2: D102.12`
- `PRECOMP_CASCADE_2: D102.2`
- `PRECOMP_TAP_1: D97.5`
- `PRECOMP_TAP_1: D101.10`
- `PRECOMP_TAP_2: D102.5`
- `PRECOMP_TAP_2: D101.11`
- `PRECOMP_TAP_3: D102.13`
- `PRECOMP_TAP_3: D101.12`
- `PST_CLK: R32.2`
- `R94_P2_BOUNDARY: R94.2`
- `RESET: D13.6`
- `RESET: D11.21`
- `RESET: D93.19`
- `RES_RC: A17.1`
- `RES_RC: VD1.2`
- `S3_3: D46.15`
- `S3_4: D46.1`
- `SEP_D106_Q3: D106.7`
- `SEP_D106_Q3: D28.9`
- `SEP_D28_CLK: D28.8`
- `SEP_D28_CLK: D96.3`
- `SEP_D28_CLK: R85.1`
- `SER_CTS_N: D104.12`
- `SER_CTS_N: D11.17`
- `SER_DSR_N: D104.11`
- `SER_DSR_N: D11.22`
- `SER_RXD: D104.13`
- `SER_TXD: D3.9`
- `SER_TXD: R18.2`
- `SER_TXD_INV: D3.8`
- `SER_TXD_INV: D12.2`
- `SHIFT_G: D41.9`
- `SHIFT_G: D42.8`
- `SHIFT_G: D43.8`
- `SOUND_CLAMP: AX603.1`
- `STSTB: W8.1`
- `STSTB_D38: W8.2`
- `SYNDET_S4: D11.16`
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
- `S_TTL: W20.1`
- `S_TTL_D3: W20.2`
- `TAPE_RUN_INT: D10.22`
- `TIMING_TAG17: D36.2`
- `TIMING_TAG17: D41.6`
- `TIMING_TAG2: D38.4`
- `USART_RXRDY_IRQ: D10.20`
- `USART_RXRDY_IRQ: D11.14`
- `USART_TXRDY_IRQ: D10.21`
- `USART_TXRDY_IRQ: D11.15`
- `VERT_RTR: D35.9`
- `VERT_SYNC: D55.17`
- `VID_MUX_G: E14.1`
- `W10_QA_SEL: W10.1`
- `W10_QA_SEL_D50: D51.1`
- `W10_QA_SEL_D50: W10.2`
- `WR: D13.3`
- `WREQ_N: X1.107C`
- `WREQ_N: D96.1`
- `WREQ_N: D96.4`
- `WREQ_N: D97.3`
- `WREQ_N: D97.11`
- `WREQ_N: D102.3`
- `WREQ_N: D102.11`
- `X2_IRQ0: X2.214`
- `X2_IRQ0: R105.1`
- `X2_PB7: R107.1`
- `X3_HARNESS_1: A21.1`
- `X3_HARNESS_1: R104.1`
- `X3_HARNESS_7: A27.1`
- `X3_HARNESS_8: A28.1`
- `X4_01_NC_HARNESS: AX401.1`
- `X4_02_BOUNDARY: AX402.1`
- `X4_03_BOUNDARY: AX403.1`
- `X4_04_BOUNDARY: AX404.1`
- `X4_05_BOUNDARY: AX405.1`
- `X4_DIR_N: AX416.1`
- `X4_DSEL0_N: D28.4`
- `X4_DSEL0_N: AX422.1`
- `X4_DSEL1_N: D28.2`
- `X4_DSEL1_N: D28.3`
- `X4_DSEL1_N: AX421.1`
- `X4_DSEL1_N: R98.1`
- `X4_HLOAD_N: AX417.1`
- `X4_INDEX_N: AX415.1`
- `X4_INDEX_N: D98.4`
- `X4_INDEX_N: R81.1`
- `X4_MOTOR_ON_N: AX419.1`
- `X4_RD_DATA: AX423.1`
- `X4_RD_DATA: D98.6`
- `X4_RD_DATA: R79.1`
- `X4_READY_N: AX408.1`
- `X4_READY_N: D98.2`
- `X4_READY_N: R83.1`
- `X4_SIDE_SEL: AX420.1`
- `X4_STEP_N: AX409.1`
- `X4_TG43: AX410.1`
- `X4_TR00_N: AX414.1`
- `X4_TR00_N: D98.12`
- `X4_TR00_N: R80.1`
- `X4_WR_DATA_N: AX411.1`
- `X4_WR_GATE_N: AX418.1`
- `X4_WR_PROTECT_N: AX407.1`
- `X4_WR_PROTECT_N: D98.14`
- `X4_WR_PROTECT_N: R82.1`
- `XTAL16M: D39.10`
- `XTAL_TRIM: Z1.2`
- `XTAL_TRIM: C73.1`

Mismatched endpoints in `kicad/juku_routed.kicad_pcb`:
- D29.15: `MRC_N` != `AMWC_N`
- D107.19: `BA7` != `BA0`
- D94.10: `BA11` != `BA0`
- D107.18: `BA6` != `BA1`
- D94.11: `BA12` != `BA1`
- D4.19: `BA8` != `BA10`
- D4.18: `BA9` != `BA11`
- D4.15: `BA13` != `BA12`
- D4.16: `BA12` != `BA13`
- D4.17: `BA15` != `BA14`
- D4.14: `BA14` != `BA15`
- D107.17: `BA5` != `BA2`
- D107.16: `BA4` != `BA3`
- D107.15: `BA3` != `BA4`
- D107.14: `BA2` != `BA5`
- D107.13: `BA1` != `BA6`
- D107.12: `BA0` != `BA7`
- D4.12: `BA10` != `BA8`
- D4.13: `BA11` != `BA9`
- C10.1: `RF_RAIL` != `C10_1_BOUNDARY`
- C10.2: `VT4_B` != `C10_2_BOUNDARY`
- C11.1: `RF_RAIL` != `C11_1_BOUNDARY`
- C11.2: `RF_TANK` != `C11_2_BOUNDARY`
- C12.1: `RF_TANK` != `C12_1_BOUNDARY`
- C15.1: `RF_TANK` != `C15_1_BOUNDARY`
- C15.2: `VT4_E` != `C15_2_BOUNDARY`
- C99.2: `GND` != `C99_FAR`
- C9.1: `GND` != `C9_1_BOUNDARY`
- C9.2: `RF_RAIL` != `C9_2_BOUNDARY`
- D105.11: `D105_MRD_INV` != `D105_MEMW_INV`
- D30.13: `D105_MRD_INV` != `D105_MEMW_INV`
- R5.2: `READY_PRE_N` != `D30B_D_PRE_N`
- D29.7: `IORD` != `D30_Q2N_D29_AIN7`
- D6.1: `MEM_MODE1` != `D3_O4_D6_A6`
- D6.2: `MEM_MODE0` != `D3_O6_D6_A5`
- D56.4: `D56_QN` != `D56_QN_D34`
- D94.14: `BA15` != `D94_A4_D101_Q0`
- D93.7: `FDC_DAL0` != `DB0`
- D93.8: `FDC_DAL1` != `DB1`
- D93.9: `FDC_DAL2` != `DB2`
- D93.10: `FDC_DAL3` != `DB3`
- D93.11: `FDC_DAL4` != `DB4`
- D93.12: `FDC_DAL5` != `DB5`
- D93.13: `FDC_DAL6` != `DB6`
- D93.14: `FDC_DAL7` != `DB7`
- D105.9: `D2_WAIT_RAW` != `DBIN`
- D105.6: `D105_WAIT_PREINV` != `DBIN_GATED`
- D5.4: `DBIN` != `DBIN_GATED`
- D93.3: `CS_FDC` != `FDC_CS_N`
- D100.1: `DB0` != `FDC_DIR_TO_D100`
- D26.17: `MEM_MODE1` != `FDC_DRIVE_SIZE_5_8`
- D26.12: `D26_PC5_TAG4` != `FDC_DSEL_IN`
- D100.3: `DB2` != `FDC_HLD_TO_D100`
- D26.16: `MEM_MODE0` != `FDC_MOTOR_EN`
- D100.7: `DB6` != `FDC_MOTOR_EN`
- D100.6: `DB5` != `FDC_PRECOMP_WRDATA`
- D93.4: `IORD` != `FDC_RE_N`
- D26.11: `D26_PC6_TAG5` != `FDC_SIDE_SEL`
- D100.8: `DB7` != `FDC_SIDE_SEL`
- D100.2: `DB1` != `FDC_STEP_TO_D100`
- D100.4: `DB3` != `FDC_TG43_TO_D100`
- D93.2: `IOWR` != `FDC_WE_N`
- D100.5: `DB4` != `FDC_WG_TO_D100`
- D29.17: `IOM_N` != `INHIB_N`
- D3.2: `IR6` != `INT6_BUF`
- D29.16: `MWC_N` != `IOM_N`
- D29.12: `IOWC_N` != `IORC_N`
- D2.2: `XACK_N` != `IORC_N`
- D29.8: `IOWR` != `IORD`
- D29.4: `MEMW` != `IORD`
- D94.12: `BA13` != `IORD`
- D29.13: `IORC_N` != `IOWC_N`
- D105.3: `D105_GATE1_Y` != `IOWR`
- D94.13: `BA14` != `IOWR`
- D29.5: `MEMR` != `IOWR`
- D5.27: `IOWR` != `IOWR_RAW_N`
- D6.15: `FDC_DDEN` != `IO_CYCLE_H`
- D105.1: `MEMW` != `IO_CYCLE_H`
- D7.1: `MEMR` != `MEMR_D7`
- D105.12: `MEMR` != `MEMW`
- D105.13: `MEMR` != `MEMW`
- D7.2: `MEMW` != `MEMW_D7P2`
- D29.14: `AMWC_N` != `MRC_N`
- D29.19: `INHIB_N` != `MWC_N`
- VT2.2: `VT2_BASE` != `P5V`
- VT1.2: `SND_BASE` != `P5V`
- C34.1: `RAIL_H` != `P5V`
- D35.10: `PHI1` != `PHI1_D35`
- D26.10: `D26_PC7_TAG6` != `POF`
- D7.13: `IORD` != `PROM_EN`
- R67.2: `SND_MIX` != `R67_2_BOUNDARY`
- D2.12: `D2_WAIT_RAW` != `READY_D`
- D45.10: `GND` != `S3_1`
- D45.9: `GND` != `S3_2`
- D46.10: `S3_1` != `S3_5`
- D46.9: `S3_2` != `S3_6`
- D12.1: `SER_TXD` != `SER_TXD_INV`
- VT1.3: `P5V` != `SND_BASE`
- D38.8: `STSTB` != `STSTB_D38`
- D7.12: `IOWR` != `SYNC`
- D3.10: `S_TTL` != `S_TTL_D3`
- D55.13: `FRAME_INT` != `VERT_RTR`
- VT2.3: `P5V` != `VT2_BASE`
- D50.1: `W10_QA_SEL` != `W10_QA_SEL_D50`
- D6.11: `RAM_SEL` != `WREQ_N`
- D92.5: `RAM_SEL` != `WREQ_N`
- R12.2: `RAM_SEL` != `WREQ_N`
- D10.18: `FDC_INTRQ` != `X2_IRQ0`
- D10.19: `FDC_DRQ` != `X2_PB7`
- D100.19: `FDC_DAL0` != `X4_DIR_N`
- D100.17: `FDC_DAL2` != `X4_HLOAD_N`
- D100.13: `FDC_DAL6` != `X4_MOTOR_ON_N`
- D100.12: `FDC_DAL7` != `X4_SIDE_SEL`
- D100.18: `FDC_DAL1` != `X4_STEP_N`
- D100.16: `FDC_DAL3` != `X4_TG43`
- D100.14: `FDC_DAL5` != `X4_WR_DATA_N`
- D100.15: `FDC_DAL4` != `X4_WR_GATE_N`

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
| `D104_X4_OUT_BOUNDARY` | logic | `D104.10` | July-2026 reflected D104 solder fit identifies output pin10 at (2350.714,1249.143) px with no B.Cu departure in two backside views; both component overlaps hide its possible F.C... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D14_I2_BOUNDARY` | video/analog | `D14.2` | sheet-1 full-resolution К170АП2 package census identifies D14 input pin2; its remote serial-interface source is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D14_O7_BOUNDARY` | video/analog | `D14.7` | sheet-1 full-resolution К170АП2 package census identifies D14 output pin7; its remote serial-interface destination is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D26_PA6_PREN_BOUNDARY` | logic | `D26.38` | sheet-1 full-resolution: D26 PA6 pin38 leaves on the conductor labeled PREN with off-sheet marker (3); the far destination is unread, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PB4_BOUNDARY` | logic | `D26.22` | sheet-1 full-resolution: D26 PB4 pin22 enters the E8 CONTRDAT selector region, but the absent switch symbol prevents a proved remote endpoint, so this remains a measurement boun... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D29_AIN1_BOUNDARY` | logic | `D29.2` | sheet-1 native 5150x3603 command-buffer chase identifies semantic command A1/CCLCK on D29 physical A1 pin2; its westbound conductor enters the dense D5/D105 crossing bundle, whe... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_A1_TAG2` | logic | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in that boundary domai... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D56_Q2N_TAG16` | memory/decode | `D56.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D56 second-section Q2_N pin12 leaves east on conductor code 16; the former D34.10 merge is disproved by the distinct... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D58_STB_TAG5` | logic | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled... | Bench-check waveform/current path with speaker disconnected first. |
| `D94_D0_BOUNDARY` | logic | `D94.1, R8.1` | owner continuity 2026-07-19: D94.1 joins R8 through approximately 2 kohm to +5 V; no other connection was found | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D5` | logic | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D6` | logic | `D94.7` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because its two-sided projec... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D7` | logic | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_CLR2_BOUNDARY` | logic | `D99.11` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q1N_BOUNDARY` | logic | `D99.4` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2N_BOUNDARY` | logic | `D99.12` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2_BOUNDARY` | logic | `D99.5` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `INHIB_STATUS_BOUNDARY` | logic | `D7.5, D29.3` | sheet-1 native 5150x3603 direct-junction chase: D7 data-turnaround NAND input pin5 and semantic D29 command A0 on physical package channel A2/pin3 meet at an explicit junction d... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Registered July and May component views e... | Scope/capture video or timing node during video bring-up. |
| `R94_P2_BOUNDARY` | logic | `R94.2` | July-2026 registered component photo identifies the lower terminal of R94 220 ohm; only the upper terminal to D98.3 is proved and pin2 remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `READY_PRE_N` | video/analog | `D30.4` | D30 section-A asynchronous preset pin4 remains a target-board continuity boundary after owner measurements moved R5 to D30.10/.12 | Scope/capture video or timing node during video bring-up. |
| `S1_3_BOUNDARY` | logic | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not identified, so it remains... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TAPE_RUN_INT` | timing/I/O | `D10.22` | recovered .009 Э3 sheet 1 explicitly labels D10 IR4/pin22 as continuation (3) TAPE RUN INT, but the complete recovered .009 sheet 3 is the replacement FDC circuit and contains n... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TIMING_TAG2` | logic | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's same-number top-edg... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.3` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `XTAL16M` | video/analog | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate fr... | Scope/capture video or timing node during video bring-up. |

## Design-release disposition

- Endpoint coverage proves that modeled nets survive into both PCB files;
  it does not prove that the modeled net is historically correct or that
  omitted functional pins are safe.
- The 2 official FDC devices with remaining source-risk pins are tracked
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
