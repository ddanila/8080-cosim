# Memory timing boundary

Status date: 2026-07-22.

Status: **MEMORY TIMING GUARDED / CAS SOURCE BOUNDARY PENDING**

This generated report narrows the remaining DRAM/clock timing risks.
The board model preserves the traced E1 and E13/E14 selector straps, RAS/CAS ladder, write rail,
PHI2TTL fanout, and D56 one-shot RC networks. Exact-revision `.009 E3`
imagery plus owner continuity closes the D54/D55/D56 trigger and clock
crossings. A primary SN54S138 comparison bounds compatible D53 decoder
propagation at 12 ns maximum under its published test conditions; it does
not replace the unresolved Juku enables, slot schedule, or CAS source.

## Command

```sh
python3 scripts/report_memory_timing_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D36 К531ЛА12 package contract is the SN74S37-compatible quad 2-input NAND | PASS | inputs 1/2,4/5,9/10,12/13; outputs 3/6/8/11; GND7/VCC14 |
| All 32 DRAM sockets retain complete option-rail roles | PASS | D60-D91 pins 1/8/16 -> RAIL_H/RAIL_G/GND; native rail E is ground; pin 1 is internal NC for populated РУ5 |
| C34 bypass follows the native rail-E to rail-F drawing | PASS | native sheet-2 power corner: C34 spans E/GND to F/+5 V |
| E1 MA7/DRAM-size selector retains all three source endpoints | PASS | sheet-2: E1.1=+5 V, E1.2=MA7 rail 28, E1.3=D51.9/MA6 |
| D59/E13/E14 complementary mux-enable topology is source-closed | PASS | sheet-2: D59.5->E14.1-3->D50/D51 /G; D59.6->E13.1-3->D48/D49 /G |
| D53 RAS/CAS ladder outputs are guarded | PASS | `D53_Y0_R49`..`D53_Y3_R52` |
| D53 identity and compatible decoder timing evidence are guarded | PASS | physical D53=КР531ИД7; TI SN54S138 primary compatible reference SHA256 guarded; published comparison max=12 ns |
| D53 unused Y4-Y7 outputs remain source-proved no-connects | PASS | sheet-2 complete D53 symbol draws only Y0-Y3; pins11/10/9/7 have no stubs |
| D36 write-gate inputs and rail are guarded to all modeled DRAM W pins | PASS | MEMW->D36.9; D36.3->D33.11/.10->D36.10; D36.8->32 DRAM pin-3 inputs |
| D36 CAS pre-driver reaches R57 | PASS | `CAS_PRE`: D36.11 -> R57.1 |
| Shared CAS rail is guarded to all modeled DRAM C pins | PASS | `CAS` includes D36.1/R57.2/R58.1 plus DRAM pin-15 fanout |
| PHI2TTL timing gate fanout is cross-sheet source-closed | PASS | sheet-2 Ф2TTL (1) export -> sheet-1 (2) Ф2 TTL/D30.3 |
| D92 triple-NOR RAM read/write combiner is source-closed | PASS | sheet-2: read NOR 1/2/13->12; write NOR 3/4/5->6; combine 9/10/11->8 |
| D37 RAM-read output-enable NAND is source-closed on both inputs and output | PASS | sheet-2: MEMR -> D33.3/.4 -> D37.5; D13.2 -> D37.4; D37.6 -> D58.OE9 |
| Factory wire 11 is preserved as an assembly closure between MEMR islands | PASS | native -MRD reaches D92.13/A11B; W11 crosses to the D7.1/A11A surface island without PCB copper |
| Factory wire 19 is preserved as an assembly closure to D7.2 | PASS | global MEMW/D5.26 reaches A19A; W19 crosses to the separate D7.2/A19B surface island |
| D39 latch/output context is guarded | PASS | `D39_O8` and `D39Y` |
| D39 remaining NAND inputs are source-closed onto control rails 3 and 1 | PASS | sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1 |
| D38 load gate is source-closed except for the remote origin of rail 2 | PASS | D38 pins5/4/2/1 <- rails4/2/1/15; D38 rail2 explicitly distinct from D34 top-edge tag2 |
| D42/D43 serializer packages retain their source-proved unused parallel outputs | PASS | sheet-2 draws only QD pin10; QA/QB/QC pins13/12/11 are explicit NCs on both packages |
| D56 one-shot RC networks are guarded | PASS | `D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2` |
| D56 trigger, clock, and active-output topology is owner-closed | PASS | exact .009 E3 plus owner continuity 2026-07-21: D54.17->D56.10, D55.17->D56.2, D56.12->D55.15/.18, D56.5/.4->D34.9/.10; D57.17 remains separate |
| D35 frame-interrupt inverter path is source-closed | PASS | native sheets: D55.13/VER RTR -> D35.9/.8 -> FRAME INT/R60 -> D10.23; D35.3/.4 remains POF/VID_MIX2 |
| D30 READY clear uses the native D38-side status strobe | PASS | sheet-2 D38.8 active-low STB export -> sheet-1 -SSTB/D30.1; W8 still separates the D5-side island |

## Compatible D53 Decoder Timing Envelope

| Evidence | Published condition | Maximum | Model use |
| --- | --- | --- | --- |
| TI SN54S138 primary manufacturer sheet (compatible function/pinout, not the exact КР531ИД7 process) | VCC=5 V, TA=25 C, RL=280 ohm, CL=15 pF; binary-select and enable paths | 12 ns | guarded order-of-magnitude comparison only; no invented HDL delay |

## Pending Boundary Checks

| Boundary | Result | Current endpoints |
| --- | --- | --- |
| D59 remaining timing boundary remains visible | PASS | D59.5/.6 mux-enable inverter is traced; D59.10 tag10 remains distinct from SOUND |
| D36_CAS_IN native-sheet chase is exhausted without inventing a timing-rail merge | PASS | D36.12, D36.13; tied inputs visible, west source unlabeled in dense bundle |
| OSC-to-XTAL16M source-side merge remains unproved after native-sheet chase | PASS | OSC and XTAL16M remain distinct source nets pending continuity |

## Current Timing Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D53_Y0_R49` | `D53.15, R49.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y1_R50` | `D53.14, R50.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y2_R51` | `D53.13, R51.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D53_Y3_R52` | `D53.12, R52.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `W_RAIL16` | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, D66.3, D67.3, D68.3, D69.3, ... (+23)` | fully traced native sheet-2 write-strobe chain: MEMW enters D36 NAND input pin9, the D36.3 -> D33.11/.10 inverter-delay leg reaches D36 input pin10, and D36.8 drives rail 16 to all 32 DRAM W pins. D36 pin 8 is omitted from the LVS pinmap because the sim cannot reproduce the physical gate-delay chain; we_n = MEMW through a net_boundary remains the boot-identical behavioral abstraction while copper follows this source-proved net |
| `CAS_PRE` | `D36.11, R57.1` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `CAS` | `D60.15, D61.15, D62.15, D63.15, D64.15, D65.15, D66.15, D67.15, D68.15, D69.15, ... (+27)` | traced sheet-2 (array read plus D38 load-gate bundle: per-bank R rails 11/12/13/14; C+W shared); rail15 = the ONE shared CAS: D36.11 (К531ЛА12/SN74S37 high-drive NAND) -> R57 -> all 32 C pins, R58 5.1k pullup -> rail E, D36.1 feedback, D38.1 load-gate input, and video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| `D36_CAS_IN` | `D36.12, D36.13` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13 (D92/D39/D52/D53 RAM-strobe cluster): D36 high-drive NAND inputs pins12/13 are visibly tied and output pin11 reaches R57, but the common west source enters a dense timing bundle without a unique rail number, label, or junction; automatic scan chase exhausted, so this remains a deliberate continuity boundary |
| `TIMING_TAG2` | `D38.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: numbered left-side timing rail2 lands directly on D38 second ЛА1 section input pin4. D34.4's same-number top-edge conductor visibly terminates in a distinct boundary domain with no continuous line between them; automatic same-number chase exhausted, and the D38.4 remote driver remains a deliberate continuity boundary |
| `D34_A1_TAG2` | `D34.4` | scan sheet-2 native 5140x3563 vertical-strip recheck 2026-07-13: D34 gate-1 input pin4 runs continuously to the top-edge conductor marked 2 and terminates in that boundary domain; it does not continue to D38.4's separate left-side timing-bundle rail2 |
| `D39_MEMCYC` | `D39.3, D39.4, D38.5` | scan sheet-2 full-resolution (bite-2 plus D38 load-gate bundle): D39 output3 feeds its section-4 input pin4 and numbered timing rail4, which lands directly on D38 load-gate input pin5 |
| `MEMR` | `D5.24, D15.22, D16.22, D29.6, D17.22, D18.22, D19.22, D20.22, D21.22, D22.22, ... (+3)` | native .006 sheets 1-2 full-resolution continuous label chase 2026-07-13: sheet-1 D29 exports -MRD to sheet 2; both sheet-2 arrivals marked (1) -MRD land on D33.3 and D92.13, while factory wire 11 continues D92.13 to D7.1. This closes the former W11_D7_D92 split onto the global MEMR conductor |
| `D33_O4` | `D33.4, D37.5` | fully traced native sheet-2 300dpi route (crops s2_d37_d58 + s2_d58_oe): global -MRD/MEMR enters D33 inverter pin3, D33.4 runs directly to D37 NAND input pin5; this is the second qualifier paired with D13.2/RAM_OUT_EN on D37.4 |
| `RAM_OUT_EN` | `D13.2, D37.4` | direct owner continuity 2026-07-14 confirms D13.2 -> D37.4. This agrees with traced sheet-1: D13.2 = ТЛ2 inverter OUTPUT (= ~D6.9) driving RAMOUTEN, exported "(2)" code 12 -> sheet-2 D37.4; factory wire 12 corroborates; cross-sheet arrival "(1) RAM OUT EN. -> D37.4" traced (crop s2_d37_d58) |
| `RAM_RD_OE` | `D37.6, D58.9` | direct owner continuity 2026-07-14 confirms D37.6 -> D58.OE pin9. This agrees with the fully traced sheet-2 300dpi route (crops s2_d37_d58 + s2_d58_oe): "(1) RAM OUT EN." -> D37.4; "-MRD" -> D33 sect 3->4 -> D37.5; D37.6 riser corners east into D58.9 |
| `D92_RD_NOR` | `D92.12, D92.11` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D92_WR_NOR` | `D92.6, D92.10, D92.9` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `D92_NOACC` | `D92.8, D39.5` | scan sheet-2 (bite-2: D92/D39/D52/D53 RAM-strobe cluster, crops b2_*) |
| `PHI2TTL` | `D35.13, D39.1, D92.2, D92.3, D53.4, D30.3` | native .006 sheets 1-2 cross-reference closure: sheet-2 D35.13/R35/C29/R106 RC shaper is the Ф2TTL rail feeding D39.1, D92.2/.3, and D53.4 before export marked (1); sheet-1 matching arrival (2) Ф2 TTL lands directly on D30 CLK1/pin3 |
| `XTAL16M` | `D39.10, D103.2, D42.9, D43.9` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: labeled 16MHz bundle tag14 feeds local control rail3 and clocks D103, D42/D43 ИР16, and D39 pin10. It is separate from D56.Q_N. A continuous source-side conductor to D59.2/D59.3 OSC is not drawn through the intervening bundle, so functional expectation alone cannot prove the PCB merge; automatic scan chase exhausted and each net remains a deliberate continuity boundary |
| `D39_O8` | `D39.8, D59.11` | scan |
| `D39Y` | `D39.11, D38.10, D38.13` | scan sheet-2 (bite-3 mesh crops b3_*): drawn D39.11 -> D38.10+13 (tied); formerly provisional, now traced |
| `D59_O10_TAG10` | `D59.10` | scan sheet-2 native 5140x3563 full-sheet recheck 2026-07-13: D59 inverter output pin10 descends continuously to its local open-circle timing-bundle marker 10. The other modeled numeral-10 use is D57.13 SOUND in a distinct bundle domain; no continuous conductor joins them, and merging would short two active TTL outputs. Automatic tag-number chase exhausted, so D59.10 remains a deliberate continuity boundary |
| `POF` | `D26.10, D35.3` | cross-sheet source closure: sheet-1 D26 PPI0 PC7/pin10 leaves through mode-bundle tag6; sheet-2 labels the receiving conductor POF directly into D35 inverter input pin3; the pinned MAME PPI0 Port-C contract independently identifies bit7 as POF |
| `VERT_RTR` | `D55.13, D35.9` | native sheet-2 draws D55 OUT1/pin13 as VER RTR with boundary tag2, which continues into D35 К155ЛН5 input pin9 before inversion to FRAME INT |
| `FRAME_INT` | `D35.8, D10.23, R60.1` | native sheet-2 draws D35 К155ЛН5 output pin8 as FRAME INT with R60 5.1k pull-up; native sheet-1 draws FRAME INT(2) directly into D10 IR5/pin23 |
| `D56_CLR` | `R61.2, D56.3, D56.11` | traced sheet-2 (crops s2_d56/s2_d56_pin2): R61 12k pullup (from +5V) -> D56 section-1 CLR_N pin 3; the section-2 CLR_N pin 11 vertical joins the same row [join read at low zoom -- probable, marked] |
| `D56_RC1` | `D56.15, R59.1, C8.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: RC pin 15 = R59 33k + C8 15nF |
| `D56_C1` | `D56.14, C8.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 1: C pin 14 = C8 far plate |
| `D56_RC2` | `D56.7, R47.1, C7.1` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: RC pin 7 = R47 20k + C7 560pF |
| `D56_C2` | `D56.6, C7.2` | traced sheet-2 (crop s2_d56): АГ3 one-shot RC network section 2: C pin 6 = C7 far plate |
| `D56_QN_D34` | `D56.4, D34.10` | scan sheet-2 native 5140x3563 review: D56 first-section Q_N pin4 runs east, corners south on its own vertical, and enters D34 gate-3 input pin10; it crosses the horizontal 16 MHz rail without a junction |
| `PIT_HSYNC_DSL` | `D54.17, D56.10` | exact-revision .009 E3 sheet 2 plus direct owner continuity 2026-07-21: D54.OUT2/pin17 H.SYNC DSL drives D56 B2/pin10; it does not join the D55 clock pair |
| `VERT_SYNC` | `D55.17, D56.2` | exact-revision .009 E3 sheet 2 plus direct owner continuity 2026-07-21: D55.OUT2/pin17 VERT SYNC DSL drives D56 B/pin2 |
| `D56_Q2N_TAG16` | `D56.12, D55.15, D55.18` | exact-revision .009 E3 sheet 2 plus direct owner continuity 2026-07-21: D56 second-section Q2_N/pin12 drives the tied D55 CLK1/pin15 and CLK2/pin18 conductor marked 16; this signal is distinct from D36.8/DRAM write rail 16 |
| `SYNC_B` | `D57.17` | exact-revision .009 E3 sheet 2 and direct owner continuity 2026-07-21 disprove the older scan chase that joined D57.OUT2/pin17 to both D56 triggers; D57.OUT2 remains the separately labeled SYNC B boundary |

