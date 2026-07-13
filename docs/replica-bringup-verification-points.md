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
- Verification-point nets: `246`
- Verification-point endpoints checked in PCB: `409`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `2239`
- All board endpoints checked in routed PCB: `2239`
- Intentional off-board endpoints excluded: `61`
- Full PCB endpoint coverage: `FAIL`

| Category | Nets |
| --- | ---: |
| FDC | 23 |
| logic | 182 |
| memory/decode | 11 |
| sound/analog | 1 |
| timing/I/O | 5 |
| video/analog | 24 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the
fabrication source preserves the same residual-risk connectivity as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 409/409 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 409/409 net names matched |

## Full Board Endpoint Coverage

Every PCB-scoped `kicad/juku.board.json` endpoint is also checked against
the generated source PCB and the routed fabrication PCB. Bracket-mounted
`S1`, `X3`, `X4`, `X8`, and `X9` are intentionally excluded because their cable
landings are separate `A*` PCB footprints. This is a
fabrication-source coverage gate, not a historical-source proof.

| PCB | Present | Matching net names | Result |
| --- | ---: | ---: | --- |
| `kicad/juku.kicad_pcb` | 2239/2239 | 2239/2239 | PASS |
| `kicad/juku_routed.kicad_pcb` | 1883/2239 | 1808/2239 | FAIL |

