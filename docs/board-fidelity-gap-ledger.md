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
- Chips modeled: `306`
- Nets modeled: `557`
- Chip-level fidelity gaps: `56`
- Net-level source-risk gaps: `228`
- Documented intentional no-connect pins: `67`

## Chip Provenance Types

| Provenance type | Chips |
| --- | ---: |
| .009 assembly drawing + owner photo | 1 |
| datasheet | 1 |
| factory X3 cable table + registered owner photos | 12 |
| factory X4 cable table + legacy circuit | 1 |
| factory X4 cable table + owner photo | 23 |
| factory assembly drawing + owner photo | 1 |
| factory power-cable table | 4 |
| factory wire table | 14 |
| factory wire table + registered two-sided owner photos | 1 |
| mame+datasheet | 1 |
| photo | 4 |
| prom | 1 |
| scan | 233 |
| scan + assembly drawing + registered owner photo | 2 |
| scan + factory assembly wire table | 3 |
| scan + owner photo | 1 |
| scan + registered owner photo | 1 |
| scan+datasheet | 1 |
| wire | 1 |

## Gap Categories

| Category | Chip gaps | Net gaps |
| --- | ---: | ---: |
| FDC owner-continuity | 9 | 24 |
| PROM truth | 1 | 0 |
| PROM/decode | 0 | 16 |
| clock/I/O | 0 | 5 |
| logic/source | 7 | 160 |
| memory/timing | 0 | 8 |
| placement/refdes | 38 | 0 |
| placement/value | 1 | 0 |
| sound/analog | 0 | 1 |
| video/analog | 0 | 14 |

## Chip-Level Gaps

These are package/source/provenance gaps, not necessarily routed-copper
failures. Large repeated groups, such as unpopulated DRAM sockets and
decoupling capacitors, are still listed because they affect faithful
parts placement and Tier-3 reproduction.

### FDC owner-continuity

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D101` | `KP12_MUX` | scan | .009 official FDC population identifies К555КП12 К555КП12/74LS253 datasheet pinout; power pins 8/16 routed; validated component and solder fits identify all... |
| `D102` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo К155АГ3 8901 marking; D102 is the rightmost lower-row one-shot 16-pin package and standard AG3 pinout; power pins 8/1... |
| `D106` | `IE7_CTR` | scan | .009 official FDC population; К555ИЕ7 identity and standard 74193-class pinout power pins 8/16 routed; corrected component and solder fits identify all 14 co... |
| `D28` | `LN3_OC_INV` | scan | .009 official FDC population identifies К155ЛН3 К155ЛН3 datasheet pinout; power pins 7/14 routed; validated component and reflected solder fits identify all... |
| `D95` | `KP12_MUX` | scan | .009 official FDC population identifies К555КП12 К555КП12/74LS253 datasheet pinout; power pins 8/16 routed; validated component and solder fits identify all... |
| `D96` | `TM2_DFF` | scan | .009 official FDC population; КМ555ТМ2 identity and standard pinout power pins 7/14 routed; full component registration and reflected solder fit identify the... |
| `D97` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo К155АГ3 8901 marking; D97 is the first lower-row one-shot right of D101 16-pin package and standard AG3 pinout; power... |
| `D98` | `LP11_BUF` | scan | .009 official FDC population identifies К155ЛП11 К155ЛП11/SN74367 datasheet pinout; power pins 8/16 routed; D98.3 is proved to R94 and D98.7 to S1.2, while r... |
| `D99` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo 8901 one-shot package directly right of D95; cable obscures part of the К155АГ3 marking 16-pin package and standard A... |

### PROM truth

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D94` | `RE3_PROM_092` | prom | .009 official; programming ДГШ5.106.092 (dump pending) РЕ3 pinout; A0-A4 = BA11-15 (same convention as D8); corrected July-2026 local pin fit traces D0/pin1-... |

### logic/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D1` | `CPU8080` | scan | complete КР580ВМ80А/8080 package contract: scan traces VSS pin2 to GND, VBB pin11 to locally derived -5V, VCC pin20 to +5V, and VDD pin28 to +12V; HOLD/pin13... |
| `D100` | `BUF8287` | datasheet | .009 official (5th ВА87 = FDC bus buffer) complete 8287 contract including VSS pin10 and +5V VCC pin20; OE_N pin9 and T pin11 are two-sided photo-identified... |
| `D105` | `LA3_GATE` | scan | .009 official placement; sheet-1 .006 wait/MRD logic 12+13 tied from MRD -> 11 to D30.13; 1 from MWR and 2 from D13.4 -> 3 boundary; D2.12 -> 9 with named of... |
| `D30` | `TM2_DFF` | scan | .009 official; assembly drawing position and sheet-1 READY circuit section A: D input2 receives physical D2.12 through the R6 pull-up node, CLK3=PHI2TTL, /CL... |
| `D6` | `DEC_PROM` | scan | validated owner dump 2026-07-13 uses physical RT4 address order A0-A7=5/6/7/4/3/2/1/15; board signals are BA15,BA14,BA13,BA12,BA11,PC2,PC3,PC4 respectively.... |
| `D7` | `LA3_GATE` | scan | complete sheet-1 full-resolution package census: section12,13->11 drives PROM_EN from two distinct unresolved-source boundaries; section1,2->3 remains a dest... |
| `D93` | `VG93_FDC` | mame+datasheet | .009 official (FDC) physical КР1818ВГ93 socket with Western Digital FD179X-01 primary-datasheet package contract: host, drive, separator, status, power, and... |