## Interpretation

- The functional board model has enough traced structure for fabrication
  and staged bring-up: RAS/CAS ladder endpoints, the DRAM write rail,
  and the key PHI2TTL/D56 support nets are guarded.
- Physical D53 is guarded as КР531ИД7 with its traced 16-pin decoder
  contract. The preserved primary TI SN54S138 sheet supplies a 12 ns
  compatible-device maximum only at 5 V, 25 C, RL=280 ohm, CL=15 pF.
  It does not guarantee the Soviet process, loaded board, or slot timing,
  so the structural HDL remains untimed and those boundaries stay open.
- The runnable CPU-memory scaffold now models a complete row/column transaction:
  RAS remains active from the row phase through the CAS column pulse, and the
  РУ5 model strobes DIN on the latter falling edge of CAS or WE for early and
  delayed writes. The 130,000-read C-reference guard reaches `CTRACE-END` and
  the dedicated DRAM unit guard covers coincident control edges. This is a
  functional timing closure; it does not infer the unresolved D36.12/.13
  conductor or the physical CPU/video slot schedule.
- D92 is no longer an unmodeled timing placeholder. Its native triple-NOR
  read/write combiner is instantiated in the structural HDL and covered by
  LVS: pins 1/2/13 qualify reads, 3/4/5 qualify writes, and 9/10/11
  combine both results onto D92.8/D39.5. The repeated native-sheet -MRD
  label reaches D92.13, while factory wire W11 closes its registered A11B
  surface island to the separate D7.1/A11A island without etched copper.