Missing endpoints in `kicad/juku_routed.kicad_pcb`:
- `A10: D2.1`
- `A12: D2.5`
- `A14: D2.3`
- `A15: D2.6`
- `A9: D2.7`
- `AMW_N: D7.3`
- `C12_2_BOUNDARY: C12.2`
- `C16_1_BOUNDARY: C16.1`
- `C16_2_BOUNDARY: C16.2`
- `C19_1_BOUNDARY: C19.1`
- `C19_2_BOUNDARY: C19.2`
- `C20_1_BOUNDARY: C20.1`
- `C20_2_BOUNDARY: C20.2`
- `C22_1_BOUNDARY: C22.1`
- `C22_2_BOUNDARY: C22.2`
- `C94_1_BOUNDARY: C94.1`
- `C94_2_BOUNDARY: C94.2`
- `CAS: D38.1`
- `CLK_123M: D57.9`
- `CLK_123M: D34.12`
- `D100_OE_BOUNDARY: D100.9`
- `D100_T_BOUNDARY: D100.11`
- `D101_A0_BOUNDARY: D101.14`
- `D101_A1_BOUNDARY: D101.2`
- `D101_D00_BOUNDARY: D101.6`
- `D101_D01_BOUNDARY: D101.5`
- `D101_D02_BOUNDARY: D101.4`
- `D101_D03_BOUNDARY: D101.3`
- `D101_D10_BOUNDARY: D101.10`
- `D101_D11_BOUNDARY: D101.11`
- `D101_D12_BOUNDARY: D101.12`
- `D101_D13_BOUNDARY: D101.13`
- `D101_OE0_BOUNDARY: D101.1`
- `D101_OE1_BOUNDARY: D101.15`
- `D101_Q0_BOUNDARY: D101.7`
- `D101_Q1_BOUNDARY: D101.9`
- `D102_A1N_BOUNDARY: D102.1`
- `D102_A2N_BOUNDARY: D102.9`
- `D102_B1_BOUNDARY: D102.2`
- `D102_B2_BOUNDARY: D102.10`
- `D102_C1_BOUNDARY: D102.14`
- `D102_C2_BOUNDARY: D102.6`
- `D102_CLR1_BOUNDARY: D102.3`
- `D102_CLR2_BOUNDARY: D102.11`
- `D102_Q1N_BOUNDARY: D102.4`
- `D102_Q1_BOUNDARY: D102.13`
- `D102_Q2N_BOUNDARY: D102.12`
- `D102_Q2_BOUNDARY: D102.5`
- `D102_RC1_BOUNDARY: D102.15`
- `D102_RC2_BOUNDARY: D102.7`
- `D105_10_H: D13.13`
- `D106_BO_BOUNDARY: D106.13`
- `D106_CLR_BOUNDARY: D106.14`
- `D106_CO_BOUNDARY: D106.12`
- `D106_D0_BOUNDARY: D106.15`
- `D106_D1_BOUNDARY: D106.1`
- `D106_D2_BOUNDARY: D106.10`
- `D106_D3_BOUNDARY: D106.9`
- `D106_DOWN_BOUNDARY: D106.4`
- `D106_LOAD_BOUNDARY: D106.11`
- `D106_Q0_BOUNDARY: D106.3`
- `D106_Q1_BOUNDARY: D106.2`
- `D106_Q2_BOUNDARY: D106.6`
- `D106_UP_BOUNDARY: D106.5`
- `D13_4_D105_2: D11.20`
- `D13_I3_BOUNDARY: D13.3`
- `D14_I2_BOUNDARY: D14.2`
- `D14_O7_BOUNDARY: D14.7`
- `D26_PA6_PREN_BOUNDARY: D26.38`
- `D26_PB4_BOUNDARY: D26.22`
- `D26_PC0_BOUNDARY: D26.14`
- `D26_PC1_BOUNDARY: D26.15`
- `D26_PC5_RN_IN: D28.3`
- `D26_PC6_STOP_IN: D28.1`
- `D29_AIN1_BOUNDARY: D29.2`
- `D30_CLK2_BOUNDARY: D30.11`
- `D30_Q2N_BOUNDARY: D30.8`
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
- `D40QA: R46.1`
- `D40_CTRL_PULL: R34.2`
- `D40_CTRL_PULL: D40.1`
- `D40_CTRL_PULL: D40.9`
- `D56_Q2N_TAG16: D56.12`
- `D56_Q2_D34: D56.5`
- `D56_Q2_D34: D34.9`
- `D56_QN_D34: D34.10`
- `D58_STB_TAG5: D58.11`
- `D59_O10_TAG10: D59.10`
- `D6_MEM_SELECT_N: D13.12`
- `D6_V_ENABLE: D6.13`
- `D6_V_ENABLE: D6.14`
- `D93_CLK_BOUNDARY: D93.24`
- `D93_DIRC_BOUNDARY: D93.16`
- `D93_EARLY_BOUNDARY: D93.17`
- `D93_HLD_BOUNDARY: D93.28`
- `D93_HLT_BOUNDARY: D93.23`
- `D93_INDEX_BOUNDARY: D93.35`
- `D93_LATE_BOUNDARY: D93.18`
- `D93_MR_BOUNDARY: D93.19`
- `D93_RAW_READ_BOUNDARY: D93.27`
- `D93_READY_BOUNDARY: D93.32`
- `D93_RG_BOUNDARY: D93.25`
- `D93_STEP_BOUNDARY: D93.15`
- `D93_TEST_BOUNDARY: D93.22`
- `D93_TG43_BOUNDARY: D93.29`
- `D93_TR00_BOUNDARY: D93.34`
- `D93_VDD12_BOUNDARY: D93.40`
- `D93_WDATA_BOUNDARY: D93.31`
- `D93_WF_VFOE_BOUNDARY: D93.33`
- `D93_WG_BOUNDARY: D93.30`
- `D93_WPRT_BOUNDARY: D93.36`
- `D94_D3: D94.4`
- `D94_D4: D94.5`
- `D94_D5: D94.6`
- `D94_D6: D94.7`
- `D94_D7: D94.9`
- `D94_EN_BOUNDARY: D94.15`
- `D95_A0_BOUNDARY: D95.14`
- `D95_A1_BOUNDARY: D95.2`
- `D95_D00_BOUNDARY: D95.6`
- `D95_D01_BOUNDARY: D95.5`
- `D95_D02_BOUNDARY: D95.4`
- `D95_D03_BOUNDARY: D95.3`
- `D95_D10_BOUNDARY: D95.10`
- `D95_D11_BOUNDARY: D95.11`
- `D95_D12_BOUNDARY: D95.12`
- `D95_D13_BOUNDARY: D95.13`
- `D95_OE0_BOUNDARY: D95.1`
- `D95_OE1_BOUNDARY: D95.15`
- `D95_Q0_BOUNDARY: D95.7`
- `D95_Q1_BOUNDARY: D95.9`
- `D96_CLK1_BOUNDARY: D96.3`
- `D96_CLK2_BOUNDARY: D96.11`
- `D96_CLR1_BOUNDARY: D96.1`
- `D96_CLR2_BOUNDARY: D96.13`
- `D96_D1_BOUNDARY: D96.2`
- `D96_D2_BOUNDARY: D96.12`
- `D96_PRE1_BOUNDARY: D96.4`
- `D96_PRE2_BOUNDARY: D96.10`
- `D96_Q1N_BOUNDARY: D96.6`
- `D96_Q1_BOUNDARY: D96.5`
- `D96_Q2_BOUNDARY: D96.9`
- `D96_Q2_N_TEST_LANDING: D96.8`
- `D97_A1N_BOUNDARY: D97.1`
- `D97_A2N_BOUNDARY: D97.9`
- `D97_B1_BOUNDARY: D97.2`
- `D97_B2_BOUNDARY: D97.10`
- `D97_C1_BOUNDARY: D97.14`
- `D97_C2_BOUNDARY: D97.6`
- `D97_CLR1_BOUNDARY: D97.3`
- `D97_CLR2_BOUNDARY: D97.11`
- `D97_Q1N_BOUNDARY: D97.4`
- `D97_Q1_BOUNDARY: D97.13`
- `D97_Q2N_BOUNDARY: D97.12`
- `D97_Q2_BOUNDARY: D97.5`
- `D97_RC1_BOUNDARY: D97.15`
- `D97_RC2_BOUNDARY: D97.7`
- `D98_A1_BOUNDARY: D98.2`
- `D98_A2_BOUNDARY: D98.4`
- `D98_A3_BOUNDARY: D98.6`
- `D98_A4_BOUNDARY: D98.10`
- `D98_A5_BOUNDARY: D98.12`
- `D98_A6_BOUNDARY: D98.14`
- `D98_OE14_BOUNDARY: D98.1`
- `D98_OE56_BOUNDARY: D98.15`
- `D98_Y1_R94: D98.3`
- `D98_Y1_R94: R94.1`
- `D98_Y2_BOUNDARY: D98.5`
- `D98_Y3_S1_2: D98.7`
- `D98_Y4_BOUNDARY: D98.9`
- `D98_Y5_BOUNDARY: D98.11`
- `D98_Y6_BOUNDARY: D98.13`
- `D99_A1N_BOUNDARY: D99.1`
- `D99_A2N_BOUNDARY: D99.9`
- `D99_B2_BOUNDARY: D99.10`
- `D99_B_TEST_LANDING: D99.2`
- `D99_C1_BOUNDARY: D99.14`
- `D99_C2_BOUNDARY: D99.6`
- `D99_CLR2_BOUNDARY: D99.11`
- `D99_Q1N_BOUNDARY: D99.4`
- `D99_Q1_BOUNDARY: D99.13`
- `D99_Q2N_BOUNDARY: D99.12`
- `D99_Q2_BOUNDARY: D99.5`
- `D99_RC1_BOUNDARY: D99.15`
- `D99_RC2_BOUNDARY: D99.7`
- `FDC_CS_N: D94.2`
- `FDC_DDEN: D28.9`
- `FDC_RCLK: D106.7`
- `FDC_RCLK: D93.26`
- `FDC_RE_N: D94.1`
- `FDC_WE_N: D94.3`
- `GND: R30.2`
- `GND: D43.1`
- `GND: D39.2`
- `GND: D38.2`
- `GND: A62.1`
- `GND: D34.5`
- `GND: R33.2`
- `GND: C6.2`
- `GND: D41.2`
- `GND: D41.3`
- `GND: D41.4`
- `GND: D41.5`
- `GND: D99.3`
- `HOR_RTR: D54.13`
- `INHIB_STATUS_BOUNDARY: D7.5`
- `INHIB_STATUS_BOUNDARY: D29.3`
- `IOM_STATUS: D7.8`
- `IORD: D7.9`
- `IOWR: D7.10`
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
- `LATCH_SIG: D33.12`
- `LATCH_SIG: D39.9`
- `M12V: A59.1`
- `MA6: E1.3`
- `MEMR: D29.6`
- `MEMW: D29.1`
- `MEMW: D7.4`
- `MEM_MODE0: D28.11`
- `MEM_MODE1: D28.13`
- `OSC: C73.2`
- `OSC_FB: D59.9`
- `OSC_FB: R31.1`
- `OSC_FB: R32.1`
- `OSC_FB: Z1.1`
- `OSC_PRE: D59.8`
- `OSC_PRE: D59.1`
- `OSC_PRE: R31.2`
- `P12V: A60.1`
- `P12V: R66.1`
- `P5V: D10.16`
- `P5V: A61.1`
- `P5V: D40.7`
- `P5V: D40.10`
- `P5V: D41.1`
- `P5V: D41.8`
- `P5V: R34.1`
- `P5V: D34.13`
- `P5V: D57.11`
- `P5V: R104.2`
- `P5V: A54.1`
- `P5V: A53.1`
- `POF: D35.3`
- `PST_CLK: R32.2`
- `R100_1_BOUNDARY: R100.1`
- `R100_2_BOUNDARY: R100.2`
- `R102_1_BOUNDARY: R102.1`
- `R102_2_BOUNDARY: R102.2`
- `R108_1_BOUNDARY: R108.1`
- `R108_2_BOUNDARY: R108.2`
- `R86_1_BOUNDARY: R86.1`
- `R86_2_BOUNDARY: R86.2`
- `R92_1_BOUNDARY: R92.1`
- `R92_2_BOUNDARY: R92.2`
- `R94_P2_BOUNDARY: R94.2`
- `R99_1_BOUNDARY: R99.1`
- `R99_2_BOUNDARY: R99.2`
- `RESET: D13.6`
- `RESET: D11.21`
- `RES_RC: A17.1`
- `S3_3: D46.15`
- `S3_4: D46.1`
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
- `TAPE_RUN_INT: D10.22`
- `TIMING_TAG17: D36.2`
- `TIMING_TAG17: D41.6`
- `TIMING_TAG2: D38.4`
- `USART_RXRDY_IRQ: D10.20`
- `USART_RXRDY_IRQ: D11.14`
- `USART_TXRDY_IRQ: D10.21`
- `USART_TXRDY_IRQ: D11.15`
- `VERT_SYNC: D55.17`
- `VID_MUX_G: E14.1`
- `W10_QA_SEL: D51.1`
- `WREQ_N: X1.107C`
- `X3_HARNESS_1: A21.1`
- `X3_HARNESS_1: R104.1`
- `X3_HARNESS_7: A27.1`
- `X3_HARNESS_8: A28.1`
- `X4_06_BOUNDARY: AX406.1`
- `X4_07_BOUNDARY: AX407.1`
- `X4_08_BOUNDARY: AX408.1`
- `X4_09_BOUNDARY: AX409.1`
- `X4_10_BOUNDARY: AX410.1`
- `X4_11_BOUNDARY: AX411.1`
- `X4_12_BOUNDARY: AX412.1`
- `X4_13_BOUNDARY: AX413.1`
- `X4_14_BOUNDARY: AX414.1`
- `X4_15_BOUNDARY: AX415.1`
- `X4_16_BOUNDARY: AX416.1`
- `X4_17_BOUNDARY: AX417.1`
- `X4_18_BOUNDARY: AX418.1`
- `X4_19_BOUNDARY: AX419.1`
- `X4_20_BOUNDARY: AX420.1`
- `X4_21_BOUNDARY: AX421.1`
- `X4_22_BOUNDARY: AX422.1`
- `X4_23_BOUNDARY: AX423.1`
- `X4_FF_N: D28.8`
- `X4_FF_N: AX401.1`
- `X4_PLAY_N: D28.12`
- `X4_PLAY_N: AX403.1`
- `X4_REC_N: D28.10`
- `X4_REC_N: AX402.1`
- `X4_RN_N: D28.4`
- `X4_RN_N: AX404.1`
- `X4_STOP_N: D28.2`
- `X4_STOP_N: AX405.1`
- `XTAL16M: D39.10`
- `XTAL_TRIM: Z1.2`
- `XTAL_TRIM: C73.1`

