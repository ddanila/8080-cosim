# Memory timing boundary

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
| PHI2TTL trunk and post-R35 RC node remain separate | PASS | sheet-2 Ф2TTL trunk -> D30.3/D29.1/R35.1; R35.2 -> D35.13/R106.1/C29.1 |
| D92 triple-NOR RAM read/write combiner is source-closed | PASS | sheet-2: read NOR 1/2/13->12; write NOR 3/4/5->6; combine 9/10/11->8 |
| D37 RAM-read output-enable NAND is source-closed on both inputs and output | PASS | sheet-2: MEMR -> D33.3/.4 -> D37.5; D13.2 -> D37.4; D37.6 -> D58.OE9 |
| Factory wire 11 is preserved as an assembly closure between MEMR islands | PASS | native -MRD reaches D92.13/A11B; W11 crosses to the D7.1/A11A surface island without PCB copper |
| Factory wire 19 is preserved as an assembly closure to D7.2 | PASS | global MEMW/D5.26 reaches A19A; W19 crosses to the separate D7.2/A19B surface island |
| D39 latch/output context is guarded | PASS | `D39_O8` and `D39Y` |
| D39 remaining NAND inputs are source-closed onto control rails 3 and 1 | PASS | sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1 |
| D38.4 and D34.4 share photographed timing rail 2; remote driver remains open | PASS | D38 pin5 <- LATCH; pins4/2/1 <- rails2/1/15; D39.3/.4 join separate rail4; owner solder copper directly joins D38.4 rail2 to D34.4 top-edge tag2 |
| D42/D43 serializer packages retain their source-proved unused parallel outputs | PASS | sheet-2 draws only QD pin10; QA/QB/QC pins13/12/11 are explicit NCs on both packages |
| D56 one-shot RC networks are guarded | PASS | `D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2` |
| D56 trigger, clock, and active-output topology is owner-closed | PASS | exact .009 E3 plus owner continuity 2026-07-21: D54.17->D56.10, D55.17->D56.2, D56.12->D55.15/.18, D56.5/.4->D34.9/.10; D57.17 remains separate |
| D35 frame-interrupt inverter path is source-closed | PASS | exact .009 E3: D55.13 active-low VER RTR -> D35.9/.8 -> FRAME INT/R60 -> D10.23 and D57.18/CLK2; POF drives D35.3/.5 and R39.1, D35.4 joins D42.10/D37.13, D37.12 shares numbered rail 3 with D42.9/D43.9 while D37.11 reaches D34.12, and D35.6/R38.1 drive SHIFT_G |
| D30 common asynchronous-control conductor uses the native D38-side status strobe | PASS | exact .009 sheets plus owner continuity: D38.8 STB -> D30.1/.4/.10/.12 and R5 pull-up; W8 still separates the D5-side island |

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

Per-net provenance is retained in [the board model](../kicad/juku.board.json).

