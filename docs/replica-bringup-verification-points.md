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
- Verification-point nets: `167`
- Verification-point endpoints checked in PCB: `333`
- PCB endpoint coverage: `PASS`
- All board endpoints checked in source PCB: `2188`
- All board endpoints checked in routed PCB: `2188`
- Intentional off-board endpoints excluded: `34`
- Full PCB endpoint coverage: `FAIL`

| Category | Nets |
| --- | ---: |
| FDC | 3 |
| logic | 139 |
| memory/decode | 7 |
| sound/analog | 1 |
| timing/I/O | 7 |
| video/analog | 10 |

## KiCad PCB Endpoint Coverage

Every source-risk endpoint listed below is checked against the final
`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the
fabrication source preserves the same residual-risk connectivity as
`kicad/juku.board.json`; it does not prove the historical assumption
behind a risk note.

| Check | Result | Evidence |
| --- | --- | --- |
| Risk endpoints present on PCB pads | PASS | 333/333 matched a footprint pad net |
| Risk endpoint net names match board JSON | PASS | 333/333 net names matched |

## Full Board Endpoint Coverage

Every PCB-scoped `kicad/juku.board.json` endpoint is also checked against
the generated source PCB and the routed fabrication PCB. Bracket-mounted
`S1`, `X3`, `X8`, and `X9` are intentionally excluded because their cable
landings are separate `A*` PCB footprints. This is a
fabrication-source coverage gate, not a historical-source proof.

| PCB | Present | Matching net names | Result |
| --- | ---: | ---: | --- |
| `kicad/juku.kicad_pcb` | 2188/2188 | 2188/2188 | PASS |
| `kicad/juku_routed.kicad_pcb` | 1924/2188 | 1909/2188 | FAIL |

Missing endpoints in `kicad/juku_routed.kicad_pcb`:
- `A10: D2.1`
- `A12: D2.5`
- `A14: D2.3`
- `A15: D2.6`
- `A9: D2.7`
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
- `D106_Q3_BOUNDARY: D106.7`
- `D106_UP_BOUNDARY: D106.5`
- `D13_4_D105_2: D11.20`
- `D28_A1_BOUNDARY: D28.1`
- `D28_A2_BOUNDARY: D28.3`
- `D28_A3_BOUNDARY: D28.5`
- `D28_A4_BOUNDARY: D28.9`
- `D28_A5_BOUNDARY: D28.11`
- `D28_A6_BOUNDARY: D28.13`
- `D28_Y1_BOUNDARY: D28.2`
- `D28_Y2_BOUNDARY: D28.4`
- `D28_Y3_BOUNDARY: D28.6`
- `D28_Y4_BOUNDARY: D28.8`
- `D28_Y5_BOUNDARY: D28.10`
- `D28_Y6_BOUNDARY: D28.12`
- `D33_CLK_RC: R46.2`
- `D33_CLK_RC: C6.1`
- `D33_CLK_RC: D33.9`
- `D34_A1_TAG2: D34.4`
- `D34_RC_DRIVE: D34.6`
- `D34_RC_DRIVE: C5.1`
- `D34_RC_NODE: C5.2`
- `D34_RC_NODE: R33.1`
- `D34_RC_NODE: D34.2`
- `D36_B2_TAG17: D36.2`
- `D38_LOAD_I1: D38.1`
- `D38_LOAD_I2: D38.2`
- `D38_LOAD_I4: D38.4`
- `D38_LOAD_I5: D38.5`
- `D40QA: R46.1`
- `D40_CTRL_PULL: R34.2`
- `D40_CTRL_PULL: D40.1`
- `D40_CTRL_PULL: D40.9`
- `D41_CK_BOUNDARY: D41.9`
- `D41_LD_BOUNDARY: D41.6`
- `D56_Q2N_D34: D56.12`
- `D56_Q2N_D34: D34.10`
- `D56_Q2_D34: D56.5`
- `D56_Q2_D34: D34.9`
- `D58_STB_TAG5: D58.11`
- `D59_O10_TAG10: D59.10`
- `D6_V_ENABLE: D6.13`
- `D6_V_ENABLE: D6.14`
- `D7_A3_BOUNDARY: D7.4`
- `D7_B3_BOUNDARY: D7.5`
- `D7_Y2_BOUNDARY: D7.3`
- `D7_Y4_TAG8: D7.8`
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
- `D99_B_TEST_LANDING: D99.2`
- `FDC_CS_N: D94.2`
- `FDC_RE_N: D94.1`
- `FDC_WE_N: D94.3`
- `GND: R30.2`
- `GND: D43.1`
- `GND: A62.1`
- `GND: D34.5`
- `GND: R33.2`
- `GND: C6.2`
- `GND: D41.2`
- `GND: D41.3`
- `GND: D41.4`
- `GND: D41.5`
- `GND: R73.3`
- `GND: D99.3`
- `HOR_RTR: D54.13`
- `INT6_BUF: S4.3`
- `IORD: D7.9`
- `IOWR: D7.10`
- `IR6: S4.2`
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
- `PIC_IR2_BOUNDARY: D10.20`
- `PIC_IR3_BOUNDARY: D10.21`
- `POF: D35.3`
- `PST_CLK: R32.2`
- `RESET: D13.6`
- `RESET: D11.21`
- `RES_RC: A17.1`
- `RF_TAP: L1.3`
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
- `SHIFT_G: D42.8`
- `SHIFT_G: D43.8`
- `SYNDET_S4: D11.16`
- `SYNDET_S4: S4.1`
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
- `VERT_SYNC: D55.17`
- `VID_MUX_G: E14.1`
- `VT4_C: C12.2`
- `W10_QA_SEL: D51.1`
- `X3_HARNESS_1: A21.1`
- `X3_HARNESS_1: R104.1`
- `X3_HARNESS_7: A27.1`
- `X3_HARNESS_8: A28.1`
- `XTAL_TRIM: Z1.2`
- `XTAL_TRIM: C73.1`

Mismatched endpoints in `kicad/juku_routed.kicad_pcb`:
- D7.12: `IOWR` != `D7_A1_BOUNDARY`
- D7.13: `IORD` != `D7_B1_BOUNDARY`
- D93.3: `CS_FDC` != `FDC_CS_N`
- D93.4: `IORD` != `FDC_RE_N`
- D93.2: `IOWR` != `FDC_WE_N`
- D3.2: `IR6` != `INT6_BUF`
- R76.1: `RF_TANK` != `RF_TAP`
- D45.10: `GND` != `S3_1`
- D45.9: `GND` != `S3_2`
- D46.10: `S3_1` != `S3_5`
- D46.9: `S3_2` != `S3_6`
- D12.1: `SER_TXD` != `SER_TXD_INV`
- VT4.3: `RF_TANK` != `VT4_C`
- L1.2: `GND` != `VT4_C`
- C15.1: `RF_TANK` != `VT4_C`

## Checklist

| Net | Category | Endpoints | Source risk | Bring-up action |
| --- | --- | --- | --- | --- |
| `CPU_WAIT_STATUS` | logic | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `CS_FDC` | logic | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch | Cross-check against hardware when the peripheral path is exercised. |
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
| `D105_WAIT_PREINV` | logic | `D105.6` | traced sheet-1 .006: D105 pin 6 feeds D95 inverter pin 1, whose pin 2 is -WAIT/E8-1; .009 reassigns D95 to an FDC KP12, so the target-revision destination remains a boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_BO_BOUNDARY` | logic | `D106.13` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin13 BO; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_CLR_BOUNDARY` | logic | `D106.14` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin14 CLR; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_CO_BOUNDARY` | logic | `D106.12` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin12 CO; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D0_BOUNDARY` | logic | `D106.15` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin15 D0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D1_BOUNDARY` | logic | `D106.1` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin1 D1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D2_BOUNDARY` | logic | `D106.10` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin10 D2 while the solder end is rail-obscured; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_D3_BOUNDARY` | logic | `D106.9` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin9 D3 while the solder end is rail-obscured; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_DOWN_BOUNDARY` | logic | `D106.4` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin4 DOWN; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_LOAD_BOUNDARY` | logic | `D106.11` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin11 LOAD_N; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q0_BOUNDARY` | logic | `D106.3` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin3 Q0; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q1_BOUNDARY` | logic | `D106.2` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin2 Q1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q2_BOUNDARY` | logic | `D106.6` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin6 Q2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_Q3_BOUNDARY` | logic | `D106.7` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin7 Q3 while the solder end is rail-obscured; the candidate FDC clock relation is unproved, so this remains a measurem... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D106_UP_BOUNDARY` | logic | `D106.5` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin5 UP; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D25_T` | logic | `D7.6, D25.11` | traced sheet-1 300dpi (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; section inputs = next hop west [un... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC5_TAG4` | logic | `D26.12` | traced sheet-1 full-resolution: D26 PC5/pin12 exits as mode-bundle tag4; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC6_TAG5` | logic | `D26.11` | traced sheet-1 full-resolution: D26 PC6/pin11 exits as mode-bundle tag5; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D26_PC7_TAG6` | logic | `D26.10` | traced sheet-1 full-resolution: D26 PC7/pin10 exits as mode-bundle tag6; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A1_BOUNDARY` | logic | `D28.1` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin1 A1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A2_BOUNDARY` | logic | `D28.3` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin3 A2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A3_BOUNDARY` | logic | `D28.5` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin5 A3; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A4_BOUNDARY` | logic | `D28.9` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin9 A4; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A5_BOUNDARY` | logic | `D28.11` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin11 A5; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_A6_BOUNDARY` | logic | `D28.13` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin13 A6; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y1_BOUNDARY` | logic | `D28.2` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin2 Y1; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y2_BOUNDARY` | logic | `D28.4` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin4 Y2; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y3_BOUNDARY` | logic | `D28.6` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin6 Y3; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y4_BOUNDARY` | logic | `D28.8` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin8 Y4; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y5_BOUNDARY` | logic | `D28.10` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin10 Y5; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D28_Y6_BOUNDARY` | logic | `D28.12` | July-2026 validated component and reflected solder package fits identify D28 К155ЛН3 pin12 Y6; no remote destination is proved, so this remains a measurement boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D30B_D_PRE_N` | logic | `D30.10, D30.12` | traced sheet-1: D30 section-B /PRE2 pin 10 and D2 pin 12 are visibly tied by the local U-shaped wire; the shared upstream source remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D34_SIG` | video/analog | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out | Scope/capture video or timing node during video bring-up. |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out | Scope/capture video or timing node during video bring-up. |
| `D36_B2_TAG17` | logic | `D36.2` | scan sheet-2: D36 second NAND input pin 2 lands directly on numbered timing-bundle rail 17; unique remote driver not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D36_CAS_IN` | memory/decode | `D36.12, D36.13` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); tied NAND pair = CAS-driver input; west source line [pending] | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D39_MEMCYC` | memory/decode | `D39.3, D39.4` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); out3 also drives rail 4 [rail dests pending] | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D41_CK_BOUNDARY` | logic | `D41.9` | scan sheet-2: D41 clock input pin 9 leaves the package as its own timing-bundle conductor; unique remote driver not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D41_LD_BOUNDARY` | logic | `D41.6` | scan sheet-2: D41 load input pin 6 leaves the package as its own timing-bundle conductor; unique remote driver not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D56_QN` | timing/I/O | `D56.4` | traced sheet-2 (crop s2_dotclk_bend): D56.Q_N (pin 4) corners SOUTH at x~6074 — destination unread [chase]; the old "16MHz astable source" attribution retired | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D58_STB_TAG5` | logic | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D59_O10_TAG10` | logic | `D59.10` | scan sheet-2: D59 inverter output pin 10 descends continuously to the open-circle bundle marker 10; the unique same-number far continuation is not established | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D6_V_ENABLE` | logic | `D6.13, D6.14` | sheet-1 full-resolution: D6 РТ4 enable pins V1/pin13 and V2/pin14 are visibly bridged; upstream conductor origin remains unread and the former D7.11 merge is refuted | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D7_A1_BOUNDARY` | logic | `D7.12` | sheet-1 full-resolution: D7 first-gate pin12 has a drawn conductor, but its unique origin is not established after correcting the false IOWR assignment, so it remains a measurem... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D7_A3_BOUNDARY` | logic | `D7.4` | sheet-1 D7 section 5,4->6: pin4 leaves west as a distinct conductor; next hop is unread in the available scan | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D7_B1_BOUNDARY` | logic | `D7.13` | sheet-1 full-resolution: D7 first-gate pin13 has a drawn conductor, but its unique origin is not established after correcting the false IORD assignment, so it remains a measurem... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D7_B3_BOUNDARY` | logic | `D7.5` | sheet-1 D7 section 5,4->6: pin5 leaves west as a distinct conductor; next hop is unread in the available scan | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `D7_Y2_BOUNDARY` | memory/decode | `D7.3` | sheet-1 full-resolution package census: D7 section pins1/2 receive the D92.13 wire-11 boundary and MEMW/wire19; NAND output pin3 remains a measurement boundary because its far d... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `D7_Y4_TAG8` | logic | `D7.8` | sheet-1 full-resolution: D7 fourth NAND output pin8 leaves on the conductor explicitly marked 8; its unique far destination is not established, so tag 8 remains a measurement bo... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
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
| `FDC_DDEN` | FDC | `D26.13, D93.37, D6.15` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15; .009/MAME PC4 is also FDC density -> D93.37. July-2026 two-sided local D93 fit identifies pin37 and its l... | Confirm density-control level against drive/emulator behavior. |
| `FDC_DRQ` | FDC | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FDC_INTRQ` | FDC | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continui... | Continuity-check WD1793 pin to 8259 input before EKDOS bring-up. |
| `FRAME_INT` | timing/I/O | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (D55.OUT1 export, cro... | Cross-check against hardware when the peripheral path is exercised. |
| `HF_OUT` | video/analog | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delt... | Scope/capture video or timing node during video bring-up. |
| `LATCH_B` | timing/I/O | `D40.11, D37.2, D54.9, D54.15, D54.18` | scan+mame; +D54 CLK0/1/2: the drawn 1MHz rail = the D40.QD /16 tap (HDL+MAME concur; rail tag read pending) | Cross-check against hardware when the peripheral path is exercised. |
| `PHI2TTL` | logic | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_T) + "(1)" exit to s... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PIC_IR2_BOUNDARY` | logic | `D10.20` | scan sheet-1: D10 IR2 pin 20 has a distinct southbound conductor; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PIC_IR3_BOUNDARY` | logic | `D10.21` | scan sheet-1: D10 IR3 pin 21 has a distinct southbound conductor; far destination remains unread | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PIT_BAUD` | timing/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V (power corner) | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `PROM_EN` | logic | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed u... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `RAIL_E` | memory/decode | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members: DRAM pin 16 x32, b... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `RAM_SEL` | memory/decode | `D6.11, D92.5, R12.2` | scan sheet-2 (bite-2: -RAM SEL arrival -> D92.5 write-strobe NOR; source D6.11 RAM_N per sheet-1 "(1)" label). D53.6/G3 detached: its drawn feed = long west line [pending]; +R12... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `REV` | logic | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder region enable (G2A_N+G... | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `RF_RAIL` | video/analog | `VT3.3, C9.2, R72.2, C10.1, R73.1, C11.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed | Scope/capture video or timing node during video bring-up. |
| `ROE` | memory/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merged factory wire W13... | Probe during ROM/RAM stage; compare address/control timing to twin. |
| `SND_MIX` | sound/analog | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible | Bench-check waveform/current path with speaker disconnected first. |
| `SSTB_N` | logic | `D30.1` | sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
| `TAPE_RUN_INT` | logic | `D10.22` | scan sheet-1: D10 IR4 pin 22 is explicitly labeled (3) TAPE RUN INT; sheet-3 source remains outside the modeled board boundary | Verify with continuity, scope, or logic-analyzer trace during staged bring-up. |
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