### placement/refdes

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `C35` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D60 remains assumed |
| `C36` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D61 remains assumed |
| `C37` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D62 remains assumed |
| `C38` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D63 remains assumed |
| `C39` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D64 remains assumed |
| `C40` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D65 remains assumed |
| `C41` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D66 remains assumed |
| `C42` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D67 remains assumed |
| `C43` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D15 remains assumed |
| `C44` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D17 remains assumed |
| `C45` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D19 remains assumed |
| `C46` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D21 remains assumed |
| `C47` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D5 remains assumed |
| `C48` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D1 remains assumed |
| `C49` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D10 remains assumed |
| `C50` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D11 remains assumed |
| `C51` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D26 remains assumed |
| `C52` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D27 remains assumed |
| `C53` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D54 remains assumed |
| `C54` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D55 remains assumed |
| `C55` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D57 remains assumed |
| `C56` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D23 remains assumed |
| `C57` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D29 remains assumed |
| `C58` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D6 remains assumed |
| `C59` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D7 remains assumed |
| `C60` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D44 remains assumed |
| `C61` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D46 remains assumed |
| `C62` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D48 remains assumed |
| `C63` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D40 remains assumed |
| `C64` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D38 remains assumed |
| `C65` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D35 remains assumed |
| `C66` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D42 remains assumed |
| `C67` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D58 remains assumed |
| `C68` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D14 remains assumed |
| `C69` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D3 remains assumed |
| `C70` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D71 remains assumed |
| `C71` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D79 remains assumed |
| `C72` | `C_KM` | scan | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D87 remains assumed |

### placement/value

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `C99` | `C_KM` | scan | sheet-1 D7/D9 RC decode path native 5150x3603 sheet-1 review proves pin1 on V3_RC; the pin2 plate is visibly drawn without an outgoing conductor, so its phys... |

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
| `D3` | `3, 4, 5, 6` |
| `D30` | `6, 9` |
| `D35` | `1, 2, 5, 6, 8, 9` |
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
| `D56` | `1, 9, 13` |
| `D59` | `5, 6` |
| `D93` | `1` |

## Net-Level Source Risks

This mirrors the net-risk surface used by
`docs/replica-bringup-verification-points.md`, but keeps it in the
same fidelity ledger as the chip provenance gaps.