Mismatched endpoints in `kicad/juku_routed.kicad_pcb`:
- D29.15: `MRC_N` != `AMWC_N`
- D29.5: `MEMR` != `AMW_N`
- D107.19: `BA7` != `BA0`
- D107.18: `BA6` != `BA1`
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
- D26.12: `D26_PC5_TAG4` != `D26_PC5_RN_IN`
- D26.11: `D26_PC6_TAG5` != `D26_PC6_STOP_IN`
- R5.2: `READY_PRE_N` != `D30B_D_PRE_N`
- D56.4: `D56_QN` != `D56_QN_D34`
- D6.11: `RAM_SEL` != `D6_MEM_SELECT_N`
- D6.12: `ROM_SEL` != `D6_MEM_SELECT_N`
- D8.15: `ROM_SEL` != `D6_MEM_SELECT_N`
- R11.2: `ROM_SEL` != `D6_MEM_SELECT_N`
- D92.5: `RAM_SEL` != `D6_MEM_SELECT_N`
- R12.2: `RAM_SEL` != `D6_MEM_SELECT_N`
- D94.10: `BA11` != `D94_A0_BOUNDARY`
- D94.11: `BA12` != `D94_A1_BOUNDARY`
- D94.12: `BA13` != `D94_A2_BOUNDARY`
- D94.13: `BA14` != `D94_A3_BOUNDARY`
- D94.14: `BA15` != `D94_A4_BOUNDARY`
- D105.9: `D2_WAIT_RAW` != `DBIN`
- D105.6: `D105_WAIT_PREINV` != `DBIN_GATED`
- D5.4: `DBIN` != `DBIN_GATED`
- D93.3: `CS_FDC` != `FDC_CS_N`
- D93.4: `IORD` != `FDC_RE_N`
- D93.2: `IOWR` != `FDC_WE_N`
- D29.17: `IOM_N` != `INHIB_N`
- D3.2: `IR6` != `INT6_BUF`
- D29.16: `MWC_N` != `IOM_N`
- D29.4: `MEMW` != `IOM_STATUS`
- D29.12: `IOWC_N` != `IORC_N`
- D2.2: `XACK_N` != `IORC_N`
- D29.8: `IOWR` != `IORD`
- D29.13: `IORC_N` != `IOWC_N`
- D29.7: `IORD` != `IOWR`
- D105.12: `MEMR` != `MEMW`
- D105.13: `MEMR` != `MEMW`
- D29.14: `AMWC_N` != `MRC_N`
- D29.19: `INHIB_N` != `MWC_N`
- D26.10: `D26_PC7_TAG6` != `POF`
- D7.13: `IORD` != `PROM_EN`
- R67.2: `SND_MIX` != `R67_2_BOUNDARY`
- D2.12: `D2_WAIT_RAW` != `READY_D`
- D45.10: `GND` != `S3_1`
- D45.9: `GND` != `S3_2`
- D46.10: `S3_1` != `S3_5`
- D46.9: `S3_2` != `S3_6`
- D12.1: `SER_TXD` != `SER_TXD_INV`
- D7.12: `IOWR` != `SYNC`
- X6.1: `HF_OUT` != `X6_1_BOUNDARY`

