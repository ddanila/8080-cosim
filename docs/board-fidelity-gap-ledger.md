# Board fidelity gap ledger

Status: **BOARD FIDELITY GAPS CATALOGED**

This generated ledger records the remaining board-fidelity surfaces that
are explicit in `kicad/juku.board.json`: chip-level provenance that is
still assumed, boundary-only, deferred, untraced, or dump-dependent, and
net-level source risks already carried into the bring-up checklist. It
is not a release decision by itself; its P0 rows feed `PLAN.md` and
prevent current gaps from hiding behind a green endpoint-coverage gate.

## Command

```sh
python3 scripts/report_board_fidelity_gap_ledger.py
```

## Summary

- Board JSON: `kicad/juku.board.json`
- Chips modeled: `325`
- Nets modeled: `504`
- Chip-level fidelity gaps: `60`
- Net-level source-risk gaps: `88`
- Explicitly dispositioned closed net risks: `14`
- Documented intentional no-connect pins: `59`

## Chip Provenance Types

| Provenance type | Chips |
| --- | ---: |
| .009 assembly drawing + owner photo | 1 |
| .009 assembly drawing + registered component/solder/value photos + factory BOM | 3 |
| datasheet | 1 |
| factory X3 cable table + registered owner photos | 12 |
| factory X4 cable table + legacy circuit | 1 |
| factory X4 cable table + owner photo | 23 |
| factory assembly drawing + owner photo | 1 |
| factory power-cable table | 4 |
| factory shielded-cable table + registered owner photos | 3 |
| factory wire table | 14 |
| factory wire table + owner photos | 1 |
| factory wire table + registered owner backside photo | 1 |
| factory wire table + registered owner backside photos | 1 |
| factory wire table + registered owner photos | 3 |
| factory wire table + registered two-sided owner photos | 1 |
| factory wire table + two-sided owner photos | 1 |
| mame+datasheet | 1 |
| native schematic + factory assembly drawing + owner photo | 1 |
| owner continuity 2026-07-19 | 1 |
| photo | 4 |
| prom | 1 |
| scan | 233 |
| scan + assembly drawing + registered owner photo | 2 |
| scan + factory assembly wire table | 3 |
| scan + owner photo | 1 |
| scan + registered owner photo | 1 |
| scan + registered owner photos | 2 |
| scan + target-photo override | 2 |
| scan+datasheet | 1 |
| wire | 1 |

## Gap Categories

| Category | Chip gaps | Net gaps |
| --- | ---: | ---: |
| FDC owner-continuity | 7 | 47 |
| PROM truth | 2 | 0 |
| PROM/decode | 0 | 5 |
| logic/source | 12 | 29 |
| memory/timing | 0 | 2 |
| placement/refdes | 26 | 0 |
| placement/value | 13 | 0 |
| sound/analog | 0 | 1 |
| video/analog | 0 | 4 |

## Chip-Level Gaps

These are package/source/provenance gaps, not necessarily routed-copper
failures. Large repeated groups, such as unpopulated DRAM sockets and
decoupling capacitors, are still listed because they affect faithful
parts placement and Tier-3 reproduction.

