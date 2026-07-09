# Board fidelity gap ledger

Status: **BOARD FIDELITY GAPS CATALOGED**

This generated ledger records the remaining board-fidelity surfaces that
are explicit in `kicad/juku.board.json`: chip-level provenance that is
still assumed, boundary-only, deferred, untraced, or dump-dependent, and
net-level source risks already carried into the bring-up checklist. It
does not block fabrication by itself; it prevents the current 1:1 gaps
from being hidden behind a green endpoint-coverage gate.

## Command

```sh
python3 scripts/report_board_fidelity_gap_ledger.py
```

## Summary

- Board JSON: `kicad/juku.board.json`
- Chips modeled: `226`
- Nets modeled: `320`
- Chip-level fidelity gaps: `76`
- Net-level source-risk gaps: `41`

## Chip Provenance Types

| Provenance type | Chips |
| --- | ---: |
| assumed | 30 |
| datasheet | 1 |
| mame+datasheet | 1 |
| photo | 2 |
| prom | 1 |
| scan | 190 |
| wire | 1 |

## Gap Categories

| Category | Chip gaps | Net gaps |
| --- | ---: | ---: |
| FDC owner-continuity | 0 | 3 |
| PROM truth | 3 | 0 |
| PROM/decode | 0 | 8 |
| analog/source | 1 | 0 |
| clock/I/O | 0 | 4 |
| logic/source | 3 | 4 |
| memory/timing | 0 | 7 |
| placement/refdes | 38 | 0 |
| unpopulated sockets | 30 | 0 |
| video/analog | 0 | 15 |
| video/timing | 1 | 0 |

## Chip-Level Gaps

These are package/source/provenance gaps, not necessarily routed-copper
failures. Large repeated groups, such as unpopulated DRAM sockets and
decoupling capacitors, are still listed because they affect faithful
parts placement and Tier-3 reproduction.

### PROM truth

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D2` | `DEC_PROM` | scan | sheet-1: РТ4 D2 = bus-arbitration/wait PROM (A <- VIDEO CYCLE/-XACK/-WREQ rails, DO=12); nets deferred; contents = ДГШ5.106.037 [dump pending]; drawing = .03... |
| `D9` | `IO_DEC138` | scan | BOM ДГШ3.031.006 ВП: К555ИД7 x1 = the IO decoder. Decoder refdes = D9 (owner-confirmed К555ИД7 on the board). Physical D2 is a separate КР556РТ4 bus/wait PRO... |
| `D94` | `RE3_PROM_092` | prom | .009 official; programming ДГШ5.106.092 (dump pending) РЕ3 pinout; A0-A4 = BA11-15 (same convention as D8) |

### analog/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `VD5` | `D_DIODE` | scan | scan: VD5 by R19; zener clamp to GND [assumed orientation] |

### logic/source

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D100` | `BUF8287` | datasheet | .009 official (5th ВА87 = FDC bus buffer) 8287 std; OE/T gating [assumed] |
| `D93` | `VG93_FDC` | mame+datasheet | .009 official (FDC) WD1793 std pinout; bus side per MAME io 1C-1F + sheet-3 CS7 delta |
| `S4` | `SW` | scan | СБ position / sheet-1 interrupt receive path ВДМ1-2 microswitch at СБ .100 position; sheet-1 notes place S4.1/S4.2 in the D3-buffered IR7/IR6 external interr... |

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

### unpopulated sockets

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D17` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D18` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D19` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D20` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D21` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D22` | `EPROM8K` | assumed | scan unpopulated ROM socket [CS decode not traced] |
| `D68` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D69` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D70` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D71` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D72` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D73` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D74` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D75` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 1 [assumed bank-CAS] |
| `D76` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D77` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D78` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D79` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D80` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D81` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D82` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D83` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 2 [assumed bank-CAS] |
| `D84` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D85` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D86` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D87` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D88` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D89` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D90` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |
| `D91` | `RU5` | assumed | scan unpopulated РУ5 socket, bank 3 [assumed bank-CAS] |

