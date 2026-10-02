# Board fidelity gap ledger

Status: **BOARD FIDELITY GAPS CATALOGED**

This generated ledger records the remaining board-fidelity surfaces
from `kicad/juku.board.json` and the exact-source passive omission census:
chip-level provenance that is
still assumed, boundary-only, deferred, untraced, or dump-dependent, and
net-level source risks already carried into the bring-up checklist, and
drawing-proved passive refs absent from the model. It
is not a release decision by itself; its P0 rows feed `PLAN.md` and
prevent current gaps from hiding behind a green endpoint-coverage gate.
Validated physical PROM dumps are established evidence, not gap markers;
their unresolved board wiring remains listed under net-level risks.

## Command

```sh
python3 scripts/report_board_fidelity_gap_ledger.py
```

## Summary

- Board JSON: `kicad/juku.board.json`
- Chips modeled: `377`
- Nets modeled: `474`
- Chip-level fidelity gaps: `71`
- Source-proved passive refs absent from model: `0`
- Net-level source-risk gaps: `55`
- Explicitly dispositioned closed net risks: `14`
- Documented intentional no-connect pins: `63`

## Chip Provenance Types

| Provenance type | Chips |
| --- | ---: |
| .009 assembly drawing + registered component/solder/value photos + factory BOM | 3 |
| datasheet | 1 |
| exact .009 E3 sheet 1 + assembly + registered two-face owner photos | 1 |
| exact .009 E3 sheet 1 + assembly/owner photo | 3 |
| exact .009 E3 sheet 1 + assembly/photo | 3 |
| exact .009 E3 sheet 1 + factory assembly + owner photos | 8 |
| exact .009 E3 sheet 1 supply collective | 20 |
| exact .009 E3 sheet 2 | 3 |
| exact .009 E3 sheet 2 + assembly/owner photo | 2 |
| exact .009 E3 sheet 2 + assembly/photo | 6 |
| exact .009 E3 sheet 2 + owner photo | 2 |
| exact .009 factory assembly + registered owner photos | 1 |
| exact .009 sheet + factory assembly + owner photo | 2 |
| exact .009 sheet + owner continuity | 1 |
| exact .009 sheet 1 + factory assembly + owner photos | 1 |
| exact .009 source + owner photo | 2 |
| exact .009 source + registered owner photos | 2 |
| factory .009 assembly wire table + system cable map + registered owner photos | 1 |
| factory X3 cable table + registered owner photos | 12 |
| factory X4 cable table + legacy circuit | 1 |
| factory X4 cable table + owner photo | 23 |
| factory assembly + owner photo + continuity | 1 |
| factory assembly drawing + owner photo | 1 |
| factory power-cable table | 4 |
| factory shielded-cable table + registered owner photos | 2 |
| factory wire table | 14 |
| factory wire table + owner photos | 1 |
| factory wire table + registered owner backside photo | 1 |
| factory wire table + registered owner backside photos | 1 |
| factory wire table + registered owner photos | 3 |
| factory wire table + registered two-sided owner photos | 1 |
| factory wire table + two-sided owner photos | 1 |
| mame+datasheet | 1 |
| native schematic + factory assembly drawing + owner photo | 3 |
| photo | 1 |
| prom | 1 |
| registered owner photo | 1 |
| scan | 221 |
| scan + assembly drawing + registered owner photo | 2 |
| scan + factory assembly drawing | 4 |
| scan + factory assembly drawing + registered owner photo | 4 |
| scan + factory assembly wire table | 3 |
| scan + owner continuity | 1 |
| scan + registered owner photos | 3 |
| scan + target-photo override | 2 |
| scan+datasheet | 1 |
| wire | 1 |

## Gap Categories

| Category | Chip gaps | Net gaps |
| --- | ---: | ---: |
| FDC owner-continuity | 2 | 7 |
| PROM/decode | 0 | 1 |
| logic/source | 29 | 37 |
| memory/timing | 0 | 2 |
| placement/value | 40 | 0 |
| sound/analog | 0 | 2 |
| video/analog | 0 | 6 |

## Chip-Level Gaps