### FDC owner-continuity

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D101` | `KP12_MUX` | scan + target-photo override | .009 official population and Э3 sheet 3 plus direct owner continuity no-conflict sheet paths close EARLY D93.17 to pin2, LATE D93.18 to pin14, delay taps D97... |
| `D102` | `AG3_ONESHOT` | scan | .009 assembly position, .009 Э3 sheet 3, and owner-photo К155АГ3 8901 marking sheet 3 closes both cascaded write-precomp delays: D97.12 to pin10/output5, pin... |
| `D106` | `IE7_CTR` | scan | .009 official FDC population; К555ИЕ7 identity and standard 74193-class pinout power pins 8/16 routed; corrected component and solder fits identify all 14 co... |
| `D28` | `LN3_OC_INV` | scan | .009 official FDC population identifies К155ЛН3 К155ЛН3 datasheet pinout; power pins 7/14 routed; validated component and reflected solder fits identify all... |
| `D96` | `TM2_DFF` | scan | .009 official FDC population; КМ555ТМ2 identity and standard pinout power pins 7/14 routed; full component registration and reflected solder fit identify the... |
| `D97` | `AG3_ONESHOT` | scan | .009 assembly position, .009 Э3 sheet 3, and owner-photo К155АГ3 8901 marking sheet 3 closes the first write-precomp delay: WDATA on pin10, output pin5 to D1... |
| `D99` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo 8901 one-shot package directly right of D95; cable obscures part of the К155АГ3 marking 16-pin package and standard A... |

### PROM truth

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D6` | `DEC_PROM` | scan | validated physical dump uses RT4 address order A0-A7=5/6/7/4/3/2/1/15. Direct .009 owner continuity on 2026-07-14 proves board signals BA15,BA14,BA13,BA12,BA... |
| `D94` | `RE3_PROM_092` | prom | .009 official; programming ДГШ5.106.092; validated repeated physical table adopted РЕ3 pinout; validated physical .092 table raw SHA256 bcf942a87ee70adb1a16c... |

