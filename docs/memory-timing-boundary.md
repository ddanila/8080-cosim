# Memory timing boundary

Status date: 2026-07-13.

Status: **MEMORY TIMING GUARDED / CAS-MEMCYC SOURCE BOUNDARY PENDING**

This generated report narrows the remaining DRAM/clock timing risks.
The board model preserves the traced E1/E14 selector straps, RAS/CAS ladder, write rail,
PHI2TTL fanout, and D56 one-shot RC networks. It also keeps the
unread CAS input, memory-cycle gate, and D56 Q_N destination as
explicit source boundaries instead of silently promoting them.

## Command

```sh
python3 scripts/report_memory_timing_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All 32 DRAM sockets retain complete option-rail roles | PASS | D60-D91 pins 1/8/16 -> RAIL_H/RAIL_G/RAIL_E; pin 1 is internal NC for populated РУ5 |
| E1 MA7/DRAM-size selector retains all three source endpoints | PASS | sheet-2: E1.1=+5 V, E1.2=MA7 rail 28, E1.3=D51.9/MA6 |
| E14 video-mux enable retains the drawn 1-3 strap | PASS | sheet-2: E14.1-E14.3 fitted strap; E14.2=+5 V; E14.4=GND |
| D53 RAS/CAS ladder outputs are guarded | PASS | `D53_Y0_R49`..`D53_Y3_R52` |
| D36 write rail is guarded to all modeled DRAM W pins | PASS | `W_RAIL16` includes D36.8 plus DRAM pin-3 fanout |
| D36 CAS pre-driver reaches R57 | PASS | `CAS_PRE`: D36.11 -> R57.1 |
| Shared CAS rail is guarded to all modeled DRAM C pins | PASS | `CAS` includes D36.1/R57.2/R58.1 plus DRAM pin-15 fanout |
| PHI2TTL timing gate fanout is guarded | PASS | `PHI2TTL` source-risk net |
| D39 latch/output context is guarded | PASS | `D39_O8` and `D39Y` |
| D39 remaining NAND inputs are source-closed onto control rails 3 and 1 | PASS | sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1 |
| D56 one-shot RC networks are guarded | PASS | `D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2` |
| D56 active outputs reach both gate-3 XOR inputs | PASS | sheet-2: D56.5/.12 -> D34.9/.10; undrawn D56.1/.9/.13 are NC |

## Pending Boundary Checks

| Boundary | Result | Current endpoints |
| --- | --- | --- |
| D35/D59 complete inverter package roles remain visible | PASS | D35.4->R39.1 is guarded; D59.5/.6 are source-proved NC; D59.10 remains a continuity boundary |
| D53 Y4-Y7 remain explicit unresolved functional pins | PASS | D53.11/.10/.9/.7 require traced destinations or explicit NC proof |
| D36_CAS_IN remains source-boundary only | PASS | D36.12, D36.13 |
| D39_MEMCYC remains source-boundary only | PASS | D39.3, D39.4 |
| D56_QN remains unresolved one-shot output | PASS | D56.4 |

## Current Timing Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D53_Y0_R49` | `D53.15, R49.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y1_R50` | `D53.14, R50.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y2_R51` | `D53.13, R51.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y3_R52` | `D53.12, R52.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `W_RAIL16` | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, D66.3, D67.3, D68.3, D69.3, ... (+23)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: the sim cannot reproduce the RC/delay chain, so we_n = MEMW through a net_boundary (boot-identical); copper follows this net |
| `CAS_PRE` | `D36.11, R57.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `CAS` | `D60.15, D61.15, D62.15, D63.15, D64.15, D65.15, D66.15, D67.15, D68.15, D69.15, ... (+26)` | traced sheet-2 (array read, crop arr_col1_locator: per-bank R rails 11/12/13/14; C+W shared); rail 15 = the ONE shared CAS: D36.11 (7437) -> R57 -> all 32 C pins, R58 5.1k pullup -> rail E, D36.1 feedback, video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| `D36_CAS_IN` | `D36.12, D36.13` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); tied NAND pair = CAS-driver input; west source line [pending] |
| `D39_MEMCYC` | `D39.3, D39.4` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*); out3 also drives rail 4 [rail dests pending] |
| `PHI2TTL` | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_T) + "(1)" exit to sheet 1 [sheet-1 pin pending]; + D53.4 G2A_N (strobe window = Phi2) [scan sheet-2 (chase crops c4_g3_src: 4x y-match both feeds)] |
| `XTAL16M` | `D39.10, D103.2, D42.9, D43.9` | traced sheet-2 (crops s2_dotclk_bend and D39/D41 control bundle): the 16MHz crystal source at bundle tag14 feeds local control rail3, clocking D103, D42/D43 ИР16, and D39 NAND input pin10; it is separate from D56.Q_N. Likely = the OSC net continuation (D59) — source-side merge remains pending |
| `D39_O8` | `D39.8, D59.11` | scan |
| `D39Y` | `D39.11, D38.10, D38.13` | scan sheet-2 (bite-3 mesh crops b3_*): drawn D39.11 -> D38.10+13 (tied); formerly provisional, now traced |
| `D56_CLR` | `R61.2, D56.3, D56.11` | traced sheet-2 (crops s2_d56/s2_d56_pin2): R61 12k pullup (from +5V) -> D56 section-1 CLR_N pin 3; the section-2 CLR_N pin 11 vertical joins the same row [join read at low zoom -- probable, marked] |
| `D56_RC1` | `D56.15, R59.1, C8.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: RC pin 15 = R59 33k + C8 15nF |
| `D56_C1` | `D56.14, C8.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: C pin 14 = C8 far plate |
| `D56_RC2` | `D56.7, R47.1, C7.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: RC pin 7 = R47 20k + C7 560pF |
| `D56_C2` | `D56.6, C7.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: C pin 6 = C7 far plate |
| `D56_QN` | `D56.4` | traced sheet-2 (crop s2_dotclk_bend): D56.Q_N (pin 4) corners SOUTH at x~6074 — destination unread [chase]; the old "16MHz astable source" attribution retired |

## Interpretation

- The functional board model has enough traced structure for fabrication
  and staged bring-up: RAS/CAS ladder endpoints, the DRAM write rail,
  and the key PHI2TTL/D56 support nets are guarded.
- The exact CAS-driver input source (`D36_CAS_IN`), D39 memory-cycle
  source/destinations (`D39_MEMCYC`), and D56 Q_N destination are still
  not historical-source-complete.
- Do not replace these boundaries with a behavioral timing guess from the
  runnable twin. They need a readable sheet-2 source pass, macro photo,
  continuity check, or scope trace before being removed from the
  fidelity gap ledger.