- D37's RAM-read gate is source-complete rather than a remaining probe ask:
  global MEMR enters D33.3, the inverter output D33.4 reaches D37.5,
  D13.2/RAM_OUT_EN reaches D37.4, and D37.6 reaches D58.OE pin 9.
- D36's DRAM-write gate is likewise source-complete: MEMW enters pin 9,
  the D36.3 -> D33.11/.10 delay leg reaches pin 10, and output pin 8
  drives rail 16 to every DRAM W pin. The direct `we_n = MEMW` simulation
  path remains an explicit timing abstraction, not a copper uncertainty.
- The promoted route preserves W11 as an explicit assembly wire between
  the separately routed `MEMR` and `MEMR_D7` copper islands; it does not
  restore the former etched bridge. Exact source-pad parity and stable
  KiCad DRC report zero opens or electrical blockers.
- The exact CAS-driver input source (`D36_CAS_IN`) is still not
  historical-source-complete. D36.12/.13 were
  rechecked across the native 5140x3563 sheet on 2026-07-13; their common
  west conductor enters an unlabeled dense timing bundle, so the automated
  scan chase is exhausted.
- Exact-revision `.009 E3` sheet 2 and owner continuity close D56.12's
  conductor code 16 onto the tied D55 CLK1/CLK2 inputs at pins 15/18.
  It remains distinct from the unrelated D36.8/DRAM write rail 16.
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