| Net | Endpoints |
| --- | --- |
| `D53_Y0_R49` | `D53.15, R49.1` |
| `D53_Y1_R50` | `D53.14, R50.1` |
| `D53_Y2_R51` | `D53.13, R51.1` |
| `D53_Y3_R52` | `D53.12, R52.1` |
| `W_RAIL16` | `D60.3, D61.3, D62.3, D63.3, D64.3, D65.3, D66.3, D67.3, D68.3, D69.3, ... (+23)` |
| `CAS_PRE` | `D36.11, R57.1` |
| `CAS` | `D60.15, D61.15, D62.15, D63.15, D64.15, D65.15, D66.15, D67.15, D68.15, D69.15, ... (+27)` |
| `D36_CAS_IN` | `D36.12, D36.13` |
| `TIMING_TAG2` | `D38.4, D34.4` |
| `D39_MEMCYC` | `D39.3, D39.4` |
| `LATCH_SIG` | `D33.12, D39.9, D38.5` |
| `MEMR` | `D5.24, D15.22, D16.22, D29.6, D17.22, D18.22, D19.22, D20.22, D21.22, D22.22, ... (+3)` |
| `D33_O4` | `D33.4, D37.5` |
| `RAM_OUT_EN` | `D13.2, D37.4` |
| `RAM_RD_OE` | `D37.6, D58.9` |
| `D92_RD_NOR` | `D92.12, D92.11` |
| `D92_WR_NOR` | `D92.6, D92.10, D92.9` |
| `D92_NOACC` | `D92.8, D39.5` |
| `PHI2TTL` | `D39.1, D53.4, D30.3, D29.1, R35.1` |
| `PHI2_POST_R35` | `D35.13, R35.2, R106.1, C29.1` |
| `XTAL16M` | `D39.10, D103.2, D42.9, D43.9, D37.12` |
| `D39_O8` | `D39.8, D59.11` |
| `D39Y` | `D39.11, D38.10, D38.13` |
| `D59_O10_TAG10` | `D59.10` |
| `POF` | `D26.10, D35.3, D35.5, R39.1` |
| `VERT_RTR` | `D55.13, D35.9, D57.18` |
| `FRAME_INT` | `D35.8, D10.23, R60.1` |
| `D56_CLR` | `R61.2, D56.3, D56.11` |
| `D56_RC1` | `D56.15, R59.1, C8.1` |
| `D56_C1` | `D56.14, C8.2` |
| `D56_RC2` | `D56.7, R47.1, C7.1` |
| `D56_C2` | `D56.6, C7.2` |
| `D56_QN_D34` | `D56.4, D34.10` |
| `PIT_HSYNC_DSL` | `D54.17, D56.10` |
| `VERT_SYNC` | `D55.17, D56.2` |
| `D56_Q2N_TAG16` | `D56.12, D55.15, D55.18` |
| `SYNC_B` | `D57.17` |

The exact `.009` sheet-2 detail places D58.11 on timing tag 5,
separate from D38.5 and D39.12. In the same tile D33.12 `LATCH`
branches into D38.5, while D39.3 and D39.4 join numbered rail 4;
D38.4 follows rail 2. The connectivity JSON reflects this source
correction. All three PCB variants assign D38.5 to LATCH; the
routed variants remove its obsolete rail-4 branch and route it to
D39.9 LATCH. This local correction is not a whole-board DRC verdict.
A registered solder close-up also shows no visible B.Cu departure
from D58.11 and no join to the broad +5 V strip below it; its
component-side trace and remote driver remain unresolved.

## Interpretation

- This generator checks source-model endpoints and evidence metadata; it
  does not execute simulations, inspect routed copper or measure timing.
  Fabrication remains on DESIGN HOLD.
- The TI SN54S138 comparison bounds a compatible decoder at the published
  conditions in the table. It does not qualify the fitted КР531ИД7,
  loaded-board timing or a physical DRAM slot schedule.
- The runnable memory scaffold holds RAS through the column phase and samples
  DIN on the latter falling edge of CAS or WE. The C/HDL bus-event and DRAM
  unit guards check this behavior separately; it does not identify the
  physical D36 CAS input or CPU/video arbitration schedule.
- D36's source-traced write rail is distinct from the simulation's direct
  `we_n = MEMW` abstraction. D56.12's conductor code 16 is also distinct
  from D36.8's DRAM write rail 16.
- `D36_CAS_IN` has a local D36.12/.13 tie but an untraced remote driver.
  `OSC` and `XTAL16M` remain separate until their source-side merge is proved.
  D38.4/D34.4 share timing rail 2; its remote driver remains open.
- D59.10's tag 10 is not proof of a connection to D57 SOUND or assembly
  wire W10 at D41.13. These independent outputs must remain separate.
- W11 is an assembly closure between `MEMR` and `MEMR_D7` islands. See
  [factory-wire fidelity](factory-wire-route-fidelity.md) and
  [the routed audit](routed-refresh-audit.md) for layout qualification.

## Source observations

- [CAS row registration](../ref/photos/juku-pcb-2/cas-timing-row-registration.json)
  records the component-side D36.12/.13 tie. Its upstream driver and the
  adjacent seven-contact field remain unresolved.
- The factory wire table assigns W10 to D41.13–D50.1. That numbered wire
  is distinct from D59.10's timing-bundle marker.
- The sheet-2 STB crossing has no junction with the +12 V phase pull-up
  conductor. Keep STB and that supply separate; the board-model provenance
  retains the original image and crop identity.
- [D59 orientation audit](../ref/photos/juku-pcb-2/d59-orientation-audit.json)
  records the open annulus reached from D59.3. Its same-hole relationship to
  Z1 is unproved and remains a physical continuity target.