## Checklist

| Net | Category | Endpoints | Source risk | Bring-up action |
| --- | --- | --- | --- | --- |
| `C10_1_BOUNDARY` | video/analog | `C10.1` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C10_2_BOUNDARY` | video/analog | `C10.2` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 VT4-base assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C11_1_BOUNDARY` | video/analog | `C11.1` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C11_2_BOUNDARY` | video/analog | `C11.2` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF tank assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C12_1_BOUNDARY` | video/analog | `C12.1` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C12_2_BOUNDARY` | video/analog | `C12.2` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C15_1_BOUNDARY` | video/analog | `C15.1` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-collector assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C15_2_BOUNDARY` | video/analog | `C15.2` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-emitter assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C16_1_BOUNDARY` | logic | `C16.1` | .009 factory identity plus registered owner component/solder views prove C16 lead 1 on the horizontal 12.5 mm span between the FDC IC rows; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C16_2_BOUNDARY` | logic | `C16.2` | .009 factory identity plus registered owner component/solder views prove C16 lead 2 on the horizontal 12.5 mm span between the FDC IC rows; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C19_1_BOUNDARY` | logic | `C19.1` | .009 factory identity plus registered owner component/solder views prove C19 lead 1 on the vertical 10 mm span immediately right of D99; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C19_2_BOUNDARY` | logic | `C19.2` | .009 factory identity plus registered owner component/solder views prove C19 lead 2 on the vertical 10 mm span immediately right of D99; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C20_1_BOUNDARY` | logic | `C20.1` | .009 factory identity plus registered owner component/solder views prove C20 pad 1 on the first 10 mm vertical drill span right of D102; the remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C20_2_BOUNDARY` | logic | `C20.2` | .009 factory identity plus registered owner component/solder views prove C20 pad 2 on the first 10 mm vertical drill span right of D102; the remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C22_1_BOUNDARY` | logic | `C22.1` | .009 factory identity plus registered owner component/solder views prove C22 pad 1 on the second 10 mm vertical drill span right of D102; the remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C22_2_BOUNDARY` | logic | `C22.2` | .009 factory identity plus registered owner component/solder views prove C22 pad 2 on the second 10 mm vertical drill span right of D102; the remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C94_1_BOUNDARY` | video/analog | `C94.1` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 1 remains an explicit continuity boundary... | Scope/capture video or timing node during video bring-up. |
| `C94_2_BOUNDARY` | video/analog | `C94.2` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 2 remains an explicit continuity boundary... | Scope/capture video or timing node during video bring-up. |
| `C99_FAR` | logic | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity boundary because an RC deg... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `C9_1_BOUNDARY` | video/analog | `C9.1` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF ground assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `C9_2_BOUNDARY` | video/analog | `C9.2` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded | Scope/capture video or timing node during video bring-up. |
| `CPU_WAIT_STATUS` | logic | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `CS_FDC` | logic | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 remains the physical... | Cross-check against hardware when the peripheral path is exercised. |
| `D100_OE_BOUNDARY` | logic | `D100.9` | July-2026 two-sided local-package registration identifies D100 OE_N pin9; component copper ends at an isolated circular landing and the projected backside point is bare substrat... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D100_T_BOUNDARY` | logic | `D100.11` | July-2026 two-sided local-package registration identifies D100 direction pin11; its component-side continuation is obscured by the factory wire/tape bundle, so the remote contro... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_A0_BOUNDARY` | logic | `D101.14` | July-2026 validated component and solder package fits identify D101 К555КП12 pin14 A0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_A1_BOUNDARY` | logic | `D101.2` | July-2026 validated component and solder package fits identify D101 К555КП12 pin2 A1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D00_BOUNDARY` | logic | `D101.6` | July-2026 validated component and solder package fits identify D101 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D01_BOUNDARY` | logic | `D101.5` | July-2026 validated component and solder package fits identify D101 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D02_BOUNDARY` | logic | `D101.4` | July-2026 validated component and solder package fits identify D101 К555КП12 pin4 D02; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D03_BOUNDARY` | logic | `D101.3` | July-2026 validated component and solder package fits identify D101 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D10_BOUNDARY` | logic | `D101.10` | July-2026 validated component and solder package fits identify D101 К555КП12 pin10 D10; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D11_BOUNDARY` | logic | `D101.11` | July-2026 validated component and solder package fits identify D101 К555КП12 pin11 D11; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D12_BOUNDARY` | logic | `D101.12` | July-2026 validated component and solder package fits identify D101 К555КП12 pin12 D12; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_D13_BOUNDARY` | logic | `D101.13` | July-2026 validated component and solder package fits identify D101 К555КП12 pin13 D13; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_OE0_BOUNDARY` | logic | `D101.1` | July-2026 validated component and solder package fits identify D101 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_OE1_BOUNDARY` | logic | `D101.15` | July-2026 validated component and solder package fits identify D101 К555КП12 pin15 OE1_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_Q0_BOUNDARY` | logic | `D101.7` | July-2026 validated component and solder package fits identify D101 К555КП12 pin7 Q0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D101_Q1_BOUNDARY` | logic | `D101.9` | July-2026 validated component and solder package fits identify D101 К555КП12 pin9 Q1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_A1N_BOUNDARY` | logic | `D102.1` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_A2N_BOUNDARY` | logic | `D102.9` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_B1_BOUNDARY` | logic | `D102.2` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin2 B; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_B2_BOUNDARY` | logic | `D102.10` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_C1_BOUNDARY` | logic | `D102.14` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_C2_BOUNDARY` | logic | `D102.6` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_CLR1_BOUNDARY` | logic | `D102.3` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin3 CLR_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_CLR2_BOUNDARY` | logic | `D102.11` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_Q1N_BOUNDARY` | logic | `D102.4` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_Q1_BOUNDARY` | logic | `D102.13` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_Q2N_BOUNDARY` | logic | `D102.12` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_Q2_BOUNDARY` | logic | `D102.5` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_RC1_BOUNDARY` | logic | `D102.15` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D102_RC2_BOUNDARY` | logic | `D102.7` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D105_GATE1_Y` | logic | `D105.3` | traced sheet-1: D105 gate pins 1,2 -> 3; output destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_BO_BOUNDARY` | logic | `D106.13` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin13 BO; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_CLR_BOUNDARY` | logic | `D106.14` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin14 CLR; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_CO_BOUNDARY` | logic | `D106.12` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin12 CO; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D0_BOUNDARY` | logic | `D106.15` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin15 D0; calibrated raw-crop review finds only local copper into a nearby handoff, with no uninterrupted pat... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D1_BOUNDARY` | logic | `D106.1` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin1 D1; calibrated raw-crop review finds only local copper into a nearby handoff, with no uninterrupted path... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D2_BOUNDARY` | logic | `D106.10` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin10 D2 while the solder end projects beneath crossing rail metal; that apparent overlap is not continuity to GND, so... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D3_BOUNDARY` | logic | `D106.9` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin9 D3 while the solder end projects beneath crossing rail metal; that apparent overlap is not continuity to GND, so t... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_DOWN_BOUNDARY` | logic | `D106.4` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin4 DOWN and its local copper departure; the path does not remain visibly unbroken to an identified clock so... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_LOAD_BOUNDARY` | logic | `D106.11` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin11 LOAD_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q0_BOUNDARY` | logic | `D106.3` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin3 Q0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q1_BOUNDARY` | logic | `D106.2` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin2 Q1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q2_BOUNDARY` | logic | `D106.6` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin6 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_UP_BOUNDARY` | logic | `D106.5` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin5 UP; calibrated raw-crop review finds only local copper, with no uninterrupted path to a known P5V anchor... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D13_I3_BOUNDARY` | logic | `D13.3` | sheet-1 full-resolution: D13 ТЛ2 input pin3 drives the proved pin4 conductor to D105.2 and D11.20, but the pin3 origin is unread and remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D14_I2_BOUNDARY` | video/analog | `D14.2` | sheet-1 full-resolution К170АП2 package census identifies D14 input pin2; its remote serial-interface source is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D14_O7_BOUNDARY` | video/analog | `D14.7` | sheet-1 full-resolution К170АП2 package census identifies D14 output pin7; its remote serial-interface destination is unread and remains a measurement boundary | Scope/capture video or timing node during video bring-up. |
| `D25_T` | memory/decode | `D7.6, D25.11` | traced sheet-1 native 5150x3603 review: D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; pin4 drops past the D29.3 rail with... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D26_PA6_PREN_BOUNDARY` | logic | `D26.38` | sheet-1 full-resolution: D26 PA6 pin38 leaves on the conductor labeled PREN with off-sheet marker (3); the far destination is unread, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PB4_BOUNDARY` | logic | `D26.22` | sheet-1 full-resolution: D26 PB4 pin22 enters the E8 CONTRDAT selector region, but the absent switch symbol prevents a proved remote endpoint, so this remains a measurement boun... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC0_BOUNDARY` | memory/decode | `D26.14` | sheet-1 full-resolution: D26 PC0 pin14 leaves the PPI into the cassette-control gate region, but its unique next hop is not established and remains a measurement boundary | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D26_PC1_BOUNDARY` | memory/decode | `D26.15` | sheet-1 full-resolution: D26 PC1 pin15 leaves the PPI into the cassette-control gate region, but its unique next hop is not established and remains a measurement boundary | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D26_PC5_RN_IN` | logic | `D26.12, D28.3` | cross-source closure: .006 sheet-1 draws the uninterrupted D26 PC5/pin12 mode conductor into D28 К155ЛН3 input pin3, whose paired open-collector output pin4 is labeled -RN/X4.4;... | Cross-check against hardware when the peripheral path is exercised. |
| `D26_PC6_STOP_IN` | logic | `D26.11, D28.1` | cross-source closure: .006 sheet-1 draws the uninterrupted D26 PC6/pin11 mode conductor into D28 К155ЛН3 input pin1, whose paired open-collector output pin2 is labeled -STOP/X4.... | Cross-check against hardware when the peripheral path is exercised. |
| `D29_AIN1_BOUNDARY` | logic | `D29.2` | sheet-1 native 5150x3603 command-buffer chase identifies semantic command A1/CCLCK on D29 physical A1 pin2; its westbound conductor enters the dense D5/D105 crossing bundle, whe... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D30_CLK2_BOUNDARY` | timing/I/O | `D30.11` | sheet-1 full-resolution: D30 second flip-flop clock pin11 has a drawn conductor whose unique source is unread, so it remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D30_Q2N_BOUNDARY` | logic | `D30.8` | sheet-1 full-resolution: D30 second flip-flop inverted output pin8 has a drawn conductor whose unique destination is unread, so it remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_A1_TAG2` | logic | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in that boundary domai... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D56_Q2N_TAG16` | memory/decode | `D56.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D56 second-section Q2_N pin12 leaves east on conductor code 16; the former D34.10 merge is disproved by the distinct... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D58_STB_TAG5` | logic | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled... | Bench-check waveform/current path with speaker disconnected first. |
| `D6_MEM_SELECT_N` | memory/decode | `D6.11, D6.12, D8.15, R11.2, D92.5, R12.2, ... (+1)` | owner continuity 2026-07-13 joins D6.11, D6.12, and D13.12 on the physical .009 board, superseding the older-sheet independent RAM_SEL/ROM_SEL interpretation; existing R11/R12,... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D6_V_ENABLE` | logic | `D6.13, D6.14` | sheet-1 full-resolution: D6 РТ4 enable pins V1/pin13 and V2/pin14 are visibly bridged; upstream conductor origin remains unread and the former D7.11 merge is refuted | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D93_CLK_BOUNDARY` | FDC | `D93.24` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin24 CLK; the candidate D106 divider relation is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_DIRC_BOUNDARY` | FDC | `D93.16` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin16 DIRC; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_EARLY_BOUNDARY` | FDC | `D93.17` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin17 EARLY; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_HLD_BOUNDARY` | FDC | `D93.28` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin28 HLD; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_HLT_BOUNDARY` | FDC | `D93.23` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin23 HLT; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_INDEX_BOUNDARY` | FDC | `D93.35` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin35 INDEX; remote drive-status continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_LATE_BOUNDARY` | FDC | `D93.18` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin18 LATE; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_MR_BOUNDARY` | FDC | `D93.19` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin19 MR_N; remote reset continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_RAW_READ_BOUNDARY` | FDC | `D93.27` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin27 RAW_READ; remote separator continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_READY_BOUNDARY` | FDC | `D93.32` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin32 READY; remote drive-status continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_RG_BOUNDARY` | FDC | `D93.25` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin25 RG; remote separator continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_STEP_BOUNDARY` | FDC | `D93.15` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin15 STEP; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_TEST_BOUNDARY` | FDC | `D93.22` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin22 TEST; remote strap continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_TG43_BOUNDARY` | FDC | `D93.29` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin29 TG43; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_TR00_BOUNDARY` | FDC | `D93.34` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin34 TR00; remote drive-status continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_VDD12_BOUNDARY` | FDC | `D93.40` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin40 VDD_12V; the +12V feed is not proved and remains a power-safety measurement boundary that must n... | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_WDATA_BOUNDARY` | FDC | `D93.31` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin31 WDATA; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_WF_VFOE_BOUNDARY` | FDC | `D93.33` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin33 WF_VFOE; remote drive/separator continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_WG_BOUNDARY` | FDC | `D93.30` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin30 WG; remote drive-interface continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D93_WPRT_BOUNDARY` | FDC | `D93.36` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin36 WPRT; remote drive-status continuity is not proved, so this remains a measurement boundary | Continuity-check the physical КР1818ВГ93 socket path before drive bring-up. |
| `D94_A0_BOUNDARY` | logic | `D94.10` | D94 .009 input continuity boundary: the retired BA11 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_A1_BOUNDARY` | logic | `D94.11` | D94 .009 input continuity boundary: the retired BA12 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_A2_BOUNDARY` | logic | `D94.12` | D94 .009 input continuity boundary: the retired BA13 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_A3_BOUNDARY` | logic | `D94.13` | D94 .009 input continuity boundary: the retired BA14 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_A4_BOUNDARY` | logic | `D94.14` | D94 .009 input continuity boundary: the retired BA15 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D3` | logic | `D94.4` | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) mm; far-side destinat... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D4` | logic | `D94.5` | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D5` | logic | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D6` | logic | `D94.7` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because its two-sided projec... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_D7` | logic | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D94_EN_BOUNDARY` | logic | `D94.15` | July-2026 registered component/solder local fits identify D94 enable pin 15 and exposed fanout, but the onward source cannot be uniquely followed across the adjacent tile | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_A0_BOUNDARY` | logic | `D95.14` | July-2026 validated component and solder package fits identify D95 К555КП12 pin14 A0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_A1_BOUNDARY` | logic | `D95.2` | July-2026 validated component and solder package fits identify D95 К555КП12 pin2 A1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D00_BOUNDARY` | logic | `D95.6` | July-2026 validated component and solder package fits identify D95 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D01_BOUNDARY` | logic | `D95.5` | July-2026 validated component and solder package fits identify D95 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D02_BOUNDARY` | logic | `D95.4` | July-2026 validated component and solder package fits identify D95 К555КП12 pin4 D02; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D03_BOUNDARY` | logic | `D95.3` | July-2026 validated component and solder package fits identify D95 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D10_BOUNDARY` | logic | `D95.10` | July-2026 validated component and solder package fits identify D95 К555КП12 pin10 D10; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D11_BOUNDARY` | logic | `D95.11` | July-2026 validated component and solder package fits identify D95 К555КП12 pin11 D11; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D12_BOUNDARY` | logic | `D95.12` | July-2026 validated component and solder package fits identify D95 К555КП12 pin12 D12; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_D13_BOUNDARY` | logic | `D95.13` | July-2026 validated component and solder package fits identify D95 К555КП12 pin13 D13; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_OE0_BOUNDARY` | logic | `D95.1` | July-2026 validated component and solder package fits identify D95 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_OE1_BOUNDARY` | logic | `D95.15` | July-2026 validated component and solder package fits identify D95 К555КП12 pin15 OE1_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_Q0_BOUNDARY` | logic | `D95.7` | July-2026 validated component and solder package fits identify D95 К555КП12 pin7 Q0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D95_Q1_BOUNDARY` | logic | `D95.9` | July-2026 validated component and solder package fits identify D95 К555КП12 pin9 Q1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_CLK1_BOUNDARY` | timing/I/O | `D96.3` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin3 CLK1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_CLK2_BOUNDARY` | timing/I/O | `D96.11` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin11 CLK2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_CLR1_BOUNDARY` | logic | `D96.1` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin1 CLR1_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_CLR2_BOUNDARY` | logic | `D96.13` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin13 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_D1_BOUNDARY` | logic | `D96.2` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin2 D1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_D2_BOUNDARY` | logic | `D96.12` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin12 D2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_PRE1_BOUNDARY` | logic | `D96.4` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin4 PRE1_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_PRE2_BOUNDARY` | logic | `D96.10` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin10 PRE2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_Q1N_BOUNDARY` | logic | `D96.6` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin6 Q1_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_Q1_BOUNDARY` | logic | `D96.5` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin5 Q1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D96_Q2_BOUNDARY` | logic | `D96.9` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin9 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_A1N_BOUNDARY` | logic | `D97.1` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_A2N_BOUNDARY` | logic | `D97.9` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_B1_BOUNDARY` | logic | `D97.2` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin2 B; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_B2_BOUNDARY` | logic | `D97.10` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_C1_BOUNDARY` | logic | `D97.14` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_C2_BOUNDARY` | logic | `D97.6` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_CLR1_BOUNDARY` | logic | `D97.3` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin3 CLR_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_CLR2_BOUNDARY` | logic | `D97.11` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_Q1N_BOUNDARY` | logic | `D97.4` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_Q1_BOUNDARY` | logic | `D97.13` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_Q2N_BOUNDARY` | logic | `D97.12` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_Q2_BOUNDARY` | logic | `D97.5` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_RC1_BOUNDARY` | logic | `D97.15` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D97_RC2_BOUNDARY` | logic | `D97.7` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A1_BOUNDARY` | logic | `D98.2` | July-2026 validated package registration identifies D98 К155ЛП11 pin2 A1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A2_BOUNDARY` | logic | `D98.4` | July-2026 validated package registration identifies D98 К155ЛП11 pin4 A2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A3_BOUNDARY` | logic | `D98.6` | July-2026 validated package registration identifies D98 К155ЛП11 pin6 A3; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A4_BOUNDARY` | logic | `D98.10` | July-2026 validated package registration identifies D98 К155ЛП11 pin10 A4; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A5_BOUNDARY` | logic | `D98.12` | July-2026 validated package registration identifies D98 К155ЛП11 pin12 A5; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_A6_BOUNDARY` | logic | `D98.14` | July-2026 validated package registration identifies D98 К155ЛП11 pin14 A6; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_OE14_BOUNDARY` | logic | `D98.1` | July-2026 validated package registration identifies D98 К155ЛП11 pin1 OE14_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_OE56_BOUNDARY` | logic | `D98.15` | July-2026 validated package registration identifies D98 К155ЛП11 pin15 OE56_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_Y2_BOUNDARY` | logic | `D98.5` | July-2026 validated package registration identifies D98 К155ЛП11 pin5 Y2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_Y4_BOUNDARY` | logic | `D98.9` | July-2026 validated package registration identifies D98 К155ЛП11 pin9 Y4; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_Y5_BOUNDARY` | logic | `D98.11` | July-2026 validated package registration identifies D98 К155ЛП11 pin11 Y5; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D98_Y6_BOUNDARY` | logic | `D98.13` | July-2026 validated package registration identifies D98 К155ЛП11 pin13 Y6; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_A1N_BOUNDARY` | logic | `D99.1` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_A2N_BOUNDARY` | logic | `D99.9` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_B2_BOUNDARY` | logic | `D99.10` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_C1_BOUNDARY` | logic | `D99.14` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_C2_BOUNDARY` | logic | `D99.6` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_CLR2_BOUNDARY` | logic | `D99.11` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q1N_BOUNDARY` | logic | `D99.4` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q1_BOUNDARY` | logic | `D99.13` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2N_BOUNDARY` | logic | `D99.12` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_Q2_BOUNDARY` | logic | `D99.5` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_RC1_BOUNDARY` | logic | `D99.15` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D99_RC2_BOUNDARY` | logic | `D99.7` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `FDC_DDEN` | FDC | `D26.13, D93.37, D6.15, D28.9` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15 and directly into D28 input pin9, whose paired open-collector output pin8 is labeled -FF/X4.1; .009/MAME P... | Confirm density-control level against drive/emulator behavior. |
| `FDC_DRQ` | FDC | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FDC_INTRQ` | FDC | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FRAME_INT` | timing/I/O | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (D55.OUT1 export, cro... | Cross-check against hardware when the peripheral path is exercised. |
| `INHIB_STATUS_BOUNDARY` | logic | `D7.5, D29.3` | sheet-1 native 5150x3603 direct-junction chase: D7 data-turnaround NAND input pin5 and semantic D29 command A0 on physical package channel A2/pin3 meet at an explicit junction d... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `MEM_MODE0` | memory/decode | `D26.16, D6.2, D28.11` | traced sheet-1 full-resolution: D26 PC2/pin16 -> mode-bundle tag1 -> D6 A5/pin2 and directly into D28 input pin11, whose paired open-collector output pin10 is labeled -REC/X4.2;... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `MEM_MODE1` | memory/decode | `D26.17, D6.1, D28.13` | traced sheet-1 full-resolution: D26 PC3/pin17 -> mode-bundle tag2 -> D6 A6/pin1 and directly into D28 input pin13, whose paired open-collector output pin12 is labeled -PLAY/X4.3... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `PHI2TTL` | logic | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_T) + "(1)" exit to s... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PIT_BAUD` | timing/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V (power corner) | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `POF` | logic | `D26.10, D35.3` | cross-sheet source closure: sheet-1 D26 PPI0 PC7/pin10 leaves through mode-bundle tag6; sheet-2 labels the receiving conductor POF directly into D35 inverter input pin3; the pin... | Cross-check against hardware when the peripheral path is exercised. |
| `PROM_EN` | video/analog | `D7.11, D7.13, R17.2` | traced sheet-1 native 5150x3603 direct-junction review: D7 section 12,13->11 is a SYNC-gated feedback strobe; pin13 loops directly onto output pin11, and that shared node runs e... | Scope/capture video or timing node during video bring-up. |
| `R100_1_BOUNDARY` | logic | `R100.1` | .009 factory drawing plus owner photo prove the upper R100 body in the right-edge FDC column; pin 1 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R100_2_BOUNDARY` | logic | `R100.2` | .009 factory drawing plus owner photo prove the upper R100 body in the right-edge FDC column; pin 2 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R102_1_BOUNDARY` | logic | `R102.1` | .009 factory drawing plus owner photo prove the second R102 body in the right-edge FDC column; pin 1 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R102_2_BOUNDARY` | logic | `R102.2` | .009 factory drawing plus owner photo prove the second R102 body in the right-edge FDC column; pin 2 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R108_1_BOUNDARY` | logic | `R108.1` | .009 factory drawing plus owner photo prove the third R108 body in the right-edge FDC column; pin 1 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R108_2_BOUNDARY` | logic | `R108.2` | .009 factory drawing plus owner photo prove the third R108 body in the right-edge FDC column; pin 2 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded; target endpoint requires continuity | Scope/capture video or timing node during video bring-up. |
| `R86_1_BOUNDARY` | logic | `R86.1` | .009 factory drawing plus owner photo prove the lowest R86 body in the right-edge FDC column; pin 1 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R86_2_BOUNDARY` | logic | `R86.2` | .009 factory drawing plus owner photo prove the lowest R86 body in the right-edge FDC column; pin 2 destination remains a continuity boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R92_1_BOUNDARY` | logic | `R92.1` | .009 factory identity plus registered owner component/solder views prove R92 lead 1 on the upper/right 10.16 mm resistor span below D95; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R92_2_BOUNDARY` | logic | `R92.2` | .009 factory identity plus registered owner component/solder views prove R92 lead 2 on the upper/right 10.16 mm resistor span below D95; its remote destination is not readable | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R94_P2_BOUNDARY` | logic | `R94.2` | July-2026 registered component photo identifies the lower terminal of R94 220 ohm; only the upper terminal to D98.3 is proved and pin2 remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R99_1_BOUNDARY` | logic | `R99.1` | .009 factory identity plus registered owner component/solder views prove R99 lead 1 on the lower/left 10.16 mm resistor span below-left of D95; its remote destination is not rea... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `R99_2_BOUNDARY` | logic | `R99.2` | .009 factory identity plus registered owner component/solder views prove R99 lead 2 on the lower/left 10.16 mm resistor span below-left of D95; its remote destination is not rea... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `RAIL_E` | memory/decode | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members: DRAM pin 16 x32, b... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `READY_PRE_N` | video/analog | `D30.4` | D30 section-A asynchronous preset pin4 remains a target-board continuity boundary after owner measurements moved R5 to D30.10/.12 | Scope/capture video or timing node during video bring-up. |
| `REV` | logic | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder region enable (G2A_N+G... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `ROE` | memory/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merged factory wire W13... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `S1_3_BOUNDARY` | logic | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not identified, so it remains... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `SSTB_N` | logic | `D30.1` | sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TAPE_RUN_INT` | logic | `D10.22` | scan sheet-1: D10 IR4 pin 22 is explicitly labeled (3) TAPE RUN INT; sheet-3 source remains outside the modeled board boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TIMING_TAG2` | logic | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's same-number top-edg... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `USART_RXRDY_IRQ` | video/analog | `D10.20, D11.14` | traced sheet-1 native full-resolution: D11 RXRDY output pin14 runs east, turns north, and lands directly on D10 PIC IR2 pin20; pinned MAME primary-USART wiring independently agr... | Scope/capture video or timing node during video bring-up. |
| `USART_TXRDY_IRQ` | video/analog | `D10.21, D11.15` | traced sheet-1 native full-resolution: D11 TXRDY output pin15 runs east, turns north, and lands directly on D10 PIC IR3 pin21; pinned MAME primary-USART wiring independently agr... | Scope/capture video or timing node during video bring-up. |
| `V3_RC` | logic | `R17.1, C99.1, D9.6` | traced sheet-1 native 5150x3603 review: R17 top + C99 pin1/left plate + D9.6 share one junction; rail3 crosses above without a dot. RC-deglitched I/O strobe -> D9.G1. The visibl... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `VIDEO_OUT` | video/analog | `VT2.1, R65.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_emaplaat.pdf, board... | Scope/capture video or timing node during video bring-up. |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Scope/capture video or timing node during video bring-up. |
| `W_RAIL16` | memory/decode | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, ... (+27)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: the sim cannot reprodu... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `X4_06_BOUNDARY` | logic | `AX406.1, X4.6` | .009 sheets4-5 wire32: physical board landing А X4:6 maps directly to bracket X4.6; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_07_BOUNDARY` | logic | `AX407.1, X4.7` | .009 sheets4-5 wire33: physical board landing А X4:7 maps directly to bracket X4.7; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_08_BOUNDARY` | logic | `AX408.1, X4.8` | .009 sheets4-5 wire34: physical board landing А X4:8 maps directly to bracket X4.8; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_09_BOUNDARY` | logic | `AX409.1, X4.9` | .009 sheets4-5 wire35: physical board landing А X4:9 maps directly to bracket X4.9; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_10_BOUNDARY` | logic | `AX410.1, X4.10` | .009 sheets4-5 wire36: physical board landing А X4:10 maps directly to bracket X4.10; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_11_BOUNDARY` | logic | `AX411.1, X4.11` | .009 sheets4-5 wire37: physical board landing А X4:11 maps directly to bracket X4.11; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_12_BOUNDARY` | logic | `AX412.1, X4.12` | .009 sheets4-5 wire38: physical board landing А X4:12 maps directly to bracket X4.12; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_13_BOUNDARY` | logic | `AX413.1, X4.13` | .009 sheets4-5 wire39: physical board landing А X4:13 maps directly to bracket X4.13; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_14_BOUNDARY` | logic | `AX414.1, X4.14` | .009 sheets4-5 wire40: physical board landing А X4:14 maps directly to bracket X4.14; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_15_BOUNDARY` | logic | `AX415.1, X4.15` | .009 sheets4-5 wire41: physical board landing А X4:15 maps directly to bracket X4.15; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_16_BOUNDARY` | logic | `AX416.1, X4.16` | .009 sheets4-5 wire42: physical board landing А X4:16 maps directly to bracket X4.16; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_17_BOUNDARY` | logic | `AX417.1, X4.17` | .009 sheets4-5 wire43: physical board landing А X4:17 maps directly to bracket X4.17; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_18_BOUNDARY` | logic | `AX418.1, X4.18` | .009 sheets4-5 wire44: physical board landing А X4:18 maps directly to bracket X4.18; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_19_BOUNDARY` | logic | `AX419.1, X4.19` | .009 sheets4-5 wire45: physical board landing А X4:19 maps directly to bracket X4.19; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_20_BOUNDARY` | logic | `AX420.1, X4.20` | .009 sheets4-5 wire46: physical board landing А X4:20 maps directly to bracket X4.20; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_21_BOUNDARY` | logic | `AX421.1, X4.21` | .009 sheets4-5 wire47: physical board landing А X4:21 maps directly to bracket X4.21; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_22_BOUNDARY` | logic | `AX422.1, X4.22` | .009 sheets4-5 wire48: physical board landing А X4:22 maps directly to bracket X4.22; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_23_BOUNDARY` | logic | `AX423.1, X4.23` | .009 sheets4-5 wire49: physical board landing А X4:23 maps directly to bracket X4.23; circuit-side destination remains untraced | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `X4_FF_N` | logic | `D28.8, AX401.1, X4.1` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin8 -FF and sends it to X4.1; .009 sheets4-5 preserve a direct 23-conductor mapping from ph... | Prefer owner continuity check or board measurement before relying on it. |
| `X4_PLAY_N` | logic | `D28.12, AX403.1, X4.3` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin12 -PLAY and sends it to X4.3; .009 sheets4-5 preserve a direct 23-conductor mapping from... | Prefer owner continuity check or board measurement before relying on it. |
| `X4_REC_N` | logic | `D28.10, AX402.1, X4.2` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin10 -REC and sends it to X4.2; .009 sheets4-5 preserve a direct 23-conductor mapping from... | Prefer owner continuity check or board measurement before relying on it. |
| `X4_RN_N` | logic | `D28.4, AX404.1, X4.4` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin4 -RN and sends it to X4.4; .009 sheets4-5 preserve a direct 23-conductor mapping from ph... | Prefer owner continuity check or board measurement before relying on it. |
| `X4_STOP_N` | logic | `D28.2, AX405.1, X4.5` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin2 -STOP and sends it to X4.5; .009 sheets4-5 preserve a direct 23-conductor mapping from... | Prefer owner continuity check or board measurement before relying on it. |
| `XTAL16M` | video/analog | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate fr... | Scope/capture video or timing node during video bring-up. |

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