### video/timing

| Ref | Type | Provenance | Note |
| --- | --- | --- | --- |
| `D41` | `IR16` | scan | sheet-2 LATCH chain: ИР16 D41, outputs B(12)/A(13); inputs D/C/B/A=5/4/3/2 from the timing-wire bus [boundary] |

## Net-Level Source Risks

This mirrors the net-risk surface used by
`docs/replica-bringup-verification-points.md`, but keeps it in the
same fidelity ledger as the chip provenance gaps.

| Net | Category | Endpoints | Source risk |
| --- | --- | --- | --- |
| `CAS` | video/analog | `D60.15, D61.15, D62.15, D63.15, D64.15, D65.15, ... (+29)` | traced sheet-2 (array read, crop arr_col1_locator: per-bank R rails 11/12/13/14; C+W shared); rail 15 = the ONE shared CAS: D36.11 (7437) -> R57 -> all 32 C... |
| `D25_T` | PROM/decode | `D7.6, D25.11` | traced sheet-1 300dpi (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; section inputs... |
| `D34_SIG` | video/analog | `D34.11, R63.1, R69.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `D34_SYNC` | video/analog | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D36_CAS_IN` | memory/timing | `D36.12, D36.13` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); tied NAND pair = CAS-driver input; west source line [pending] |
| `D39Y` | logic/source | `D39.11, D38.10, D38.13` | scan sheet-2 (bite-3 mesh crops b3_*): drawn D39.11 -> D38.10+13 (tied); ex-assumed, now traced |
| `D39_MEMCYC` | memory/timing | `D39.3, D39.4` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); out3 also drives rail 4 [rail dests pending] |
| `D56_QN` | clock/I/O | `D56.4` | traced sheet-2 (crop s2_dotclk_bend): D56.Q_N (pin 4) corners SOUTH at x~6074 — destination unread [chase]; the old "16MHz astable source" attribution retired |
| `FDC_DDEN` | FDC owner-continuity | `D26.13, D93.37` | mame (PC4 = density) |
| `FDC_DRQ` | FDC owner-continuity | `D93.38, D10.19` | assumed (MAME-era IR1; owner-verify) |
| `FDC_INTRQ` | FDC owner-continuity | `D93.39, D10.18` | assumed (MAME-era IR0; owner-verify) |
| `FRAME_INT` | memory/timing | `D55.13, D10.23, R60.1` | mame; D57.18 detached (drawn: CLK2 <- 1.23M rail tag 13, crop s2_d57_outs); +R60 5.1k pullup (sheet-2 overview + SB spot 253.9,202.7); drawn name "VER RTR" (... |
| `HF_OUT` | video/analog | `R76.2, R77.1, X6.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: RF out -> contact 701; conn = X6 per СБ assembly drawing (es101_emaplaat.pdf, board... |
| `IORD` | logic/source | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, ... (+5)` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed) |
| `IOWR` | logic/source | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, ... (+5)` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed) |
| `LATCH_B` | clock/I/O | `D40.11, D37.2, D54.9, D54.15, D54.18` | scan+mame; +D54 CLK0/1/2: the drawn 1MHz rail = the D40.QD /16 tap (HDL+MAME concur; rail tag read pending) |
| `MEM_MODE0` | PROM/decode | `D26.14, D6.2` | traced sheet-1 (bios_hunt1: D6.A5/pin2 <- mode-bundle tag 1) + scan (PPI PC0 = D26.14); tag<->PC-bit order assumed. D7.13 endpoint removed (that pin = IORD s... |
| `MEM_MODE1` | PROM/decode | `D26.15, D6.1` | traced sheet-1 (bios_hunt1: D6.A6/pin1 <- mode-bundle tag 2); source PPI PC1 = D26.15 [order assumed]. Tag 3 -> D6.15 left un-netted (source unread; PC2 guess) |
| `MEM_MODE2` | PROM/decode | `D26.16, D6.15` | traced sheet-1 300dpi (crop s1_d6_ven2: row "3/15" = mode-bundle tag 3 -> D6.15/A7) + source PPI PC2 = D26.16 [tag<->PC-bit order assumed, same level as MODE... |
| `PHI2TTL` | logic/source | `D35.13, D39.1, D92.2, D92.3, D53.4` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_... |
| `PIT_BAUD` | clock/I/O | `D57.10, D11.25, D11.9` | traced sheet-2 (bite-3): D57.OUT0 -> line labeled "BAUD R." -> pin 9 (D11 TxC) drawn at the label; D11.25 RxC fork [assumed at the UART end]. Rail "A" = +5V... |
| `PIT_HCHAIN` | memory/timing | `D54.10, D55.9, D54.14, D54.16` | traced sheet-2 300dpi (crops s2_d54/s2_d55): drawn cascade matches the MAME-derived wiring EXACTLY; D54.OUT0(10) -> D54.G1(14)+G2(16) + D55.CLK0(9) |
| `PIT_HSYNC_DSL` | video/analog | `D54.17, D55.15, D55.18` | traced sheet-2 300dpi (crops s2_d54/s2_d55): drawn cascade matches the MAME-derived wiring EXACTLY; D54.OUT2(17) "H.SYNC DSL" -> D55.CLK1(15)+CLK2(18) tied pair |
| `PIT_VCHAIN` | memory/timing | `D55.10, D55.14, D55.16` | traced sheet-2 300dpi (crops s2_d54/s2_d55): drawn cascade matches the MAME-derived wiring EXACTLY; D55.OUT0(10) -> D55.G1(14)+G2(16) |
| `PROM_EN` | PROM/decode | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assu... |
| `RAIL_E` | memory/timing | `R53.2, R54.2, R55.2, R56.2, R58.2, D60.16, ... (+69)` | traced sheet-2 power corner (crop b3_pwr_corner) + array read: "E" = the array ground rail (one-point strap to main GND; net-tie deferred to layout). Members... |
| `RAM_SEL` | PROM/decode | `D6.11, D92.5, R12.2` | scan sheet-2 (bite-2: -RAM SEL arrival -> D92.5 write-strobe NOR; source D6.11 RAM_N per sheet-1 "(1)" label). D53.6/G3 detached: its drawn feed = long west... |
| `REV` | PROM/decode | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder re... |
| `RF_RAIL` | video/analog | `VT3.3, C9.2, R72.2, C10.1, R73.1, C11.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R72 33R = can supply feed |
| `RF_TANK` | video/analog | `VT4.3, C11.2, C12.1, L1.1, R76.1, C15.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; L1 tap simplification (1/5 turns, ta... |
| `ROE` | PROM/decode | `D6.9, D13.1, D92.1, R14.2` | traced sheet-1 (crops d9_v3_follow/v3_junction: rail code 3 = D6.9, drawn name "-RAM OUT EN", 1k pullup R13/R14 pair-zone) -> D13.1 (TL2 Schmitt input); merg... |
| `SND_MIX` | video/analog | `R67.2, R68.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `SOUND_CLAMP` | video/analog | `R66.2, VD3.2, R67.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R66.1 <- the "SOUND" PIT line [sourc... |
| `VIDEO_OUT` | video/analog | `VT2.1, R65.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_... |
| `VT2_BASE` | video/analog | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT3_BASE` | video/analog | `R68.2, R69.2, R70.2, R71.1, C13.1, VT3.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `VT3_E` | video/analog | `VT3.1, R74.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VT4_B` | video/analog | `R73.2, VT4.2, C10.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout; R73 4.7k drawn adjustable |
| `VT4_E` | video/analog | `VT4.1, R75.1, C14.1, C15.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible; joint read ~approx, refine vs photos at layout |
| `W_RAIL16` | memory/timing | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, ... (+27)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: th... |
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
