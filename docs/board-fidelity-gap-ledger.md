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
- Chips modeled: `277`
- Nets modeled: `369`
- Chip-level fidelity gaps: `59`
- Net-level source-risk gaps: `49`
- Documented intentional no-connect pins: `26`

## Chip Provenance Types

| Provenance type | Chips |
| --- | ---: |
| .009 assembly drawing + owner photo | 1 |
| datasheet | 1 |
| factory X3 cable table + registered owner photos | 12 |
| factory assembly drawing + owner photo | 1 |
| factory power-cable table | 4 |
| factory wire table | 14 |
| factory wire table + registered two-sided owner photos | 1 |
| mame+datasheet | 1 |
| photo | 4 |
| prom | 1 |
| scan | 230 |
| scan + assembly drawing + registered owner photo | 2 |
| scan + factory assembly wire table | 3 |
| scan + registered owner photo | 1 |
| wire | 1 |

## Gap Categories

| Category | Chip gaps | Net gaps |
| --- | ---: | ---: |
| FDC owner-continuity | 9 | 3 |
| PROM truth | 2 | 0 |
| PROM/decode | 0 | 18 |
| clock/I/O | 0 | 4 |
| logic/source | 8 | 8 |
| memory/timing | 0 | 5 |
| placement/refdes | 38 | 0 |
| video/analog | 0 | 11 |
| video/timing | 2 | 0 |

## Chip-Level Gaps

These are package/source/provenance gaps, not necessarily routed-copper
failures. Large repeated groups, such as unpopulated DRAM sockets and
decoupling capacitors, are still listed because they affect faithful
parts placement and Tier-3 reproduction.

### FDC owner-continuity

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D101` | `KP12_MUX` | scan | .009 official FDC population identifies К555КП12 К555КП12/74LS253 datasheet pinout; power pins 8/16 routed, mux signals await FDC continuity |
| `D102` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo К155АГ3 8901 marking; D102 is the rightmost lower-row one-shot 16-pin package and standard AG3 pinout; power pins 8/1... |
| `D106` | `IE7_CTR` | scan | .009 official FDC population; К555ИЕ7 identity and standard 74193-class pinout power pins 8/16 promoted; corrected component fit identifies package contacts,... |
| `D28` | `LN3_OC_INV` | scan | .009 official FDC population identifies К155ЛН3 К155ЛН3 datasheet pinout; power pins 7/14 routed, six inverter signal pairs await FDC continuity |
| `D95` | `KP12_MUX` | scan | .009 official FDC population identifies К555КП12 К555КП12/74LS253 datasheet pinout; power pins 8/16 routed, mux signals await FDC continuity |
| `D96` | `TM2_DFF` | scan | .009 official FDC population; КМ555ТМ2 identity and standard pinout power pins 7/14 promoted; all functional pins remain explicit FDC continuity boundaries |
| `D97` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo К155АГ3 8901 marking; D97 is the first lower-row one-shot right of D101 16-pin package and standard AG3 pinout; power... |
| `D98` | `LP11_BUF` | scan | .009 official FDC population identifies К155ЛП11 К155ЛП11/SN74367 datasheet pinout; power pins 8/16 routed, six buffer signals and two enables await FDC cont... |
| `D99` | `AG3_ONESHOT` | scan | .009 assembly position plus owner-photo 8901 one-shot package directly right of D95; cable obscures part of the К155АГ3 marking 16-pin package and standard A... |

### PROM truth

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D2` | `DEC_PROM` | scan | sheet-1: РТ4 D2 bus-arbitration/wait PROM; A3/pin4=VIDEO CYCLE=sheet-2 CAS rail 15, A5/pin2=-XACK boundary, A7/pin15=-WREQ boundary, V1/V2 pins13/14=GND, D0/... |
| `D94` | `RE3_PROM_092` | prom | .009 official; programming ДГШ5.106.092 (dump pending) РЕ3 pinout; A0-A4 = BA11-15 (same convention as D8); corrected July-2026 local pin fit traces D0/pin1-... |