| Net | Category | Endpoints | Source risk |
| --- | --- | --- | --- |
| `C99_FAR` | logic/source | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity bounda... |
| `CPU_WAIT_STATUS` | logic/source | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread |
| `CS_FDC` | PROM/decode | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch |
| `D100_OE_BOUNDARY` | logic/source | `D100.9` | July-2026 two-sided local-package registration identifies D100 OE_N pin9; component copper ends at an isolated circular landing and the projected backside po... |
| `D100_T_BOUNDARY` | logic/source | `D100.11` | July-2026 two-sided local-package registration identifies D100 direction pin11; its component-side continuation is obscured by the factory wire/tape bundle,... |
| `D101_A0_BOUNDARY` | logic/source | `D101.14` | July-2026 validated component and solder package fits identify D101 К555КП12 pin14 A0; no remote destination is proved, so this remains a measurement boundary |
| `D101_A1_BOUNDARY` | logic/source | `D101.2` | July-2026 validated component and solder package fits identify D101 К555КП12 pin2 A1; no remote destination is proved, so this remains a measurement boundary |
| `D101_D00_BOUNDARY` | logic/source | `D101.6` | July-2026 validated component and solder package fits identify D101 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary |
| `D101_D01_BOUNDARY` | logic/source | `D101.5` | July-2026 validated component and solder package fits identify D101 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary |
| `D101_D02_BOUNDARY` | logic/source | `D101.4` | July-2026 validated component and solder package fits identify D101 К555КП12 pin4 D02; no remote destination is proved, so this remains a measurement boundary |
| `D101_D03_BOUNDARY` | logic/source | `D101.3` | July-2026 validated component and solder package fits identify D101 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary |
| `D101_D10_BOUNDARY` | logic/source | `D101.10` | July-2026 validated component and solder package fits identify D101 К555КП12 pin10 D10; no remote destination is proved, so this remains a measurement boundary |
| `D101_D11_BOUNDARY` | logic/source | `D101.11` | July-2026 validated component and solder package fits identify D101 К555КП12 pin11 D11; no remote destination is proved, so this remains a measurement boundary |
| `D101_D12_BOUNDARY` | logic/source | `D101.12` | July-2026 validated component and solder package fits identify D101 К555КП12 pin12 D12; no remote destination is proved, so this remains a measurement boundary |
| `D101_D13_BOUNDARY` | logic/source | `D101.13` | July-2026 validated component and solder package fits identify D101 К555КП12 pin13 D13; no remote destination is proved, so this remains a measurement boundary |
| `D101_OE0_BOUNDARY` | logic/source | `D101.1` | July-2026 validated component and solder package fits identify D101 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary |
| `D101_OE1_BOUNDARY` | logic/source | `D101.15` | July-2026 validated component and solder package fits identify D101 К555КП12 pin15 OE1_N; no remote destination is proved, so this remains a measurement boun... |
| `D101_Q0_BOUNDARY` | logic/source | `D101.7` | July-2026 validated component and solder package fits identify D101 К555КП12 pin7 Q0; no remote destination is proved, so this remains a measurement boundary |
| `D101_Q1_BOUNDARY` | logic/source | `D101.9` | July-2026 validated component and solder package fits identify D101 К555КП12 pin9 Q1; no remote destination is proved, so this remains a measurement boundary |
| `D102_A1N_BOUNDARY` | logic/source | `D102.1` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_A2N_BOUNDARY` | logic/source | `D102.9` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_B1_BOUNDARY` | logic/source | `D102.2` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin2 B; no remote destination is proved, so this remains a measurement boundary |
| `D102_B2_BOUNDARY` | logic/source | `D102.10` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement boundary |
| `D102_C1_BOUNDARY` | logic/source | `D102.14` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement boundary |
| `D102_C2_BOUNDARY` | logic/source | `D102.6` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement boundary |
| `D102_CLR1_BOUNDARY` | logic/source | `D102.3` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin3 CLR_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_CLR2_BOUNDARY` | logic/source | `D102.11` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boun... |
| `D102_Q1N_BOUNDARY` | logic/source | `D102.4` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_Q1_BOUNDARY` | logic/source | `D102.13` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary |
| `D102_Q2N_BOUNDARY` | logic/source | `D102.12` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary |
| `D102_Q2_BOUNDARY` | logic/source | `D102.5` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary |
| `D102_RC1_BOUNDARY` | logic/source | `D102.15` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measurement boundary |
| `D102_RC2_BOUNDARY` | logic/source | `D102.7` | July-2026 validated component and solder package fits identify D102 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement boundary |
| `D105_GATE1_Y` | logic/source | `D105.3` | traced sheet-1: D105 gate pins 1,2 -> 3; output destination remains unread |
| `D106_BO_BOUNDARY` | logic/source | `D106.13` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin13 BO; no remote destination is proved, so this remains a measurement boundary |
| `D106_CLR_BOUNDARY` | logic/source | `D106.14` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin14 CLR; no remote destination is proved, so this remains a measurement boundary |
| `D106_CO_BOUNDARY` | logic/source | `D106.12` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin12 CO; no remote destination is proved, so this remains a measurement boundary |
| `D106_D0_BOUNDARY` | logic/source | `D106.15` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin15 D0; no remote destination is proved, so this remains a measurement boundary |
| `D106_D1_BOUNDARY` | logic/source | `D106.1` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin1 D1; no remote destination is proved, so this remains a measurement boundary |
| `D106_D2_BOUNDARY` | PROM/decode | `D106.10` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin10 D2 while the solder end is rail-obscured; no remote destination is proved, so this remains a... |
| `D106_D3_BOUNDARY` | logic/source | `D106.9` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin9 D3 while the solder end is rail-obscured; no remote destination is proved, so this remains a m... |
| `D106_DOWN_BOUNDARY` | logic/source | `D106.4` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin4 DOWN; no remote destination is proved, so this remains a measurement boundary |
| `D106_LOAD_BOUNDARY` | logic/source | `D106.11` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin11 LOAD_N; no remote destination is proved, so this remains a measurement boun... |
| `D106_Q0_BOUNDARY` | logic/source | `D106.3` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin3 Q0; no remote destination is proved, so this remains a measurement boundary |
| `D106_Q1_BOUNDARY` | logic/source | `D106.2` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin2 Q1; no remote destination is proved, so this remains a measurement boundary |
| `D106_Q2_BOUNDARY` | logic/source | `D106.6` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin6 Q2; no remote destination is proved, so this remains a measurement boundary |
| `D106_Q3_BOUNDARY` | logic/source | `D106.7` | July-2026 corrected component fit identifies D106 К555ИЕ7 pin7 Q3 while the solder end is rail-obscured; the candidate FDC clock relation is unproved, so thi... |
| `D106_UP_BOUNDARY` | logic/source | `D106.5` | July-2026 corrected component and solder package fits identify D106 К555ИЕ7 pin5 UP; no remote destination is proved, so this remains a measurement boundary |
| `D11_RXRDY_BOUNDARY` | logic/source | `D11.14` | sheet-1 full-resolution USART package census identifies D11 pin14 RXRDY; no target-revision destination is drawn after rejecting the older IR0 mapping, so th... |
| `D11_TXRDY_BOUNDARY` | logic/source | `D11.15` | sheet-1 full-resolution USART package census identifies D11 pin15 TXRDY; no target-revision destination is drawn after rejecting the older IR1 mapping, so th... |
| `D13_I3_BOUNDARY` | logic/source | `D13.3` | sheet-1 full-resolution: D13 ТЛ2 input pin3 drives the proved pin4 conductor to D105.2 and D11.20, but the pin3 origin is unread and remains a measurement bo... |
| `D14_I2_BOUNDARY` | video/analog | `D14.2` | sheet-1 full-resolution К170АП2 package census identifies D14 input pin2; its remote serial-interface source is unread and remains a measurement boundary |
| `D14_O7_BOUNDARY` | video/analog | `D14.7` | sheet-1 full-resolution К170АП2 package census identifies D14 output pin7; its remote serial-interface destination is unread and remains a measurement boundary |
| `D25_T` | logic/source | `D7.6, D25.11` | traced sheet-1 native 5150x3603 review (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaroun... |
| `D26_PA6_PREN_BOUNDARY` | logic/source | `D26.38` | sheet-1 full-resolution: D26 PA6 pin38 leaves on the conductor labeled PREN with off-sheet marker (3); the far destination is unread, so this remains a measu... |
| `D26_PB4_BOUNDARY` | logic/source | `D26.22` | sheet-1 full-resolution: D26 PB4 pin22 enters the E8 CONTRDAT selector region, but the absent switch symbol prevents a proved remote endpoint, so this remain... |
| `D26_PC0_BOUNDARY` | memory/timing | `D26.14` | sheet-1 full-resolution: D26 PC0 pin14 leaves the PPI into the cassette-control gate region, but its unique next hop is not established and remains a measure... |
| `D26_PC1_BOUNDARY` | memory/timing | `D26.15` | sheet-1 full-resolution: D26 PC1 pin15 leaves the PPI into the cassette-control gate region, but its unique next hop is not established and remains a measure... |
| `D26_PC5_RN_IN` | logic/source | `D26.12, D28.3` | cross-source closure: .006 sheet-1 draws the uninterrupted D26 PC5/pin12 mode conductor into D28 К155ЛН3 input pin3, whose paired open-collector output pin4... |
| `D26_PC6_STOP_IN` | logic/source | `D26.11, D28.1` | cross-source closure: .006 sheet-1 draws the uninterrupted D26 PC6/pin11 mode conductor into D28 К155ЛН3 input pin1, whose paired open-collector output pin2... |
| `D29_AIN0_BOUNDARY` | logic/source | `D29.1` | sheet-1 full-resolution system-bus buffer census identifies D29 AIN0 pin1; its remote source is unread and remains a measurement boundary |
| `D29_AIN1_BOUNDARY` | logic/source | `D29.2` | sheet-1 full-resolution system-bus buffer census identifies D29 AIN1 pin2; its remote source is unread and remains a measurement boundary |
| `D29_AIN2_BOUNDARY` | logic/source | `D29.3` | sheet-1 full-resolution system-bus buffer census identifies D29 AIN2 pin3; its remote source is unread and remains a measurement boundary |
| `D29_AIN5_BOUNDARY` | logic/source | `D29.6` | sheet-1 full-resolution system-bus buffer census identifies D29 AIN5 pin6; its remote source is unread and remains a measurement boundary |
| `D30_CLK2_BOUNDARY` | clock/I/O | `D30.11` | sheet-1 full-resolution: D30 second flip-flop clock pin11 has a drawn conductor whose unique source is unread, so it remains a measurement boundary |
| `D30_Q2N_BOUNDARY` | logic/source | `D30.8` | sheet-1 full-resolution: D30 second flip-flop inverted output pin8 has a drawn conductor whose unique destination is unread, so it remains a measurement boun... |
| `D34_A1_TAG2` | logic/source | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in... |
| `D34_SIG` | video/analog | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D36_CAS_IN` | memory/timing | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and o... |
| `D56_Q2N_TAG16` | memory/timing | `D56.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D56 second-section Q2_N pin12 leaves east on conductor code 16; the former D34.10 merge is dispr... |
| `D58_STB_TAG5` | logic/source | `D58.11` | scan sheet-2: D58 ИР82 strobe pin 11 runs continuously left to timing-bundle conductor tag 5; unique remote source not established |
| `D59_O10_TAG10` | sound/analog | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10... |
| `D6_MEM_SELECT_N` | PROM/decode | `D6.11, D6.12, D8.15, R11.2, D92.5, R12.2, ... (+1)` | owner continuity 2026-07-13 joins D6.11, D6.12, and D13.12 on the physical .009 board, superseding the older-sheet independent RAM_SEL/ROM_SEL interpretation... |
| `D6_V_ENABLE` | PROM/decode | `D6.13, D6.14` | sheet-1 full-resolution: D6 РТ4 enable pins V1/pin13 and V2/pin14 are visibly bridged; upstream conductor origin remains unread and the former D7.11 merge is... |
| `D7_A1_BOUNDARY` | logic/source | `D7.12` | sheet-1 full-resolution: D7 first-gate pin12 has a drawn conductor, but its unique origin is not established after correcting the false IOWR assignment, so i... |
| `D7_A3_BOUNDARY` | logic/source | `D7.4` | sheet-1 D7 section 5,4->6: pin4 leaves west as a distinct conductor; next hop is unread in the available scan |
| `D7_B1_BOUNDARY` | logic/source | `D7.13` | sheet-1 full-resolution: D7 first-gate pin13 has a drawn conductor, but its unique origin is not established after correcting the false IORD assignment, so i... |
| `D7_B3_BOUNDARY` | logic/source | `D7.5` | sheet-1 D7 section 5,4->6: pin5 leaves west as a distinct conductor; next hop is unread in the available scan |
| `D7_Y2_BOUNDARY` | memory/timing | `D7.3` | sheet-1 full-resolution package census: D7 section pins1/2 receive the D92.13 wire-11 boundary and MEMW/wire19; NAND output pin3 remains a measurement bounda... |
| `D7_Y4_TAG8` | logic/source | `D7.8` | sheet-1 full-resolution: D7 fourth NAND output pin8 leaves on the conductor explicitly marked 8; its unique far destination is not established, so tag 8 rema... |
| `D93_CLK_BOUNDARY` | FDC owner-continuity | `D93.24` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin24 CLK; the candidate D106 divider relation is not proved, so this remains a me... |
| `D93_DIRC_BOUNDARY` | FDC owner-continuity | `D93.16` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin16 DIRC; remote drive-interface continuity is not proved, so this remains a mea... |
| `D93_EARLY_BOUNDARY` | FDC owner-continuity | `D93.17` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin17 EARLY; remote drive-interface continuity is not proved, so this remains a me... |
| `D93_HLD_BOUNDARY` | FDC owner-continuity | `D93.28` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin28 HLD; remote drive-interface continuity is not proved, so this remains a meas... |
| `D93_HLT_BOUNDARY` | FDC owner-continuity | `D93.23` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin23 HLT; remote drive-interface continuity is not proved, so this remains a meas... |
| `D93_INDEX_BOUNDARY` | FDC owner-continuity | `D93.35` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin35 INDEX; remote drive-status continuity is not proved, so this remains a measu... |
| `D93_LATE_BOUNDARY` | FDC owner-continuity | `D93.18` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin18 LATE; remote drive-interface continuity is not proved, so this remains a mea... |
| `D93_MR_BOUNDARY` | FDC owner-continuity | `D93.19` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin19 MR_N; remote reset continuity is not proved, so this remains a measurement b... |
| `D93_RAW_READ_BOUNDARY` | FDC owner-continuity | `D93.27` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin27 RAW_READ; remote separator continuity is not proved, so this remains a measu... |
| `D93_RCLK_BOUNDARY` | FDC owner-continuity | `D93.26` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin26 RCLK; remote separator continuity is not proved, so this remains a measureme... |
| `D93_READY_BOUNDARY` | FDC owner-continuity | `D93.32` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin32 READY; remote drive-status continuity is not proved, so this remains a measu... |
| `D93_RG_BOUNDARY` | FDC owner-continuity | `D93.25` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin25 RG; remote separator continuity is not proved, so this remains a measurement... |
| `D93_STEP_BOUNDARY` | FDC owner-continuity | `D93.15` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin15 STEP; remote drive-interface continuity is not proved, so this remains a mea... |
| `D93_TEST_BOUNDARY` | FDC owner-continuity | `D93.22` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin22 TEST; remote strap continuity is not proved, so this remains a measurement b... |
| `D93_TG43_BOUNDARY` | FDC owner-continuity | `D93.29` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin29 TG43; remote drive-interface continuity is not proved, so this remains a mea... |
| `D93_TR00_BOUNDARY` | FDC owner-continuity | `D93.34` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin34 TR00; remote drive-status continuity is not proved, so this remains a measur... |
| `D93_VDD12_BOUNDARY` | FDC owner-continuity | `D93.40` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin40 VDD_12V; the +12V feed is not proved and remains a power-safety measurement... |
| `D93_WDATA_BOUNDARY` | FDC owner-continuity | `D93.31` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin31 WDATA; remote drive-interface continuity is not proved, so this remains a me... |
| `D93_WF_VFOE_BOUNDARY` | FDC owner-continuity | `D93.33` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin33 WF_VFOE; remote drive/separator continuity is not proved, so this remains a... |
| `D93_WG_BOUNDARY` | FDC owner-continuity | `D93.30` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin30 WG; remote drive-interface continuity is not proved, so this remains a measu... |
| `D93_WPRT_BOUNDARY` | FDC owner-continuity | `D93.36` | July-2026 two-sided physical КР1818ВГ93 socket registration identifies D93 pin36 WPRT; remote drive-status continuity is not proved, so this remains a measur... |
| `D94_D3` | PROM/decode | `D94.4` | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) m... |
| `D94_D4` | PROM/decode | `D94.5` | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary |
| `D94_D5` | PROM/decode | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary |
| `D94_D6` | PROM/decode | `D94.7` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because... |
| `D94_D7` | PROM/decode | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary |
| `D94_EN_BOUNDARY` | PROM/decode | `D94.15` | July-2026 registered component/solder local fits identify D94 enable pin 15 and exposed fanout, but the onward source cannot be uniquely followed across the... |
| `D95_A0_BOUNDARY` | logic/source | `D95.14` | July-2026 validated component and solder package fits identify D95 К555КП12 pin14 A0; no remote destination is proved, so this remains a measurement boundary |
| `D95_A1_BOUNDARY` | logic/source | `D95.2` | July-2026 validated component and solder package fits identify D95 К555КП12 pin2 A1; no remote destination is proved, so this remains a measurement boundary |
| `D95_D00_BOUNDARY` | logic/source | `D95.6` | July-2026 validated component and solder package fits identify D95 К555КП12 pin6 D00; no remote destination is proved, so this remains a measurement boundary |
| `D95_D01_BOUNDARY` | logic/source | `D95.5` | July-2026 validated component and solder package fits identify D95 К555КП12 pin5 D01; no remote destination is proved, so this remains a measurement boundary |
| `D95_D02_BOUNDARY` | logic/source | `D95.4` | July-2026 validated component and solder package fits identify D95 К555КП12 pin4 D02; no remote destination is proved, so this remains a measurement boundary |
| `D95_D03_BOUNDARY` | logic/source | `D95.3` | July-2026 validated component and solder package fits identify D95 К555КП12 pin3 D03; no remote destination is proved, so this remains a measurement boundary |
| `D95_D10_BOUNDARY` | logic/source | `D95.10` | July-2026 validated component and solder package fits identify D95 К555КП12 pin10 D10; no remote destination is proved, so this remains a measurement boundary |
| `D95_D11_BOUNDARY` | logic/source | `D95.11` | July-2026 validated component and solder package fits identify D95 К555КП12 pin11 D11; no remote destination is proved, so this remains a measurement boundary |
| `D95_D12_BOUNDARY` | logic/source | `D95.12` | July-2026 validated component and solder package fits identify D95 К555КП12 pin12 D12; no remote destination is proved, so this remains a measurement boundary |
| `D95_D13_BOUNDARY` | logic/source | `D95.13` | July-2026 validated component and solder package fits identify D95 К555КП12 pin13 D13; no remote destination is proved, so this remains a measurement boundary |
| `D95_OE0_BOUNDARY` | logic/source | `D95.1` | July-2026 validated component and solder package fits identify D95 К555КП12 pin1 OE0_N; no remote destination is proved, so this remains a measurement boundary |
| `D95_OE1_BOUNDARY` | logic/source | `D95.15` | July-2026 validated component and solder package fits identify D95 К555КП12 pin15 OE1_N; no remote destination is proved, so this remains a measurement boundary |
| `D95_Q0_BOUNDARY` | logic/source | `D95.7` | July-2026 validated component and solder package fits identify D95 К555КП12 pin7 Q0; no remote destination is proved, so this remains a measurement boundary |
| `D95_Q1_BOUNDARY` | logic/source | `D95.9` | July-2026 validated component and solder package fits identify D95 К555КП12 pin9 Q1; no remote destination is proved, so this remains a measurement boundary |
| `D96_CLK1_BOUNDARY` | clock/I/O | `D96.3` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin3 CLK1; no remote destination is proved, so this remains a me... |
| `D96_CLK2_BOUNDARY` | clock/I/O | `D96.11` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin11 CLK2; no remote destination is proved, so this remains a m... |
| `D96_CLR1_BOUNDARY` | logic/source | `D96.1` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin1 CLR1_N; no remote destination is proved, so this remains a... |
| `D96_CLR2_BOUNDARY` | logic/source | `D96.13` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin13 CLR2_N; no remote destination is proved, so this remains a... |
| `D96_D1_BOUNDARY` | logic/source | `D96.2` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin2 D1; no remote destination is proved, so this remains a meas... |
| `D96_D2_BOUNDARY` | PROM/decode | `D96.12` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin12 D2; no remote destination is proved, so this remains a mea... |
| `D96_PRE1_BOUNDARY` | logic/source | `D96.4` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin4 PRE1_N; no remote destination is proved, so this remains a... |
| `D96_PRE2_BOUNDARY` | logic/source | `D96.10` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin10 PRE2_N; no remote destination is proved, so this remains a... |
| `D96_Q1N_BOUNDARY` | logic/source | `D96.6` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin6 Q1_N; no remote destination is proved, so this remains a me... |
| `D96_Q1_BOUNDARY` | logic/source | `D96.5` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin5 Q1; no remote destination is proved, so this remains a meas... |
| `D96_Q2_BOUNDARY` | logic/source | `D96.9` | July-2026 full component registration and reflected solder package fit identify D96 КМ555ТМ2 pin9 Q2; no remote destination is proved, so this remains a meas... |
| `D97_A1N_BOUNDARY` | logic/source | `D97.1` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_A2N_BOUNDARY` | logic/source | `D97.9` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_B1_BOUNDARY` | logic/source | `D97.2` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin2 B; no remote destination is proved, so this remains a measurement boundary |
| `D97_B2_BOUNDARY` | logic/source | `D97.10` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement boundary |
| `D97_C1_BOUNDARY` | logic/source | `D97.14` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement boundary |
| `D97_C2_BOUNDARY` | logic/source | `D97.6` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement boundary |
| `D97_CLR1_BOUNDARY` | logic/source | `D97.3` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin3 CLR_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_CLR2_BOUNDARY` | logic/source | `D97.11` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_Q1N_BOUNDARY` | logic/source | `D97.4` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_Q1_BOUNDARY` | logic/source | `D97.13` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement boundary |
| `D97_Q2N_BOUNDARY` | logic/source | `D97.12` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measurement boundary |
| `D97_Q2_BOUNDARY` | logic/source | `D97.5` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement boundary |
| `D97_RC1_BOUNDARY` | logic/source | `D97.15` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measurement boundary |
| `D97_RC2_BOUNDARY` | logic/source | `D97.7` | July-2026 validated component and solder package fits identify D97 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement boundary |
| `D98_A1_BOUNDARY` | logic/source | `D98.2` | July-2026 validated package registration identifies D98 К155ЛП11 pin2 A1; no remote destination is proved, so this remains a measurement boundary |
| `D98_A2_BOUNDARY` | logic/source | `D98.4` | July-2026 validated package registration identifies D98 К155ЛП11 pin4 A2; no remote destination is proved, so this remains a measurement boundary |
| `D98_A3_BOUNDARY` | logic/source | `D98.6` | July-2026 validated package registration identifies D98 К155ЛП11 pin6 A3; no remote destination is proved, so this remains a measurement boundary |
| `D98_A4_BOUNDARY` | logic/source | `D98.10` | July-2026 validated package registration identifies D98 К155ЛП11 pin10 A4; no remote destination is proved, so this remains a measurement boundary |
| `D98_A5_BOUNDARY` | logic/source | `D98.12` | July-2026 validated package registration identifies D98 К155ЛП11 pin12 A5; no remote destination is proved, so this remains a measurement boundary |
| `D98_A6_BOUNDARY` | logic/source | `D98.14` | July-2026 validated package registration identifies D98 К155ЛП11 pin14 A6; no remote destination is proved, so this remains a measurement boundary |
| `D98_OE14_BOUNDARY` | logic/source | `D98.1` | July-2026 validated package registration identifies D98 К155ЛП11 pin1 OE14_N; no remote destination is proved, so this remains a measurement boundary |
| `D98_OE56_BOUNDARY` | logic/source | `D98.15` | July-2026 validated package registration identifies D98 К155ЛП11 pin15 OE56_N; no remote destination is proved, so this remains a measurement boundary |
| `D98_Y2_BOUNDARY` | logic/source | `D98.5` | July-2026 validated package registration identifies D98 К155ЛП11 pin5 Y2; no remote destination is proved, so this remains a measurement boundary |
| `D98_Y4_BOUNDARY` | logic/source | `D98.9` | July-2026 validated package registration identifies D98 К155ЛП11 pin9 Y4; no remote destination is proved, so this remains a measurement boundary |
| `D98_Y5_BOUNDARY` | logic/source | `D98.11` | July-2026 validated package registration identifies D98 К155ЛП11 pin11 Y5; no remote destination is proved, so this remains a measurement boundary |
| `D98_Y6_BOUNDARY` | logic/source | `D98.13` | July-2026 validated package registration identifies D98 К155ЛП11 pin13 Y6; no remote destination is proved, so this remains a measurement boundary |
| `D99_A1N_BOUNDARY` | logic/source | `D99.1` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin1 A_N; no remote destination is proved, so this remains a measurement... |
| `D99_A2N_BOUNDARY` | logic/source | `D99.9` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin9 A2_N; no remote destination is proved, so this remains a measuremen... |
| `D99_B2_BOUNDARY` | logic/source | `D99.10` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin10 B2; no remote destination is proved, so this remains a measurement... |
| `D99_C1_BOUNDARY` | logic/source | `D99.14` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin14 C1; no remote destination is proved, so this remains a measurement... |
| `D99_C2_BOUNDARY` | logic/source | `D99.6` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin6 C2; no remote destination is proved, so this remains a measurement... |
| `D99_CLR2_BOUNDARY` | logic/source | `D99.11` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin11 CLR2_N; no remote destination is proved, so this remains a measure... |
| `D99_Q1N_BOUNDARY` | logic/source | `D99.4` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin4 Q_N; no remote destination is proved, so this remains a measurement... |
| `D99_Q1_BOUNDARY` | logic/source | `D99.13` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin13 Q; no remote destination is proved, so this remains a measurement... |
| `D99_Q2N_BOUNDARY` | logic/source | `D99.12` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin12 Q2_N; no remote destination is proved, so this remains a measureme... |
| `D99_Q2_BOUNDARY` | logic/source | `D99.5` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin5 Q2; no remote destination is proved, so this remains a measurement... |
| `D99_RC1_BOUNDARY` | logic/source | `D99.15` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin15 RC1; no remote destination is proved, so this remains a measuremen... |
| `D99_RC2_BOUNDARY` | logic/source | `D99.7` | July-2026 validated component and solder package registration identifies D99 К155АГ3 pin7 RC2; no remote destination is proved, so this remains a measurement... |
| `FDC_DDEN` | FDC owner-continuity | `D26.13, D93.37, D6.15, D28.9` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15 and directly into D28 input pin9, whose paired open-collector output pin8 is labeled -... |
| `FDC_DRQ` | FDC owner-continuity | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `FDC_INTRQ` | FDC owner-continuity | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `FRAME_INT` | memory/timing | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (... |
| `HF_OUT` | video/analog | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board... |
| `LATCH_B` | clock/I/O | `D40.11, D37.2, D54.9, D54.15, D54.18` | scan+mame; +D54 CLK0/1/2: the drawn 1MHz rail = the D40.QD /16 tap (HDL+MAME concur; rail tag read pending) |
| `MEM_MODE0` | PROM/decode | `D26.16, D6.2, D28.11` | traced sheet-1 full-resolution: D26 PC2/pin16 -> mode-bundle tag1 -> D6 A5/pin2 and directly into D28 input pin11, whose paired open-collector output pin10 i... |
| `MEM_MODE1` | PROM/decode | `D26.17, D6.1, D28.13` | traced sheet-1 full-resolution: D26 PC3/pin17 -> mode-bundle tag2 -> D6 A6/pin1 and directly into D28 input pin13, whose paired open-collector output pin12 i... |
| `PHI2TTL` | logic/source | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_... |
| `PIC_IR2_BOUNDARY` | logic/source | `D10.20` | scan sheet-1: D10 IR2 pin 20 has a distinct southbound conductor; far destination remains unread |
| `PIC_IR3_BOUNDARY` | logic/source | `D10.21` | scan sheet-1: D10 IR3 pin 21 has a distinct southbound conductor; far destination remains unread |
| `PIT_BAUD` | clock/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V... |
| `POF` | logic/source | `D26.10, D35.3` | cross-sheet source closure: sheet-1 D26 PPI0 PC7/pin10 leaves through mode-bundle tag6; sheet-2 labels the receiving conductor POF directly into D35 inverter... |
| `PROM_EN` | PROM/decode | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assu... |
| `R94_P2_BOUNDARY` | logic/source | `R94.2` | July-2026 registered component photo identifies the lower terminal of R94 220 ohm; only the upper terminal to D98.3 is proved and pin2 remains a measurement... |
| `RAIL_E` | memory/timing | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members... |
| `READY_PRE_N` | video/analog | `D30.4` | D30 section-A asynchronous preset pin4 remains a target-board continuity boundary after owner measurements moved R5 to D30.10/.12 |
| `REV` | PROM/decode | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder re... |
| `RF_RAIL` | video/analog | `VT3.3, C9.2, R72.2, C10.1, R73.1, C11.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed |
| `ROE` | PROM/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merg... |
| `S1_3_BOUNDARY` | logic/source | `S1.3` | ДГШ5.109.009 СБ and owner photos establish bracket-mounted SPDT S1 contacts 1 and 2; contact3 belongs to the off-board symbol union but its wire is not ident... |
| `SND_MIX` | video/analog | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `SSTB_N` | logic/source | `D30.1` | sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary |
| `TAPE_RUN_INT` | logic/source | `D10.22` | scan sheet-1: D10 IR4 pin 22 is explicitly labeled (3) TAPE RUN INT; sheet-3 source remains outside the modeled board boundary |
| `TIMING_TAG2` | logic/source | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's... |
| `V3_RC` | logic/source | `R17.1, C99.1, D9.6` | traced sheet-1 native 5150x3603 review: R17 top + C99 pin1/left plate + D9.6 share one junction; rail3 crosses above without a dot. RC-deglitched I/O strobe... |
| `VIDEO_OUT` | video/analog | `VT2.1, R65.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_... |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT3_BASE` | video/analog | `R68.2, R69.2, R70.2, R71.1, C13.1, VT3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `VT3_E` | video/analog | `VT3.1, R74.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT4_B` | video/analog | `R73.2, VT4.2, C10.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R73 4.7k drawn adjustable |
| `VT4_E` | video/analog | `VT4.1, R75.1, C14.1, C15.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `W_RAIL16` | memory/timing | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, ... (+27)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: th... |
| `X4_06_BOUNDARY` | logic/source | `AX406.1, X4.6` | .009 sheets4-5 wire32: physical board landing А X4:6 maps directly to bracket X4.6; circuit-side destination remains untraced |
| `X4_07_BOUNDARY` | logic/source | `AX407.1, X4.7` | .009 sheets4-5 wire33: physical board landing А X4:7 maps directly to bracket X4.7; circuit-side destination remains untraced |
| `X4_08_BOUNDARY` | logic/source | `AX408.1, X4.8` | .009 sheets4-5 wire34: physical board landing А X4:8 maps directly to bracket X4.8; circuit-side destination remains untraced |
| `X4_09_BOUNDARY` | logic/source | `AX409.1, X4.9` | .009 sheets4-5 wire35: physical board landing А X4:9 maps directly to bracket X4.9; circuit-side destination remains untraced |
| `X4_10_BOUNDARY` | logic/source | `AX410.1, X4.10` | .009 sheets4-5 wire36: physical board landing А X4:10 maps directly to bracket X4.10; circuit-side destination remains untraced |
| `X4_11_BOUNDARY` | logic/source | `AX411.1, X4.11` | .009 sheets4-5 wire37: physical board landing А X4:11 maps directly to bracket X4.11; circuit-side destination remains untraced |
| `X4_12_BOUNDARY` | logic/source | `AX412.1, X4.12` | .009 sheets4-5 wire38: physical board landing А X4:12 maps directly to bracket X4.12; circuit-side destination remains untraced |
| `X4_13_BOUNDARY` | logic/source | `AX413.1, X4.13` | .009 sheets4-5 wire39: physical board landing А X4:13 maps directly to bracket X4.13; circuit-side destination remains untraced |
| `X4_14_BOUNDARY` | logic/source | `AX414.1, X4.14` | .009 sheets4-5 wire40: physical board landing А X4:14 maps directly to bracket X4.14; circuit-side destination remains untraced |
| `X4_15_BOUNDARY` | logic/source | `AX415.1, X4.15` | .009 sheets4-5 wire41: physical board landing А X4:15 maps directly to bracket X4.15; circuit-side destination remains untraced |
| `X4_16_BOUNDARY` | logic/source | `AX416.1, X4.16` | .009 sheets4-5 wire42: physical board landing А X4:16 maps directly to bracket X4.16; circuit-side destination remains untraced |
| `X4_17_BOUNDARY` | logic/source | `AX417.1, X4.17` | .009 sheets4-5 wire43: physical board landing А X4:17 maps directly to bracket X4.17; circuit-side destination remains untraced |
| `X4_18_BOUNDARY` | logic/source | `AX418.1, X4.18` | .009 sheets4-5 wire44: physical board landing А X4:18 maps directly to bracket X4.18; circuit-side destination remains untraced |
| `X4_19_BOUNDARY` | logic/source | `AX419.1, X4.19` | .009 sheets4-5 wire45: physical board landing А X4:19 maps directly to bracket X4.19; circuit-side destination remains untraced |
| `X4_20_BOUNDARY` | logic/source | `AX420.1, X4.20` | .009 sheets4-5 wire46: physical board landing А X4:20 maps directly to bracket X4.20; circuit-side destination remains untraced |
| `X4_21_BOUNDARY` | logic/source | `AX421.1, X4.21` | .009 sheets4-5 wire47: physical board landing А X4:21 maps directly to bracket X4.21; circuit-side destination remains untraced |
| `X4_22_BOUNDARY` | logic/source | `AX422.1, X4.22` | .009 sheets4-5 wire48: physical board landing А X4:22 maps directly to bracket X4.22; circuit-side destination remains untraced |
| `X4_23_BOUNDARY` | logic/source | `AX423.1, X4.23` | .009 sheets4-5 wire49: physical board landing А X4:23 maps directly to bracket X4.23; circuit-side destination remains untraced |
| `X4_FF_N` | logic/source | `D28.8, AX401.1, X4.1` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin8 -FF and sends it to X4.1; .009 sheets4-5 preserve a direct 23-condu... |
| `X4_PLAY_N` | logic/source | `D28.12, AX403.1, X4.3` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin12 -PLAY and sends it to X4.3; .009 sheets4-5 preserve a direct 23-co... |
| `X4_REC_N` | logic/source | `D28.10, AX402.1, X4.2` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin10 -REC and sends it to X4.2; .009 sheets4-5 preserve a direct 23-con... |
| `X4_RN_N` | logic/source | `D28.4, AX404.1, X4.4` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin4 -RN and sends it to X4.4; .009 sheets4-5 preserve a direct 23-condu... |
| `X4_STOP_N` | logic/source | `D28.2, AX405.1, X4.5` | cross-revision harness reconstruction: .006 sheet-1 labels D28 open-collector output pin2 -STOP and sends it to X4.5; .009 sheets4-5 preserve a direct 23-con... |
| `XTAL16M` | logic/source | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin1... |

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