These are package/source/provenance gaps, not necessarily routed-copper
failures. Large repeated groups, such as unpopulated DRAM sockets and
decoupling capacitors, are still listed because they affect faithful
parts placement and Tier-3 reproduction.

### FDC owner-continuity

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D101` | `KP12_MUX` | scan + target-photo override | .009 official population and Э3 sheet 3 plus direct owner continuity no-conflict sheet paths close EARLY D93.17 to pin2, LATE D93.18 to pin14, delay taps D97... |
| `D99` | `AG3_ONESHOT` | scan + registered owner photos | .009 assembly position plus owner-photo 8901 one-shot package directly right of D95; cable obscures part of the К155АГ3 marking exact .009 sheet 3 closes A1_... |

### logic/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `AX603` | `WIRE_PAD` | factory shielded-cable table + registered owner photos | ДГШ5.109.009 СБ point А:3 factory conductor 1 joins bracket X6 to printed board point A:3 beside VT2/R65. The former VD3.2/SOUND_CLAMP landing claim is rejec... |
| `D1` | `CPU8080` | scan | complete КР580ВМ80А/8080 package contract: scan traces VSS pin2 to GND, VBB pin11 to locally derived -5V, VCC pin20 to +5V, and VDD pin28 to +12V; HOLD/pin13... |
| `D100` | `BUF8287` | datasheet | .009 official (5th ВА87 = drive-output buffer) complete 8287 contract including VSS pin10 and +5V VCC pin20; recovered .009 Э3 sheet 3 proves A-side inputs T... |
| `D104` | `UP2` | scan | sheet-1 triple К170УП2 receiver and power-pin table A24/SIN 4->13, A25/CTS 5->12, A26/DSR 6->11; datasheet fourth receiver is 7->10. Owner resistance 2026-07... |
| `D11` | `USART8251` | scan | complete КР580ВВ51А/8251 package contract including VSS pin4 and +5V VCC pin26; native sheet-1 directly loops RXRDY pin14 to D10 IR2 and TXRDY pin15 to D10 I... |
| `D12` | `LA18` | scan | Exact .009 sheet-1: pins1/2 tied to serial TXD inverse, open-collector output3 drives S_OC; pins6/7 tied to X1.114C -INT4, open-collector output5 joins X2.21... |
| `D13` | `TL2` | scan | ТЛ2: sheet-1 accounts for sections 1->2 RAMOUTEN, 3->4 system/USART clock, and 5->6 RESIN->RESET. Owner continuity on 2026-07-20 proves RESET enters the form... |
| `D38` | `LA1_GATE` | scan | sheet-2 full-resolution: second ЛА1 section pin5 receives D33.12 LATCH via its filled junction and westward branch, while pins4/2/1 receive numbered rails2/1... |
| `D41` | `IR16` | scan | complete sheet-2 package census plus Texas Instruments SDLS154 device contract: A-D pins2-5 share ground, SER1/OC8 share +5V rail A, QB12/QA13 are traced, QC... |
| `D7` | `LA3_GATE` | scan | complete sheet-1 full-resolution package census: section12,13->11 forms the PROM_EN strobe, with pin12 on CPU SYNC and pin13 fed back from output pin11 befor... |
| `R20` | `R_AXIAL` | exact .009 E3 sheet 1 + assembly/owner photo | assembly 114604420 labels vertical R20 above C21, left of D52; owner 200450127 has matching red body above green C21 Exact sheet 1 draws C21 then R20 in seri... |
| `R21` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R21 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R22` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R22 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R23` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R23 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R24` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R24 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R25` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R25 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R26` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R26 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R27` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R27 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R28` | `R_AXIAL` | exact .009 E3 sheet 1 + factory assembly + owner photos | Assembly R28..R21 left-to-right bank above D8; R28 position fixed by factory order and July/May owner photos Exact sheet 1 draws eight 1k branches from D8 ou... |
| `R35` | `R_AXIAL` | exact .009 E3 sheet 2 + assembly/photo | R35 RC clock shaper position Source 330 ohms and owner 330R body agree; calibrated owner pad geometry is pending. |
| `R4` | `R_AXIAL` | scan | Exact .009 sheet 1 puts one R4 contact on RES_RC. Owner component tile 200450127 shows the horizontal R4 100 body and its left joint near (802,1480); solder... |
| `R67` | `R_AXIAL` | scan | .009 factory identity plus independent registered July/May owner photos; target body reads 4K7 pin1 remains on the source-proved SOUND_CLAMP node. Both the e... |
| `RUNK1` | `R_AXIAL` | registered owner photo | local evidence placeholder only; historical reference remains unidentified populated 220-ohm body below-left of D98 retained at its photographed position aft... |
| `S1` | `SW` | factory assembly drawing + owner photo | ДГШ5.109.009 СБ sheets 1-5; PXL_20260710_200402344.jpg SPDT bracket switch contract declares contacts 1-3; wire-table rows 11/12 identify А:17->S1.1 and А:18... |
| `W11` | `WIRE_LINK` | factory wire table + registered owner photos | ДГШ5.109.009 СБ conductor position 7 / board point А:11 registered component-side surface joints at (261.325,128.548) and (142.256,123.468) mm; fitted insula... |
| `W14` | `WIRE_LINK` | factory wire table + registered owner backside photo | ДГШ5.109.009 СБ conductor position 10 / board point А:14 owner component photos prove A14A is the second D1-side white-wire surface joint at (23.621,184.440)... |
| `W19` | `WIRE_LINK` | factory wire table + registered owner photos | ДГШ5.109.009 СБ conductor position 13 / board point А:19 registered component-side surface joints at (35.308,122.281) and (130.027,121.736) mm; uninterrupted... |
| `W7` | `WIRE_LINK` | factory wire table + registered owner backside photos | ДГШ5.109.009 СБ conductor position 3 / board point А:7 owner component photos prove A7A is the printed-7 white-wire surface joint at (14.597,184.485) mm; the... |
| `W8` | `WIRE_LINK` | factory wire table + owner photos | ДГШ5.109.009 СБ conductor position 4 / board point А:8 factory table joins D5.1 to D38.8 and the D5-side surface joint is fitted at (40.811,99.989) mm; forme... |