### logic/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D1` | `CPU8080` | scan | complete КР580ВМ80А/8080 package contract: scan traces VSS pin2 to GND, VBB pin11 to locally derived -5V, VCC pin20 to +5V, and VDD pin28 to +12V; HOLD/pin13... |
| `D100` | `BUF8287` | datasheet | .009 official (5th ВА87 = FDC bus buffer) complete 8287 contract including VSS pin10 and +5V VCC pin20; OE/T gating remains assumed pending continuity |
| `D105` | `LA3_GATE` | scan | .009 official placement; sheet-1 .006 wait/MRD logic 12+13 tied from MRD -> 11 to D30.13; 1 from MWR and 2 from D13.4 -> 3 boundary; D2.12 -> 9 with named of... |
| `D30` | `TM2_DFF` | scan | .009 official; assembly drawing position and sheet-1 READY circuit section A traced: /PRE4 and D2 via R5/R6 pullups, CLK3=PHI2TTL, /CLR1=-SSTB boundary, Q5->... |
| `D35` | `CLK_PHASE` | scan | К155ЛН5 standard hex-inverter package contract; scan proves phase sections 11->10 (Φ1) and 13->12 (Φ2/Φ2TTL), while D35.4 is already traced to R39.1/VID_MIX2... |
| `D42` | `IR16` | scan | scan + К155ИР16/74295 pin contract: parallel outputs QA/QB/QC/QD = pins 13/12/11/10; only QD is used by the serializer chain, other output destinations/NC st... |
| `D43` | `IR16` | scan | scan + К155ИР16/74295 pin contract: parallel outputs QA/QB/QC/QD = pins 13/12/11/10; only QD is used by the serializer chain, other output destinations/NC st... |
| `D93` | `VG93_FDC` | mame+datasheet | .009 official (FDC) Western Digital FD179X-01 primary datasheet complete package contract: host, step/precompensation, separator, head-load, drive-status, wr... |

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

