# Memory timing boundary

Status date: 2026-07-13.

Status: **MEMORY TIMING GUARDED / CAS-D56 SOURCE BOUNDARY PENDING**

This generated report narrows the remaining DRAM/clock timing risks.
The board model preserves the traced E1/E14 selector straps, RAS/CAS ladder, write rail,
PHI2TTL fanout, and D56 one-shot RC networks. It also keeps the
unresolved CAS input and D56 Q2_N tag-16 destination as
explicit source boundaries instead of silently promoting them.

## Command

```sh
python3 scripts/report_memory_timing_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D36 К531ЛА12 package contract is the SN74S37-compatible quad 2-input NAND | PASS | inputs 1/2,4/5,9/10,12/13; outputs 3/6/8/11; GND7/VCC14 |
| All 32 DRAM sockets retain complete option-rail roles | PASS | D60-D91 pins 1/8/16 -> RAIL_H/RAIL_G/RAIL_E; pin 1 is internal NC for populated РУ5 |
| E1 MA7/DRAM-size selector retains all three source endpoints | PASS | sheet-2: E1.1=+5 V, E1.2=MA7 rail 28, E1.3=D51.9/MA6 |
| E14 video-mux enable retains the drawn 1-3 strap | PASS | sheet-2: E14.1-E14.3 fitted strap; E14.2=+5 V; E14.4=GND |
| D53 RAS/CAS ladder outputs are guarded | PASS | `D53_Y0_R49`..`D53_Y3_R52` |
| D53 unused Y4-Y7 outputs remain source-proved no-connects | PASS | sheet-2 complete D53 symbol draws only Y0-Y3; pins11/10/9/7 have no stubs |
| D36 write rail is guarded to all modeled DRAM W pins | PASS | `W_RAIL16` includes D36.8 plus DRAM pin-3 fanout |
| D36 CAS pre-driver reaches R57 | PASS | `CAS_PRE`: D36.11 -> R57.1 |
| Shared CAS rail is guarded to all modeled DRAM C pins | PASS | `CAS` includes D36.1/R57.2/R58.1 plus DRAM pin-15 fanout |
| PHI2TTL timing gate fanout is guarded | PASS | `PHI2TTL` source-risk net |
| D92 triple-NOR RAM read/write combiner is source-closed | PASS | sheet-2: read NOR 1/2/13->12; write NOR 3/4/5->6; combine 9/10/11->8 |
| Factory wire 11 is promoted onto MEMR with a clearance-safe routed bridge | PASS | native -MRD labels merge D92.13/D7.1; two-via B.Cu bridge avoids the front select bus |
| D39 latch/output context is guarded | PASS | `D39_O8` and `D39Y` |
| D39 remaining NAND inputs are source-closed onto control rails 3 and 1 | PASS | sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1 |
| D38 load gate is source-closed except for the remote origin of rail 2 | PASS | D38 pins5/4/2/1 <- rails4/2/1/15; D38 rail2 explicitly distinct from D34 top-edge tag2 |
| D42/D43 serializer packages retain their source-proved unused parallel outputs | PASS | sheet-2 draws only QD pin10; QA/QB/QC pins13/12/11 are explicit NCs on both packages |
| D56 one-shot RC networks are guarded | PASS | `D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2` |
| D56 active outputs reach both gate-3 XOR inputs | PASS | native sheet-2: D56.5/.4 -> D34.9/.10; D56.12 departs on unresolved tag16; undrawn D56.1/.9/.13 are NC |

## Pending Boundary Checks

| Boundary | Result | Current endpoints |
| --- | --- | --- |
| D35/D59 complete inverter package roles remain visible | PASS | D26.PC7 -> POF -> D35.3/.4 -> R39.1 guarded; D59.5/.6 NC; D59.10 tag10 distinct from SOUND |
| D36_CAS_IN native-sheet chase is exhausted without inventing a timing-rail merge | PASS | D36.12, D36.13; tied inputs visible, west source unlabeled in dense bundle |
| OSC-to-XTAL16M source-side merge remains unproved after native-sheet chase | PASS | OSC and XTAL16M remain distinct source nets pending continuity |
| D56_Q2_N tag-16 far destination remains unresolved | PASS | D56.12; explicitly not merged with D36.8/DRAM W rail16 |

## Current Timing Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D53_Y0_R49` | `D53.15, R49.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y1_R50` | `D53.14, R50.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y2_R51` | `D53.13, R51.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y3_R52` | `D53.12, R52.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `W_RAIL16` | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, D66.3, D67.3, D68.3, D69.3, ... (+23)` | traced sheet-2 (array read): all DRAM W pins <- rail 16 <- D36.8 (strobe-chain write leg; D36.9 qualifier pending). D36 pin 8 omitted from the LVS pinmap: the sim cannot reproduce the RC/delay chain, so we_n = MEMW through a net_boundary (boot-identical); copper follows this net |
| `CAS_PRE` | `D36.11, R57.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `CAS` | `D60.15, D61.15, D62.15, D63.15, D64.15, D65.15, D66.15, D67.15, D68.15, D69.15, ... (+27)` | traced sheet-2 (array read plus D38 load-gate bundle: per-bank R rails 11/12/13/14; C+W shared); rail15 = the ONE shared CAS: D36.11 (К531ЛА12/SN74S37 high-drive NAND) -> R57 -> all 32 C pins, R58 5.1k pullup -> rail E, D36.1 feedback, D38.1 load-gate input, and video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| `D36_CAS_IN` | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches R57, but the common west source enters a dense timing bundle without a unique rail number, label, or junction; automatic scan chase exhausted, so this remains a deliberate continuity boundary |
| `TIMING_TAG2` | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's same-number top-edge conductor visibly terminates in a distinct boundary domain with no continuous line between them; automatic same-number chase exhausted, and the D38.4 remote driver remains a deliberate continuity boundary |
| `D34_A1_TAG2` | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in that boundary domain; it does not continue to D38.4's separate left-side timing-bundle rail2 |
| `D39_MEMCYC` | `D39.3, D39.4, D38.5` | scan sheet-2 full-resolution (bite-2 plus D38 load-gate bundle): D39 output3 feeds its section-4 input pin4 and numbered timing rail4, which lands directly on D38 load-gate input pin5 |
| `MEMR` | `D5.24, D15.22, D16.22, D29.6, D17.22, D18.22, D19.22, D20.22, D21.22, D22.22, ... (+3)` | native .006 sheets 1-2 full-resolution continuous label chase 2026-07-13: sheet-1 D29 exports -MRD to sheet 2; both sheet-2 arrivals marked (1) -MRD land on D33.3 and D92.13, while factory wire 11 continues D92.13 to D7.1. This closes the former W11_D7_D92 split onto the global MEMR conductor |
| `D92_RD_NOR` | `D92.12, D92.11` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D92_WR_NOR` | `D92.6, D92.10, D92.9` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D92_NOACC` | `D92.8, D39.5` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `PHI2TTL` | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | scan sheet-2 (bite-3 mesh crops b3_*): pin-13 node = R35/C29/R106 RC shaper (passives not yet placed) = the "Ф2TTL" rail -> D39.1 + D92.2/3 (ex net D92_GATE_T) + "(1)" exit to sheet 1 [sheet-1 pin pending]; + D53.4 G2A_N (strobe window = Phi2) [scan sheet-2 (chase crops c4_g3_src: 4x y-match both feeds)] |
| `XTAL16M` | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate from D56.Q_N. A continuous source-side conductor to D59.2/D59.3 OSC is not drawn through the intervening bundle, so functional expectation alone cannot prove the PCB merge; automatic scan chase exhausted and each net remains a deliberate continuity boundary |
| `D39_O8` | `D39.8, D59.11` | scan |
| `D39Y` | `D39.11, D38.10, D38.13` | scan sheet-2 (bite-3 mesh crops b3_*): drawn D39.11 -> D38.10+13 (tied); formerly provisional, now traced |
| `D59_O10_TAG10` | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled numeral-10 use is D57.13 SOUND in a distinct bundle domain; no continuous conductor joins them, and merging would short two active TTL outputs. Automatic tag-number chase exhausted, so D59.10 remains a deliberate continuity boundary |
| `POF` | `D26.10, D35.3` | cross-sheet source closure: sheet-1 D26 PPI0 PC7/pin10 leaves through mode-bundle tag6; sheet-2 labels the receiving conductor POF directly into D35 inverter input pin3; the pinned MAME PPI0 Port-C contract independently identifies bit7 as POF |
| `D56_CLR` | `R61.2, D56.3, D56.11` | traced sheet-2 (crops s2_d56/s2_d56_pin2): R61 12k pullup (from +5V) -> D56 section-1 CLR_N pin 3; the section-2 CLR_N pin 11 vertical joins the same row [join read at low zoom -- probable, marked] |
| `D56_RC1` | `D56.15, R59.1, C8.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: RC pin 15 = R59 33k + C8 15nF |
| `D56_C1` | `D56.14, C8.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: C pin 14 = C8 far plate |
| `D56_RC2` | `D56.7, R47.1, C7.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: RC pin 7 = R47 20k + C7 560pF |
| `D56_C2` | `D56.6, C7.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: C pin 6 = C7 far plate |
| `D56_QN_D34` | `D56.4, D34.10` | scan sheet-2 native 5140x3563 review: D56 first-section Q_N pin4 runs east, corners south on its own vertical, and enters D34 gate-3 input pin10; it crosses the horizontal 16 MHz rail without a junction |
| `D56_Q2N_TAG16` | `D56.12` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D56 second-section Q2_N pin12 leaves east on conductor code 16; the former D34.10 merge is disproved by the distinct local D56.4-to-D34.10 vertical. No junction to D36.8 or the DRAM W rail is drawn, and merging solely by the repeated numeral 16 would short two push-pull outputs; automatic scan chase exhausted, so the far destination remains a deliberate continuity boundary |

## Interpretation

- The functional board model has enough traced structure for fabrication
  and staged bring-up: RAS/CAS ladder endpoints, the DRAM write rail,
  and the key PHI2TTL/D56 support nets are guarded.
- D92 is no longer an unmodeled timing placeholder. Its native triple-NOR
  read/write combiner is instantiated in the structural HDL and covered by
  LVS: pins 1/2/13 qualify reads, 3/4/5 qualify writes, and 9/10/11
  combine both results onto D92.8/D39.5. The repeated native-sheet -MRD
  label plus factory wire 11 close D92.13 and D7.1 onto global MEMR; the
  former artificial W11 boundary has been removed.
- The routed snapshot retains the former wire-11 copper as MEMR. Two
  0.6/0.3 mm vias at `(227.0497,127.5849)` and `(230,123)` plus a
  back-layer bridge join the two MEMR islands without crossing the four
  front-layer select traces. KiCad DRC reports zero MEMR shorts,
  clearances, crossings, or unconnected items.
- The exact CAS-driver input source (`D36_CAS_IN`) and D56 Q2_N tag-16
  destination are still not historical-source-complete. D36.12/.13 were
  rechecked across the native 5140x3563 sheet on 2026-07-13; their common
  west conductor enters an unlabeled dense timing bundle, so the automated
  scan chase is exhausted.
- D56.12's printed conductor code 16 is not evidence for a merge with the
  separate D36.8/DRAM write rail 16. Native full-sheet review shows no
  junction, and such a merge would short two push-pull outputs; its remote
  destination therefore remains a continuity boundary.
- D59.10's local timing-bundle marker 10 is likewise not the D57.13 SOUND
  bundle marker 10. Native full-sheet review shows no continuous conductor,
  and merging them would short active TTL outputs; automatic tag-number
  chasing is exhausted pending continuity or stronger imagery.
- The tag-14 `XTAL16M` bundle is functionally expected to originate at the
  D59 oscillator, but the native sheet does not draw a continuous source-side
  path through the intervening bundle. `OSC` and `XTAL16M` therefore remain
  separate until continuity or stronger artwork proves the PCB merge.
- D38.4's left-side timing rail 2 and D34.4's top-edge tag 2 are distinct
  boundary domains. The native vertical strip shows each terminating at its
  own gate input with no continuous conductor between them; matching numerals
  alone do not justify a merge.
- Do not replace these boundaries with a behavioral timing guess from the
  runnable twin. They need stronger sheet-2 imagery, macro photo,
  continuity check, or scope trace before being removed from the
  fidelity gap ledger.