### placement/value

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `C1` | `C_ELEC` | exact .009 E3 sheet 1 + assembly/owner photo | Exact .009 sheet 1 prints C1=47,0 in the reset RC network; assembly PXL_20260711_114604420.jpg labels the vertical C1 can and lower + end Owner 200439607 sho... |
| `C10` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C10 vertically immediately right of D93; later July owner photo 202708344 shows an upright green two-lead... |
| `C11` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C11 vertically between D95 and D99; later July owner photo 202708344 shows a green two-lead body there un... |
| `C12` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places target C12 vertically between D94 and D100; exact .009 sheet-1 supply detail groups C9...C12 as +5 V-to-g... |
| `C15` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C15 vertically between D97 and D102; later July owner views 202734776/202744232 show a green component ed... |
| `C34` | `C_KM` | scan | sheet-2 power corner native sheet-2 C34 bypass from grounded rail E to +5 V rail F; connected nets GND/P5V carry direct crop evidence physical placement unre... |
| `C35` | `C_KM` | scan | .009 factory drawing omits C35 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C36` | `C_KM` | scan | .009 factory drawing omits C36 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C37` | `C_KM` | scan | .009 factory drawing omits C37 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C38` | `C_KM` | scan | .009 factory drawing directly places C38 above D91 in the populated D91-D84 DRAM bank; the owner photo shows no capacitor body, and its bright marks continue... |
| `C39` | `C_KM` | scan | .009 factory drawing omits C39 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C40` | `C_KM` | scan | .009 factory drawing omits C40 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C41` | `C_KM` | scan | .009 factory drawing omits C41 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C42` | `C_KM` | scan | .009 factory drawing directly places C42 above D89 in the populated D91-D84 DRAM bank; the owner photo shows no capacitor body, and its bright marks continue... |
| `C43` | `C_KM` | scan | .009 factory drawing omits C43 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C44` | `C_KM` | scan | .009 factory drawing omits C44 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C45` | `C_KM` | scan | .009 factory drawing omits C45 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C46` | `C_KM` | scan | .009 factory drawing directly places C46 above D87 in the populated D91-D84 DRAM bank; the owner photo shows no capacitor body, and its bright marks continue... |
| `C47` | `C_KM` | scan | .009 factory drawing omits C47 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C48` | `C_KM` | scan | .009 factory drawing omits C48 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C49` | `C_KM` | scan | .009 factory drawing omits C49 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C50` | `C_KM` | scan | .009 factory drawing directly places C50 above D85 in the populated D91-D84 DRAM bank; the owner photo shows no capacitor body, and its bright marks continue... |
| `C54` | `C_KM` | scan | .009 factory drawing omits C54 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C55` | `C_KM` | scan | .009 factory drawing omits C55 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C56` | `C_KM` | scan | .009 factory drawing omits C56 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C57` | `C_KM` | scan | .009 factory drawing omits C57 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C58` | `C_KM` | scan | .009 factory drawing omits C58 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C59` | `C_KM` | scan | .009 factory drawing omits C59 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C60` | `C_KM` | scan | .009 factory drawing omits C60 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C61` | `C_KM` | scan | .009 factory drawing omits C61 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C62` | `C_KM` | scan | .009 factory drawing omits C62 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C64` | `C_KM` | scan | .009 factory drawing omits C64 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C65` | `C_KM` | scan | .009 factory drawing omits C65 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C66` | `C_KM` | scan | .009 factory drawing omits C66 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C67` | `C_KM` | scan | .009 factory drawing omits C67 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C68` | `C_KM` | scan | .009 factory drawing omits C68 from the target DRAM assembly and the owner photo shows no body at its inherited grid position; assembly DNP with the modeled... |
| `C73` | `C_TRIM` | exact .009 E3 sheet 2 + assembly/photo | C73 trimmer is fitted beside Z1 in the exact .009 assembly and owner-board D59 corner Exact .009 sheet-2 PXL_20260718_101908284.jpg draws the Z1+C73 series b... |
| `C85` | `C_KM` | exact .009 E3 sheet 1 supply collective | C85 is a member of the printed C82...C93 supply-bypass range. No individual C85 assembly callout is securely readable in the archived .009 placement panels;... |
| `C9` | `C_KM` | scan | ДГШ5.109.009 СБ FDC quadrant factory drawing places C9 vertically between D100 and D98; later July owner photo 202708344 shows a green two-lead body at that... |
| `C94` | `C_KM` | scan | ДГШ5.109.009 СБ; May and July owner views show bare board at the locally projected C94 centre factory drawing identifies a separate two-terminal C94 immediat... |

## Source-Proved Passive Refs Absent From Model

These exact `.009` drawing or owner-photo refs are listed in
`docs/omitted-resistor-census.md` but have no component in the board JSON.
They are separate from chip-level and net-level gaps, which can only
inspect components and endpoints already modeled.

| Ref | Source evidence |
| --- | --- |
| *None* | - |

## Documented Intentional No-Connects

These package pins are visibly unused in the authoritative schematic.
They are excluded from the unnetted-functional-pin list and emitted as
explicit KiCad schematic no-connect markers.

| Ref | Pins |
| --- | --- |
| `D1` | `16` |
| `D10` | `12, 13, 15` |
| `D102` | `4` |
| `D103` | `12, 13, 14` |
| `D104` | `10` |
| `D106` | `2, 3, 6, 12, 13` |
| `D11` | `18` |
| `D13` | `10, 11` |
| `D2` | `9, 10, 11` |
| `D26` | `39` |
| `D30` | `6, 9` |
| `D35` | `1, 2` |
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
| `D94` | `5` |
| `D97` | `13` |
| `D98` | `9, 10` |
| `X2` | `216, 228` |

## Net-Level Source Risks

This mirrors the net-risk surface used by
`docs/replica-bringup-verification-points.md`, but keeps it in the
same fidelity ledger as the chip provenance gaps.

| Net | Category | Endpoints | Source risk |
| --- | --- | --- | --- |
| `C10_1_BOUNDARY` | logic/source | `C10.1` | .009 C10 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `C10_2_BOUNDARY` | logic/source | `C10.2` | .009 C10 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-base assignment revision-superseded |
| `C11_1_BOUNDARY` | logic/source | `C11.1` | .009 C11 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `C11_2_BOUNDARY` | logic/source | `C11.2` | .009 C11 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF tank assignment revision-superseded |
| `C12_1_BOUNDARY` | logic/source | `C12.1` | .009 C12 bypass and later July owner photo prove a +5 V/GND lap-lead pair at the factory site (D100.20/D94.8). This provisional replica through-hole pad1 has... |
| `C12_2_BOUNDARY` | logic/source | `C12.2` | .009 C12 bypass and later July owner photo prove a +5 V/GND lap-lead pair at the factory site (D100.20/D94.8). This provisional replica through-hole pad2 has... |
| `C15_1_BOUNDARY` | logic/source | `C15.1` | .009 C15 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 VT4-collector assignment revision-superseded |
| `C15_2_BOUNDARY` | logic/source | `C15.2` | .009 C15 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-emitter assignment revision-superseded |
| `C94_1_BOUNDARY` | video/analog | `C94.1` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 hol... |
| `C94_2_BOUNDARY` | video/analog | `C94.2` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 hol... |
| `C9_1_BOUNDARY` | logic/source | `C9.1` | .009 C9 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF ground assignment revision-superseded |
| `C9_2_BOUNDARY` | logic/source | `C9.2` | .009 C9 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `CPU_WAIT_STATUS` | logic/source | `D1.24` | exact .009 full-sheet photo 101754468 traces D1.24 WAIT through lower filled junction and fold to D105.1; older .006 scan corroborates. Owner continuity 2026... |
| `D100_CONTROL_SHEET1_BOUNDARY` | logic/source | `D100.11` | Exact .009 Э3 sheet-3 detail PXL_20260718_101641055.jpg: D100 T/pin11 runs left to its own quoted sheet-1 continuation; it crosses nearby descending conducto... |
| `D101_D02_R92_R99` | FDC owner-continuity | `D101.3, D101.4, D101.5, D101.6, R92.1, R99.2, ... (+1)` | July-2026 calibrated component photo PXL_20260710_200418174.jpg shows uninterrupted target-board copper joining D101 К555КП12 pin4 D02 to R99.2 and R92.1. Ex... |
| `D14_I2_BOUNDARY` | logic/source | `D14.2` | factory IC census and owner package identify D14 as К170АП2; pin2 I2 is a package-model role, while exact .009 E3 sheet-1 serial detail has no traceable D14.... |
| `D14_O7_BOUNDARY` | logic/source | `D14.7` | factory IC census and owner package identify D14 as К170АП2; pin7 O7 is a package-model role, while exact .009 E3 sheet-1 serial detail has no traceable D14.... |
| `D26_PB5_E8_2_BOUNDARY` | logic/source | `D26.23` | Exact .009 sheet-1 detail PXL_20260718_101824181.MP.jpg sends D26 PB5/pin23 to E8.2, distinct from PB4/pin22 at E8.3 and CONTRDAT at E8.4. The .009 assembly... |
| `D26_PC0_D3_I5` | logic/source | `D26.14, D3.5, R15.1` | direct .009 owner continuity 2026-07-14: D26 PC0/pin14 reaches D3 inverter input pin5 and owner reports a resistor path to +5 V; exact .009 sheet-1 photo PXL... |
| `D26_PC1_D3_I3` | logic/source | `D26.15, D3.3, R16.1` | direct .009 owner continuity 2026-07-14: D26 PC1/pin15 reaches D3 inverter input pin3 and owner reports a resistor path to +5 V; exact .009 sheet-1 photo PXL... |
| `D34_SIG` | video/analog | `D34.11, R63.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D36_CAS_IN` | memory/timing | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and o... |
| `D58_STB_TAG5` | logic/source | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10... |
| `D94_D0_BOUNDARY` | PROM/decode | `D94.1, R8.1` | exact .009 E3 sheet 1 PXL_20260718_101817644.jpg draws R8=2k from +5 V to -WREQ; sheet 3 PXL_20260718_101633062.jpg traces D94.1 through the top bundle to WR... |
| `D99_B2_SHEET1_BOUNDARY` | FDC owner-continuity | `D99.10, D96.13` | exact .009 Э3 sheet-3 photo PXL_20260718_101641055.jpg joins D99 B2/pin10 to D96 section-2 active-low clear/pin13 at a marked junction; their shared conducto... |
| `D99_Q2N_BOUNDARY` | FDC owner-continuity | `D99.12, D100.9` | Exact .009 Э3 sheet-3 detail PXL_20260718_101641055.jpg: D99 section-2 Q_N/pin12 descends and turns left to D100 OE_N/pin9. This line crosses D100 T/pin11 wi... |
| `FDC_HLD_TO_D100` | FDC owner-continuity | `D93.28, D100.3, D99.2` | recovered .009 Э3 sheet 3 photo PXL_20260718_101641055.jpg: D93 HLD/pin28 drives D100 A6/pin3 and E12 post 3; drawn E12 2-3 bridge connects D99 B1/pin2. Orig... |
| `FDC_IMDRG` | FDC owner-continuity | `D26.38, D101.1` | Exact .009 Э3 sheet-1 native PXL_20260718_101824181.MP.jpg labels D26 PA6/pin38 IMDRG with sheet-3 continuation (3); sheet-3 PXL_20260718_101648508.jpg label... |
| `FDC_MOTOR_EN` | FDC owner-continuity | `D26.16, D99.11` | Exact .009 Э3 sheet 1 MOTOR EN continuation from D26 PC2/pin16 enters D99 CLR2_N/pin11 on sheet 3; D100 A7/pin7 is driven separately by D99 Q2/pin5. Original... |
| `INHIB_STATUS_BOUNDARY` | memory/timing | `D7.5, D29.3` | Exact .009 sheet-1 crop PXL_20260718_101813438.jpg (850,2900)-(1850,3650): D7 NAND input pin5 joins D29 physical input pin3 at a filled T junction. The share... |
| `INT4_RAW` | logic/source | `X1.114C, D12.6, D12.7` | Exact .009 sheet-1 PXL_20260718_101817644.jpg: -INT4 at X1.114C branches to both D12 LA18 gate inputs pins6 and7; D12.5 open-collector output reaches X2.214/... |
| `KBD_CONTRDAT` | logic/source | `D26.22, X9.9, A50.1` | Exact .009 sheet-1 detail PXL_20260718_101824181.MP.jpg sends D26.22/PB4 to E8.3 and E8.4 to CONTRDAT continuation 909; .009 assembly and owner front photo s... |
| `P5V` | FDC owner-continuity | `R78.2, D10.16, D1.20, D4.11, D107.11, D44.4, ... (+223)` | scan; sheet-1 arrow-A rail ties address-buffer direction pins D4.11/D107.11 and PIC master strap D10.16 high; native sheet-2 power corner continues +5 V rail... |
| `PHI1_D35` | logic/source | `D35.10, W7.2, R37.2` | factory wire А:7 D35 clock-source-side copper island D35.10 reaches the candidate A7B plated through-joint under mastic; the W7 insulated-wire termination re... |
| `PHI2_D35` | logic/source | `D35.12, W14.2, R36.2` | factory wire А:14 D35 clock-source-side copper island D35.12 reaches the candidate A14B plated through-joint under mastic; the W14 insulated-wire termination... |
| `R20_RETURN_SOURCE_HOLD` | logic/source | `R20.2` | exact .009 sheet-1 detail PXL_20260718_101801729.jpg plus full-sheet 101754468: R20 far symbol lead descends, crosses D50.5/R29 without a junction, and conti... |
| `R21_D8_OUTPUT_HOLD` | logic/source | `R21.2` | R21...R28 collective source output branch; R21 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R22_D8_OUTPUT_HOLD` | logic/source | `R22.2` | R21...R28 collective source output branch; R22 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R23_D8_OUTPUT_HOLD` | logic/source | `R23.2` | R21...R28 collective source output branch; R23 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R24_D8_OUTPUT_HOLD` | logic/source | `R24.2` | R21...R28 collective source output branch; R24 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R25_D8_OUTPUT_HOLD` | logic/source | `R25.2` | R21...R28 collective source output branch; R25 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R26_D8_OUTPUT_HOLD` | logic/source | `R26.2` | R21...R28 collective source output branch; R26 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R27_D8_OUTPUT_HOLD` | logic/source | `R27.2` | R21...R28 collective source output branch; R27 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R28_D8_OUTPUT_HOLD` | logic/source | `R28.2` | R21...R28 collective source output branch; R28 physical position fixed by assembly, but individual D8 output pin among 1-7,9 unresolved. This singleton holds... |
| `R67_2_BOUNDARY` | video/analog | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Exact .009 E3 sheet-2... |
| `S1_3_BOUNDARY` | logic/source | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not ident... |
| `SYNC_B` | logic/source | `D57.17` | exact-revision .009 E3 sheet 2 and direct owner continuity 2026-07-21 disprove the older scan chase that joined D57.OUT2/pin17 to both D56 triggers; D57.OUT2... |
| `TAPE_RUN_INT` | logic/source | `D10.22` | recovered .009 Э3 sheet 1 explicitly labels D10 IR4/pin22 as continuation (3) TAPE RUN INT, but the complete recovered .009 sheet 3 is the replacement FDC ci... |
| `TIMING_TAG17` | logic/source | `D36.2, D41.6` | scan sheet-2 full-resolution (D41 control-bundle crop): numbered timing rail 17 has direct junctions to D41 load pin6 and D36 second NAND input pin2; the uni... |
| `TIMING_TAG2` | logic/source | `D38.4, D34.4` | Exact .009 sheet-2 PXL_20260718_101911242.jpg draws D34.4 upward to top conductor 2; overlapping exact .009 PXL_20260718_101908284.jpg crop (950,3200)-(2350,... |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.3` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible |
| `X6_A3_BOUNDARY` | sound/analog | `AX603.1, X6.1` | Factory .009 assembly wire table item 151 proves A:3 to bracket X6.1; independent system drawing ДГШ3.031.011 Э6 identifies X6 as the display cable; exact .0... |
| `XTAL16M` | logic/source | `D39.10, D103.2, D42.9, D43.9, D37.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin1... |

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
| `PHI2TTL` | closed by exact-revision correction and the unique labeled cross-sheet pair; D92.2/.3 are explicitly excluded and every remaining drawn endpoint is modeled |
| `PIT_BAUD` | closed across the native sheets: sheet 2 proves D57.10 to the BAUD R. handoff, and sheet 1 draws one junctioned BAUD RATE conductor to both D11.9 TxC and D11.25 RxC |
| `POF` | closed by the sheet-1 tag6 to sheet-2 named-POF conductor; MAME is independent corroboration, not the source |
| `PROM_EN` | the native sheet closes D7.11/D7.13/R17.2 as one feedback-strobe conductor; the refuted D6.14 branch is tracked separately on D6_V_ENABLE |
| `REV` | closed by the native sheet-1 code-2 conductor: the upper labeled R13 1k pull-up branch is REV and reaches tied D9.4/D9.5, distinct from the lower R14/code-3 ROE branch |
| `ROE` | closed by direct D6.9-D13.1 continuity plus the native sheet-1 code-3 conductor: the lower labeled R14 1k pull-up branch is ROE, distinct from the upper R13/code-2 REV branch |
| `USART_RXRDY_IRQ` | closed by the native sheet-1 D11.14-to-D10.20 trace; the separately drawn off-sheet interface is explicitly excluded |
| `USART_TXRDY_IRQ` | closed by the native sheet-1 D11.15-to-D10.21 trace; the separately drawn off-sheet interface is explicitly excluded |
| `V3_RC` | the exact .009 sheet closes R17.1/C99.1/D9.6 as one RC node and places C99.2 on GND; owner-board pad identity and population remain inspection questions |
| `VERT_RTR` | closed on exact-revision .009 E3 sheet 2 by the matching VER RTR/tag2 conductor joining D55.13, D35.9, and D57.18 |
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