### video/timing

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D41` | `IR16` | scan | sheet-2 LATCH chain: ИР16 D41, outputs QB(12)/QA(13); standard К155ИР16/74295 outputs QC/pin11 and QD/pin10 are explicit unresolved functional endpoints; inp... |
| `D53` | `RASCAS_DEC` | scan | ИД7/74138 complete standard package contract; sheet-2 proves A/B<-E2/E3 jumpers (D52 mux vs Φ1/Φ2), C=GND, G1(6)=VID_CPU_SEL, and Y0-Y3=15/14/13/12 through R... |

## Unnetted Functional Pins

The full PCB endpoint coverage gate checks every modeled net endpoint,
but it cannot check package pins that are still deliberately absent
from `kicad/juku.board.json` nets. These rows expose the remaining
functional pins on non-placement chip gaps that still need scan,
continuity, PROM-dump, or implementation evidence before the board
model is historical-source-complete.

| Ref | Category | Unnetted modeled pins |
| --- | --- | --- |
| `D100` | logic/source | `9:OE_N, 11:T` |
| `D101` | FDC owner-continuity | `1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N` |
| `D102` | FDC owner-continuity | `1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` |
| `D106` | FDC owner-continuity | `1:D1, 2:Q1, 3:Q0, 4:DOWN, 5:UP, 6:Q2, 7:Q3, 9:D3, 10:D2, 11:LOAD_N, 12:CO, 13:BO, 14:CLR, 15:D0` |
| `D28` | FDC owner-continuity | `1:A1, 2:Y1, 3:A2, 4:Y2, 5:A3, 6:Y3, 8:Y4, 9:A4, 10:Y5, 11:A5, 12:Y6, 13:A6` |
| `D30` | logic/source | `8:Q2_N, 11:CLK2` |
| `D35` | logic/source | `1:I1, 2:O2, 3:I3, 5:I5, 6:O6, 8:O8, 9:I9` |
| `D41` | video/timing | `1:DS, 2:A, 3:B, 4:C, 5:D, 6:LD, 8:G, 9:CK, 10:QD, 11:QC` |
| `D42` | logic/source | `8:G, 11:QC, 12:QB, 13:QA` |
| `D43` | logic/source | `1:DS, 8:G, 11:QC, 12:QB, 13:QA` |
| `D53` | video/timing | `7:Y_N7, 9:Y_N6, 10:Y_N5, 11:Y_N4` |
| `D93` | logic/source | `15:STEP, 16:DIRC, 17:EARLY, 18:LATE, 19:MR_N, 22:TEST, 23:HLT, 24:CLK, 25:RG, 26:RCLK, 27:RAW_READ, 28:HLD, 29:TG43, 30:WG, 31:WDATA, 32:READY, 33:WF_VFOE, 34:TR00, 35:INDEX, 36:WPRT, 40:VDD_12V` |
| `D95` | FDC owner-continuity | `1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N` |
| `D96` | FDC owner-continuity | `1:CLR1_N, 2:D1, 3:CLK1, 4:PRE1_N, 5:Q1, 6:Q1_N, 9:Q2, 10:PRE2_N, 11:CLK2, 12:D2, 13:CLR2_N` |
| `D97` | FDC owner-continuity | `1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` |
| `D98` | FDC owner-continuity | `1:OE14_N, 2:A1, 4:A2, 5:Y2, 6:A3, 9:Y4, 10:A4, 11:Y5, 12:A5, 13:Y6, 14:A6, 15:OE56_N` |
| `D99` | FDC owner-continuity | `1:A_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` |

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
| `D2` | `9, 10, 11` |
| `D26` | `39` |
| `D3` | `3, 4, 5, 6` |
| `D30` | `6, 9` |
| `D44` | `13` |
| `D45` | `13` |
| `D46` | `13` |
| `D47` | `12, 13` |
| `D59` | `5, 6` |
| `D93` | `1` |

## Net-Level Source Risks

This mirrors the net-risk surface used by
`docs/replica-bringup-verification-points.md`, but keeps it in the
same fidelity ledger as the chip provenance gaps.

| Net | Category | Endpoints | Source risk |
| --- | --- | --- | --- |
| `CPU_WAIT_STATUS` | logic/source | `D1.24` | traced sheet-1 full-resolution: CPU D1 WAIT output pin24 enters the lower control-wire bundle; far destination remains unread |
| `CS_FDC` | PROM/decode | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch |
| `D105_GATE1_Y` | logic/source | `D105.3` | traced sheet-1: D105 gate pins 1,2 -> 3; output destination remains unread |
| `D105_WAIT_PREINV` | logic/source | `D105.6` | traced sheet-1 .006: D105 pin 6 feeds D95 inverter pin 1, whose pin 2 is -WAIT/E8-1; .009 reassigns D95 to an FDC KP12, so the target-revision destination re... |
| `D25_T` | PROM/decode | `D7.6, D25.11` | traced sheet-1 300dpi (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; section inputs... |
| `D26_PC5_TAG4` | PROM/decode | `D26.12` | traced sheet-1 full-resolution: D26 PC5/pin12 exits as mode-bundle tag4; far destination remains unread |
| `D26_PC6_TAG5` | PROM/decode | `D26.11` | traced sheet-1 full-resolution: D26 PC6/pin11 exits as mode-bundle tag5; far destination remains unread |
| `D26_PC7_TAG6` | PROM/decode | `D26.10` | traced sheet-1 full-resolution: D26 PC7/pin10 exits as mode-bundle tag6; far destination remains unread |
| `D30B_D_PRE_N` | PROM/decode | `D30.10, D30.12` | traced sheet-1: D30 section-B /PRE2 pin 10 and D2 pin 12 are visibly tied by the local U-shaped wire; the shared upstream source remains unread |
| `D34_SIG` | video/analog | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D36_CAS_IN` | memory/timing | `D36.12, D36.13` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); tied NAND pair = CAS-driver input; west source line [pending] |
| `D39_MEMCYC` | memory/timing | `D39.3, D39.4` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); out3 also drives rail 4 [rail dests pending] |
| `D56_QN` | clock/I/O | `D56.4` | traced sheet-2 (crop s2_dotclk_bend): D56.Q_N (pin 4) corners SOUTH at x~6074 — destination unread [chase]; the old "16MHz astable source" attribution retired |
| `D94_D3` | PROM/decode | `D94.4` | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) m... |
| `D94_D4` | PROM/decode | `D94.5` | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary |
| `D94_D5` | PROM/decode | `D94.6` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary |
| `D94_D6` | PROM/decode | `D94.7` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because... |
| `D94_D7` | PROM/decode | `D94.9` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary |
| `FDC_DDEN` | FDC owner-continuity | `D26.13, D93.37, D6.15` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15; .009/MAME PC4 is also FDC density -> D93.37. July-2026 two-sided local D93 fit identi... |
| `FDC_DRQ` | FDC owner-continuity | `D93.38, D10.19` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `FDC_INTRQ` | FDC owner-continuity | `D93.39, D10.18` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.1... |
| `FRAME_INT` | memory/timing | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (... |
| `HF_OUT` | video/analog | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board... |
| `IORD` | PROM/decode | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, ... (+4)` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed); D93.4 removed after local photo fit proved its direct D94.1... |
| `IOWR` | PROM/decode | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, ... (+4)` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed); D93.2 removed after local photo fit proved its direct D... |
| `LATCH_B` | clock/I/O | `D40.11, D37.2, D54.9, D54.15, D54.18` | scan+mame; +D54 CLK0/1/2: the drawn 1MHz rail = the D40.QD /16 tap (HDL+MAME concur; rail tag read pending) |
| `PHI2TTL` | logic/source | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_... |
| `PIC_IR2_BOUNDARY` | logic/source | `D10.20` | scan sheet-1: D10 IR2 pin 20 has a distinct southbound conductor; far destination remains unread |
| `PIC_IR3_BOUNDARY` | logic/source | `D10.21` | scan sheet-1: D10 IR3 pin 21 has a distinct southbound conductor; far destination remains unread |
| `PIT_BAUD` | clock/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V... |
| `PROM_EN` | PROM/decode | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assu... |
| `RAIL_E` | memory/timing | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members... |
| `RAM_SEL` | PROM/decode | `D6.11, D92.5, R12.2` | scan sheet-2 (bite-2: -RAM SEL arrival -> D92.5 write-strobe NOR; source D6.11 RAM_N per sheet-1 "(1)" label). D53.6/G3 detached: its drawn feed = long west... |
| `REV` | PROM/decode | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder re... |
| `RF_RAIL` | video/analog | `VT3.3, C9.2, R72.2, C10.1, R73.1, C11.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed |
| `ROE` | PROM/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merg... |
| `SND_MIX` | video/analog | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `SSTB_N` | logic/source | `D30.1` | sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary |
| `TAPE_RUN_INT` | logic/source | `D10.22` | scan sheet-1: D10 IR4 pin 22 is explicitly labeled (3) TAPE RUN INT; sheet-3 source remains outside the modeled board boundary |
| `VIDEO_OUT` | video/analog | `VT2.1, R65.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_... |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT3_BASE` | video/analog | `R68.2, R69.2, R70.2, R71.1, C13.1, VT3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `VT3_E` | video/analog | `VT3.1, R74.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT4_B` | video/analog | `R73.2, VT4.2, C10.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R73 4.7k drawn adjustable |
| `VT4_E` | video/analog | `VT4.1, R75.1, C14.1, C15.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `W_RAIL16` | memory/timing | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, ... (+27)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: th... |
| `XACK_N` | PROM/decode | `D2.2` | traced sheet-1: label -XACK enters D2 A5/pin 2 from edge code 106C; the existing X1.106C transcription says IORC_N, so the connector merge remains an explici... |
| `XTAL16M` | clock/I/O | `D103.2, D42.9, D43.9` | traced sheet-2 (crop s2_dotclk_bend): the 16MHz crystal rail (bundle tag 14) is a SEPARATE net from D56.Q_N; it clocks D103 + the ИР16 shifters. Likely = the... |

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