### logic/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D1` | `CPU8080` | scan | complete КР580ВМ80А/8080 package contract: scan traces VSS pin2 to GND, VBB pin11 to locally derived -5V, VCC pin20 to +5V, and VDD pin28 to +12V; HOLD/pin13... |
| `D105` | `LA3_GATE` | scan | .009 official placement; sheet-1 .006 wait/MRD logic 12+13 tied from MEMW -> 11 to D30.13; direct .009 owner continuity on 2026-07-14 proves pin1 joins D6.15... |
| `D13` | `TL2` | scan | ТЛ2: sheet-1 accounts for sections 1->2 RAMOUTEN, 3->4 system/USART clock, and 5->6 RESIN->RESET. Chip-removed owner continuity on 2026-07-14 supersedes the... |
| `D30` | `TM2_DFF` | scan | .009 official; assembly drawing position and sheet-1 READY circuit section A: D input2 receives physical D2.12 through the R6 pull-up node, CLK3=PHI2TTL, /CL... |
| `R67` | `R_AXIAL` | scan | .009 factory identity plus independent registered July/May owner photos; target body reads 4K7 pin1 remains on the source-proved SOUND_CLAMP node. The revisi... |
| `R8` | `R_AXIAL` | owner continuity 2026-07-19 | R8, physical placement not yet registered in the replica one end joins only D94.1 in the measured scope; the other end reaches +5 V; measured resistance appr... |
| `S1` | `SW` | factory assembly drawing + owner photo | ДГШ5.109.009 СБ sheets 1-5; PXL_20260710_200402344.jpg SPDT bracket switch contract declares contacts 1-3; wire-table rows 11/12 identify А:17->S1.1 and А:18... |
| `W11` | `WIRE_LINK` | factory wire table + registered owner photos | ДГШ5.109.009 СБ conductor position 7 / board point А:11 registered component-side surface joints at (261.325,128.548) and (142.256,123.468) mm; fitted insula... |
| `W14` | `WIRE_LINK` | factory wire table + registered owner backside photo | ДГШ5.109.009 СБ conductor position 10 / board point А:14 registered plated through-joints beside the printed 14 marks at (10.449,179.305) and (224.478,193.14... |
| `W19` | `WIRE_LINK` | factory wire table + registered owner photos | ДГШ5.109.009 СБ conductor position 13 / board point А:19 registered component-side surface joints at (35.308,122.281) and (130.027,121.736) mm; uninterrupted... |
| `W7` | `WIRE_LINK` | factory wire table + registered owner backside photos | ДГШ5.109.009 СБ conductor position 3 / board point А:7 registered plated through-joints beside the printed 7 marks at (1.697,179.350) and (227.668,194.422) m... |
| `W8` | `WIRE_LINK` | factory wire table + owner photos | ДГШ5.109.009 СБ conductor position 4 / board point А:8 two independently registered component-side surface joints at (40.811,99.989) and (223.601,170.724) mm... |

### placement/refdes

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `C35` | `C_KM` | scan | .009 factory drawing omits C35 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C36` | `C_KM` | scan | .009 factory drawing omits C36 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C37` | `C_KM` | scan | .009 factory drawing omits C37 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C39` | `C_KM` | scan | .009 factory drawing omits C39 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C40` | `C_KM` | scan | .009 factory drawing omits C40 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C41` | `C_KM` | scan | .009 factory drawing omits C41 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C43` | `C_KM` | scan | .009 factory drawing omits C43 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C44` | `C_KM` | scan | .009 factory drawing omits C44 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C45` | `C_KM` | scan | .009 factory drawing omits C45 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C47` | `C_KM` | scan | .009 factory drawing omits C47 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C48` | `C_KM` | scan | .009 factory drawing omits C48 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C49` | `C_KM` | scan | .009 factory drawing omits C49 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C54` | `C_KM` | scan | .009 factory drawing omits C54 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C55` | `C_KM` | scan | .009 factory drawing omits C55 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C56` | `C_KM` | scan | .009 factory drawing omits C56 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C57` | `C_KM` | scan | .009 factory drawing omits C57 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C58` | `C_KM` | scan | .009 factory drawing omits C58 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C59` | `C_KM` | scan | .009 factory drawing omits C59 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C60` | `C_KM` | scan | .009 factory drawing omits C60 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C61` | `C_KM` | scan | .009 factory drawing omits C61 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C62` | `C_KM` | scan | .009 factory drawing omits C62 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C64` | `C_KM` | scan | .009 factory drawing omits C64 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C65` | `C_KM` | scan | .009 factory drawing omits C65 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C66` | `C_KM` | scan | .009 factory drawing omits C66 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C67` | `C_KM` | scan | .009 factory drawing omits C67 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |
| `C68` | `C_KM` | scan | .009 factory drawing omits C68 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with... |

### placement/value

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `C10` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C10 vertically immediately right of D93; both target-revision electrical destinations remain explicit con... |
| `C11` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C11 vertically between D95 and D99; both target-revision electrical destinations remain explicit continui... |
| `C12` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places the target C12 vertically between D94 and D100; the .006 trimmer identity is revision-superseded and both... |
| `C15` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C15 vertically between D97 and D102; both target-revision electrical destinations remain explicit continu... |
| `C20` | `C_KM` | scan | ДГШ5.109.009 СБ plus registered owner component/solder photos and ГОСТ 11076-69 electrical sheet 3 closes C20.1 to D102.6 and C20.2 to D102.7/R108.1. Owner e... |
| `C22` | `C_KM` | scan | ДГШ5.109.009 СБ plus independent owner component angle/registered solder photo and ГОСТ 11076-69 electrical sheet 3 closes C22.1 to D102.14 and C22.2 to D102... |
| `C38` | `C_KM` | scan | .009 factory drawing directly places C38 above D91 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and... |
| `C42` | `C_KM` | scan | .009 factory drawing directly places C42 above D89 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and... |
| `C46` | `C_KM` | scan | .009 factory drawing directly places C46 above D87 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and... |
| `C50` | `C_KM` | scan | .009 factory drawing directly places C50 above D85 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and... |
| `C9` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C9 vertically between D100 and D98; both target-revision electrical destinations remain explicit continui... |
| `C94` | `C_KM` | scan | ДГШ5.109.009 СБ; owner component views are VT2-obscured at the projected C94 site factory drawing identifies a separate two-terminal C94 immediately right of... |
| `C99` | `C_KM` | scan | sheet-1 D7/D9 RC decode path native 5150x3603 sheet-1 review prints C99=160 and proves pin1 on V3_RC; the pin2 plate is visibly drawn without an outgoing con... |

## Documented Intentional No-Connects

These package pins are visibly unused in the authoritative schematic.
They are excluded from the unnetted-functional-pin list and emitted as
explicit KiCad schematic no-connect markers.

| Ref | Pins |
| --- | --- |
| `D1` | `16` |
| `D10` | `12, 13, 15` |
| `D103` | `12, 13, 14` |
| `D11` | `18` |
| `D13` | `8, 9, 10, 11` |
| `D2` | `9, 10, 11` |
| `D26` | `39` |
| `D28` | `5, 6` |
| `D30` | `6, 9` |
| `D35` | `1, 2, 5, 6` |
| `D37` | `8, 9, 10` |
| `D40` | `3, 4, 5, 6, 15` |
| `D41` | `10, 11` |
| `D42` | `11, 12, 13` |
| `D43` | `11, 12, 13` |
| `D44` | `13` |
| `D45` | `13` |
| `D46` | `13` |
| `D47` | `12, 13` |
| `D52` | `9, 10, 11, 12, 13, 14` |
| `D53` | `7, 9, 10, 11` |
| `D56` | `13` |
| `D59` | `5, 6` |
| `D94` | `5` |

## Net-Level Source Risks

This mirrors the net-risk surface used by
`docs/replica-bringup-verification-points.md`, but keeps it in the
same fidelity ledger as the chip provenance gaps.

| Net | Category | Endpoints | Source risk |
| --- | --- | --- | --- |
| `AMW_N` | logic/source | `D7.3` | D7 NAND output pin3 remains a boundary. Owner continuity 2026-07-19 disproves the earlier sheet interpretation that joined it to D29.5; D29.5 instead belongs... |
| `C10_1_BOUNDARY` | logic/source | `C10.1` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `C10_2_BOUNDARY` | logic/source | `C10.2` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 VT4-base assignment is revision-superseded |
| `C11_1_BOUNDARY` | logic/source | `C11.1` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `C11_2_BOUNDARY` | logic/source | `C11.2` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF tank assignment is revision-superseded |
| `C12_1_BOUNDARY` | logic/source | `C12.1` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded |
| `C12_2_BOUNDARY` | logic/source | `C12.2` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded |
| `C15_1_BOUNDARY` | logic/source | `C15.1` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-collector assignment is revision-superseded |
| `C15_2_BOUNDARY` | logic/source | `C15.2` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-emitter assignment is revision-superseded |
| `C99_FAR` | logic/source | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity bounda... |
| `C9_1_BOUNDARY` | logic/source | `C9.1` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF ground assignment is revision-superseded |
| `C9_2_BOUNDARY` | logic/source | `C9.2` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `CPU_WAIT_STATUS` | logic/source | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread |
| `CS_FDC` | PROM/decode | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 r... |
| `D101_D00_BOUNDARY` | FDC owner-continuity | `D101.6` | July-2026 validated component and solder package fits identify D101 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary |
| `D101_D01_BOUNDARY` | FDC owner-continuity | `D101.5` | July-2026 validated component and solder package fits identify D101 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary |
| `D101_D03_BOUNDARY` | FDC owner-continuity | `D101.3` | July-2026 validated component and solder package fits identify D101 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary |
| `D101_OE0_BOUNDARY` | FDC owner-continuity | `D101.1` | July-2026 validated component and solder package fits identify D101 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_Q1N_BOUNDARY` | FDC owner-continuity | `D102.4` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary |
| `D104_X4_IN_BOUNDARY` | logic/source | `D104.7` | owner resistance 2026-07-19 measures approximately 84 kohm between D104.7 and D94.13, disproving the former direct-net claim; D104 receiver input pin7 remain... |
| `D104_X4_OUT_BOUNDARY` | logic/source | `D104.10` | July-2026 reflected D104 solder fit identifies output pin10 at (2350.714,1249.143) px with no B.Cu departure in two backside views; both component overlaps h... |
| `D106_BO_BOUNDARY` | FDC owner-continuity | `D106.13` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin13 BO; no remote destination is proved, so this remains a measurement boundary |
| `D106_CLR_BOUNDARY` | FDC owner-continuity | `D106.14` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin14 CLR; no remote destination is proved, so this remains a measurement boundary |
| `D106_CO_BOUNDARY` | FDC owner-continuity | `D106.12` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin12 CO; no remote destination is proved, so this remains a measurement boundary |
| `D106_D0_BOUNDARY` | FDC owner-continuity | `D106.15` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin15 D0; calibrated raw-crop review finds only local copper into a nearby handoff, with... |
| `D106_D1_BOUNDARY` | FDC owner-continuity | `D106.1` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin1 D1; calibrated raw-crop review finds only local copper into a nearby handoff, with n... |
| `D106_D2_BOUNDARY` | FDC owner-continuity | `D106.10` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin10 D2 while the solder end projects beneath crossing rail metal; that apparent overlap is not co... |
| `D106_D3_BOUNDARY` | FDC owner-continuity | `D106.9` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin9 D3 while the solder end projects beneath crossing rail metal; that apparent overlap is not con... |
| `D106_LOAD_BOUNDARY` | FDC owner-continuity | `D106.11` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin11 LOAD_N; no remote destination is proved, so this remains a measurement boun... |
| `D106_Q0_BOUNDARY` | FDC owner-continuity | `D106.3` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin3 Q0; no remote destination is proved, so this remains a measurement boundary |
| `D106_Q1_BOUNDARY` | FDC owner-continuity | `D106.2` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin2 Q1; no remote destination is proved, so this remains a measurement boundary |
| `D106_Q2_BOUNDARY` | FDC owner-continuity | `D106.6` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin6 Q2; no remote destination is proved, so this remains a measurement boundary |
| `D106_UP_BOUNDARY` | FDC owner-continuity | `D106.5` | July-2026 corrected component and solder fits identify D106 К555ИЕ7 pin5 UP; calibrated raw-crop review finds only local copper, with no uninterrupted path t... |
| `D14_I2_BOUNDARY` | logic/source | `D14.2` | sheet-1 full-resolution К170АП2 package census identifies D14 input pin2; its remote serial-interface source is unread and remains a measurement boundary |
| `D14_O7_BOUNDARY` | logic/source | `D14.7` | sheet-1 full-resolution К170АП2 package census identifies D14 output pin7; its remote serial-interface destination is unread and remains a measurement boundary |
| `D26_PA6_PREN_BOUNDARY` | logic/source | `D26.38` | sheet-1 full-resolution: D26 PA6 pin38 leaves on the conductor labeled PREN with off-sheet marker (3); the far destination is unread, so this remains a measu... |
| `D26_PB4_BOUNDARY` | logic/source | `D26.22` | sheet-1 full-resolution: D26 PB4 pin22 enters the E8 CONTRDAT selector region, but the absent switch symbol prevents a proved remote endpoint, so this remain... |
| `D29_AIN1_BOUNDARY` | logic/source | `D29.2` | sheet-1 native 5150x3603 command-buffer chase identifies semantic command A1/CCLCK on D29 physical A1 pin2; its westbound conductor enters the dense D5/D105... |
| `D34_A1_TAG2` | logic/source | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in... |
| `D34_SIG` | video/analog | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D36_CAS_IN` | memory/timing | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and o... |
| `D56_Q2N_TAG16` | memory/timing | `D56.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D56 second-section Q2_N pin12 leaves east on conductor code 16; the former D34.10 merge is dispr... |
| `D58_STB_TAG5` | logic/source | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10... |
| `D93_HLT_BOUNDARY` | FDC owner-continuity | `D93.23` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin23 HLT; remote drive-interface continuity is not proved, so this remains a meas... |
| `D93_MR_BOUNDARY` | FDC owner-continuity | `D93.19` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin19 MR_N; remote reset continuity is not proved, so this remains a measurement b... |
| `D93_RG_BOUNDARY` | FDC owner-continuity | `D93.25` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin25 RG; remote separator continuity is not proved, so this remains a measurement... |
| `D93_TEST_BOUNDARY` | FDC owner-continuity | `D93.22` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin22 TEST; remote strap continuity is not proved, so this remains a measurement b... |
| `D93_WF_VFOE_BOUNDARY` | FDC owner-continuity | `D93.33` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin33 WF_VFOE; remote drive/separator continuity is not proved, so this remains a... |
| `D94_D0_BOUNDARY` | PROM/decode | `D94.1, R8.1` | owner continuity 2026-07-19: D94.1 joins R8 through approximately 2 kohm to +5 V; no other connection was found |
| `D94_D5` | PROM/decode | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary |
| `D94_D6` | PROM/decode | `D94.7` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because... |
| `D94_D7` | PROM/decode | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary |
| `D96_CLK2_BOUNDARY` | FDC owner-continuity | `D96.11` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin11 CLK2; no remote destination is proved, so this remains a m... |
| `D96_CLR1_BOUNDARY` | FDC owner-continuity | `D96.1` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin1 CLR1_N; no remote destination is proved, so this remains a... |
| `D96_CLR2_BOUNDARY` | FDC owner-continuity | `D96.13` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin13 CLR2_N; no remote destination is proved, so this remains a... |
| `D96_D1_BOUNDARY` | FDC owner-continuity | `D96.2` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin2 D1; no remote destination is proved, so this remains a meas... |
| `D96_D2_BOUNDARY` | FDC owner-continuity | `D96.12` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin12 D2; no remote destination is proved, so this remains a mea... |
| `D96_PRE1_BOUNDARY` | FDC owner-continuity | `D96.4` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin4 PRE1_N; no remote destination is proved, so this remains a... |
| `D96_PRE2_BOUNDARY` | FDC owner-continuity | `D96.10` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin10 PRE2_N; no remote destination is proved, so this remains a... |
| `D96_Q1N_BOUNDARY` | FDC owner-continuity | `D96.6` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin6 Q1_N; no remote destination is proved, so this remains a me... |
| `D96_Q2_BOUNDARY` | FDC owner-continuity | `D96.9` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin9 Q2; no remote destination is proved, so this remains a meas... |
| `D97_Q1_BOUNDARY` | FDC owner-continuity | `D97.13` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary |
| `D98_A4_BOUNDARY` | FDC owner-continuity | `D98.10` | July-2026 validated package registration identifies D98 К155ЛП11 pin10 A4; no remote destination is proved, so this remains a measurement boundary |
| `D98_Y4_BOUNDARY` | FDC owner-continuity | `D98.9` | July-2026 validated package registration identifies D98 К155ЛП11 pin9 Y4; no remote destination is proved, so this remains a measurement boundary |
| `D99_A1N_BOUNDARY` | FDC owner-continuity | `D99.1` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement... |
| `D99_B2_BOUNDARY` | FDC owner-continuity | `D99.10` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement... |
| `D99_C1_BOUNDARY` | FDC owner-continuity | `D99.14` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement... |
| `D99_C2_BOUNDARY` | FDC owner-continuity | `D99.6` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement... |
| `D99_CLR2_BOUNDARY` | FDC owner-continuity | `D99.11` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measure... |
| `D99_Q1N_BOUNDARY` | FDC owner-continuity | `D99.4` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement... |
| `D99_Q1_BOUNDARY` | FDC owner-continuity | `D99.13` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement... |
| `D99_Q2N_BOUNDARY` | FDC owner-continuity | `D99.12` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measureme... |
| `D99_Q2_BOUNDARY` | FDC owner-continuity | `D99.5` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement... |
| `D99_RC1_BOUNDARY` | FDC owner-continuity | `D99.15` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measuremen... |
| `D99_RC2_BOUNDARY` | FDC owner-continuity | `D99.7` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement... |
| `FDC_DRQ` | FDC owner-continuity | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `FDC_INTRQ` | FDC owner-continuity | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `INHIB_STATUS_BOUNDARY` | logic/source | `D7.5, D29.3` | sheet-1 native 5150x3603 direct-junction chase: D7 data-turnaround NAND input pin5 and semantic D29 command A0 on physical package channel A2/pin3 meet at an... |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Registered July and M... |
| `R94_P2_BOUNDARY` | logic/source | `R94.2` | July-2026 registered component photo identifies the lower terminal of R94 220 ohm; only the upper terminal to D98.3 is proved and pin2 remains a measurement... |
| `READY_PRE_N` | logic/source | `D30.4` | D30 section-A asynchronous preset pin4 remains a target-board continuity boundary after owner measurements moved R5 to D30.10/.12 |
| `S1_3_BOUNDARY` | logic/source | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not ident... |
| `TAPE_RUN_INT` | logic/source | `D10.22` | scan sheet-1: D10 IR4 pin 22 is explicitly labeled (3) TAPE RUN INT; sheet-3 source remains outside the modeled board boundary |
| `TIMING_TAG2` | logic/source | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's... |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.3` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `XTAL16M` | logic/source | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin1... |

## Explicitly Closed Regex Matches

These nets contain historical uncertainty words in their provenance,
but stronger evidence closes the modeled conductor. Their explicit
`source_risk=false` dispositions prevent prose history from inflating
the active release-risk count.

| Net | Disposition |
| --- | --- |
| `D25_T` | the native sheet closes the D7.6-to-D25.11 turnaround conductor; unread upstream inputs belong to MEMW and INHIB_STATUS_BOUNDARY, not this output net |
| `D30_Q2N_D29_AIN7` | closed by direct owner continuity; the word boundary refers only to the superseded scan interpretation |
| `FRAME_INT` | closed across native sheets 2 and 1; D35.8 and D10.23 share the named FRAME INT off-sheet conductor and R60 pull-up |
| `PHI2TTL` | owner measurement retired: the full-resolution sheet-2 Ф2TTL (1) export and sheet-1 (2) Ф2 TTL arrival are a unique labeled cross-sheet pair, and every drawn endpoint is modeled |
| `PIT_BAUD` | closed across the native sheets: sheet 2 proves D57.10 to the BAUD R. handoff, and sheet 1 draws one junctioned BAUD RATE conductor to both D11.9 TxC and D11.25 RxC |
| `POF` | closed by the sheet-1 tag6 to sheet-2 named-POF conductor; MAME is independent corroboration, not the source |
| `PROM_EN` | the native sheet closes D7.11/D7.13/R17.2 as one feedback-strobe conductor; the refuted D6.14 branch is tracked separately on D6_V_ENABLE |
| `REV` | closed by the native sheet-1 code-2 conductor: the upper labeled R13 1k pull-up branch is REV and reaches tied D9.4/D9.5, distinct from the lower R14/code-3 ROE branch |
| `ROE` | closed by direct D6.9-D13.1 continuity plus the native sheet-1 code-3 conductor: the lower labeled R14 1k pull-up branch is ROE, distinct from the upper R13/code-2 REV branch |
| `USART_RXRDY_IRQ` | closed by the native sheet-1 D11.14-to-D10.20 trace; the separately drawn off-sheet interface is explicitly excluded |
| `USART_TXRDY_IRQ` | closed by the native sheet-1 D11.15-to-D10.21 trace; the separately drawn off-sheet interface is explicitly excluded |
| `V3_RC` | the native sheet closes R17.1/C99.1/D9.6 as one RC node; uncertainty on the opposite C99 plate is isolated on C99_FAR |
| `VERT_RTR` | closed on native sheet 2 by the matching VER RTR/tag2 conductor between D55.13 and D35.9 |
| `W_RAIL16` | the native sheet closes both D36 write-NAND inputs and its complete output fanout: MEMW->D36.9, D36.3->D33.11/.10->D36.10, and D36.8->all DRAM W pins; only the simulation timing abstraction remains |

## Automatic Closure Rule

- If a gap can be closed from existing scans/docs/code, update
  `kicad/juku.board.json` first, then regenerate this report and the
  manufacturing readiness packet.
- If a gap depends on PROM contents, hidden routing, owner continuity,
  analog measurement, or vendor/order evidence, keep it listed here
  until that stronger evidence exists.
- Endpoint coverage remains necessary but not sufficient: it proves the
  PCB preserves modeled connectivity, while this ledger records where
  the model is still not fully historical-source-proven.
