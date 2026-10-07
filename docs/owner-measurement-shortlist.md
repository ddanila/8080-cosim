# Owner measurement shortlist

Status: **EVIDENCE HOLD**

This report assigns current source gaps to physical measurement tasks.
`READY` means required inputs and selected report markers are present
and the gap-to-task assignment checks pass. It does not rerun the cited
guards, validate every narrative request, or record completed measurements.
A recorded assembly placement failure remains `HOLD` and keeps this report
at `EVIDENCE HOLD`; generation succeeds so freshness CI can check it.
Missing markers and unexpected assembly failures still fail generation.

## Command

```sh
python3 scripts/report_owner_measurement_shortlist.py
```

## Input and Report Marker Checks

| Check | Status |
| --- | --- |
| Community request packet ready | PASS |
| PROM dump procedure exists | PASS |
| Physical D2/D6/D8/D94 tables are guarded | PASS |
| D2 constraint report generated | PASS |
| D30 section-B continuity closure guarded | PASS |
| D94 constraint report generated | PASS |
| FDC hardware handoff generated | PASS |
| FDC firmware profiles proved; archive-0037 direct-bus profile adopted | PASS |
| Beeper standalone toggle and JSON handoff guarded | PASS |
| Serial USART behavior guarded | PASS |
| Decap value boundary guarded | PASS |
| D41 timing connectivity source-closed | PASS |
| Memory timing connections guarded | PASS |
| I/O decode boundary guarded | PASS |
| .009 video / .006 RF disposition guarded | PASS |
| S4 interrupt boundary guarded | PASS |
| FDC functional-pin design hold is visible | PASS |
| Bring-up verification points generated | PASS |
| Source inventory PASS marker present | PASS |
| Cartridge BASIC boundary documented | PASS |
| .009 assembly drawing extraction guarded | HOLD |
| Factory Вид В modifications guarded | PASS |
| Source-PCB placement collision gate passes | PASS |

## Highest-value physical asks

P0 tasks block design release; P1 tasks resolve remaining physical details.
P2 includes preservation and authenticity follow-up; only tasks explicitly
described as optional may be skipped. Priority does not waive a release hold
in the owning evidence report. Use the linked evidence for photo coordinates
and source interpretation; record measurements separately.

### P0: D94 .092 D0 closure

Exact .009 sheets 1 and 3 close D9.7 CS7 to D94.15/D93.3, independently supported by owner D94.15-D93.3 continuity. With D94 removed, repeat-check D94.1 against D101.1, D2.15/-WREQ, and nearby support pins; either identify its hidden load or confirm the R8 2 kΩ pull-up is the only owner branch. Exact .009 sheets 1 and 3 connect the R8 pull-up and D94.1 to WREQ; test the corresponding remote path on the owner board before closing it. Optionally scope D101.7, D94.1, /RE, and /WE on port 1F to observe register-3 steering.

Purpose: closes the remaining D94 D0 physical boundary; the optional runtime capture validates steering but does not replace continuity.

Evidence: [d94-reconstruction-constraints.md](../docs/d94-reconstruction-constraints.md); [photo-registration.md](../docs/photo-registration.md); exact two-sided local-fit rows in [endpoints.csv](../ref/photos/juku-pcb-2/endpoints.csv).

### P0: PPI physical supply and orientation closure

With power removed, check physical D26.7 and D27.7 to an independently marked GND landing, then D27.26 and the end of its visible front trace near (1467,1993) in 200358952 to the marked +5 V landing. The nearest west solder annulus (3438,1811) is rejected by inverse photo registration; locate the actual opposite-face landing during inspection. D26.26 is already photo-traced to +5 V. Record exact package pin numbers using the right-edge notches, not the current routed pad numbers: both routed 90-degree DIP-40 footprints have left-edge notches and all 40 physical pin locations on each carry the wrong intended net. Correct footprint orientation and reroute only after the physical power checks are reconciled.

Purpose: closes the PPI power-route boundary and prevents the 40-pin permutation from reaching a fabricated board.

Evidence: [ppi-orientation-audit.md](../docs/ppi-orientation-audit.md); [d26-pin7-ground-chase.json](../ref/photos/juku-pcb-2/d26-pin7-ground-chase.json); [d27-pin7-ground-chase.json](../ref/photos/juku-pcb-2/d27-pin7-ground-chase.json); [d27-pin26-via-review.json](../ref/photos/juku-pcb-2/d27-pin26-via-review.json); [ppi-physical-pin-mapping.json](../docs/ppi-physical-pin-mapping.json).

### P0: D52 mux supply closure

Exact .009 sheet-2 microcircuit power table assigns К531КП14 pin 8 to ground and pin 16 to rail A/+5 V. D52 was the only КП14 instance missing those model nets; JSON and all three PCB pad net names are corrected, but no power track touches either 1.6 mm pad. With power off, verify the owner's physical D52.8 to known ground and D52.16 to known +5 V, then route each replica pad to its rail with signal clearance, rerun connectivity and DRC.

Purpose: closes two missing КП14 supply-pad connections without mistaking nearby signal tracks for power.

Evidence: [d52-supply-pin-correction.json](../ref/schematics/d52-supply-pin-correction.json); [main-board-erc-parity.md](../docs/main-board-erc-parity.md); [kp14-device-contract.json](../ref/video/kp14-device-contract.json).

### P0: D6 PROM footprint orientation and placement

Owner photos establish D6's right-facing notch: pin1 upper-right, pin8 upper-left, pin9 lower-left, pin16 lower-right. The source footprint uses −90 degrees; both routed variants retain +90 degrees and displaced pin sites. Use the [D6 photo audit](d6-owner-footprint-photo-audit.md) for the approximate placement and pin coordinates. Refit neighboring copper against multiple package contacts, preserve logical pin nets, and rerun full DRC/connectivity after correcting the routed boards. C87's nearby candidate holes remain unproved.

Purpose: corrects a photographed PROM end reversal that would invalidate physical pin and local copper placement.

Evidence: [d6-owner-footprint-photo-audit.md](../docs/d6-owner-footprint-photo-audit.md); [PXL_20260710_200411500.jpg](../ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg); [local-package-registration.json](../ref/photos/juku-pcb-2/local-package-registration.json); source and routed KiCad PCBs.

### P0: D8/D92 supply closure

The .009 D8 К155РЕ3 pinout gives pin8=GND and pin16=+5 V; D92 К555ЛЕ4 is a 74LS27-class triple 3-input NOR with pin7=GND and pin14=+5 V. The logical model and all three PCB pad net names are corrected. Both routed variants now connect D92.14 to +5 V through a DRC-checked via and D8.8 to ground with a short F.Cu track; D8.16 and D92.7 remain without power tracks, and the source PCB remains unrouted at all four pads. With power off, confirm owner D8.8/D92.7 to known ground and D8.16/D92.14 to known +5 V. Route the two remaining replica pads around nearby signal traces, then rerun connectivity and DRC.

Purpose: closes four omitted package-supply conductors and prevents a 74LS02 substitute for the D92 triple 3-input NOR.

Evidence: [d8-d92-supply-pin-correction.json](../ref/schematics/d8-d92-supply-pin-correction.json); [prom-dump-procedure.md](../docs/prom-dump-procedure.md); TI SN74LS27 datasheet; [main-board-erc-parity.md](../docs/main-board-erc-parity.md).

### P0: D2 PROM package supply closure

D2 К556РТ4 has package GND pin8 and +5 V pin16, as on the matching D6 and in the tracked 82S126 pinout. Its already-grounded pins13/14 are chip-enable inputs, not package supplies. JSON and all three PCB pad net names now include D2.8/D2.16, but neither pad has touching power copper. With power off, confirm the owner D2.8 to known ground and D2.16 to known +5 V, then route the replica pads with signal clearance and rerun connectivity and DRC.

Purpose: closes two omitted D2 package-supply conductors without confusing chip-enable GND ties with VSS.

Evidence: [d2-package-supply-correction.json](../ref/schematics/d2-package-supply-correction.json); [k556rt4-pinout.txt](../ref/datasheets/k556rt4-pinout.txt); [d2-reconstruction-constraints.md](../docs/d2-reconstruction-constraints.md); [main-board-erc-parity.md](../docs/main-board-erc-parity.md).

### P0: D2 PROM address-input continuity

Five D2 address names remain scan/model assignments after the D4 photo-route claims were withdrawn. The July solder photo follows D2.1 to a via near (2185,1498), D2.5 to (2640,1685), D2.6 to (2500,1745), and D2.7 to (2100,1840); D2.3 has no visible solder-face departure in two overlapping views. With power off, verify each pad-to-via segment, then test each via or D2.3 directly against the corresponding known raw CPU address pad and buffered D4/D107 candidate. Record positive and negative results before changing A10/A14/A12/A15/A9. The front ring near July (1227,2002)/May (1768,1650) is only a D2.6 candidate.

Purpose: settles five PROM address-input assignments and whether the source uses raw or buffered address lines.

Evidence: [d2-d4-column-row-audit.json](../ref/photos/juku-pcb-2/d2-d4-column-row-audit.json); [photo-registration.md](../docs/photo-registration.md); [d2-reconstruction-constraints.md](../docs/d2-reconstruction-constraints.md); exact .009 sheet-1 overview `PXL_20260718_101754468.jpg`.

### P0: D34 video logic package supply closure

The exact К555ЛП5 datasheet fixes physical D34.7=GND and D34.14=+5 V. D34.5 ground and D34.1/D34.13 high are functional input ties, not package supplies. JSON and all three PCB pad net names include pins7/14. Both routed variants now connect D34.14 to +5 V and D34.7 to ground by a back-layer detour around D34_SIG, with no new DRC violation and two fewer unconnected records; the source PCB remains unrouted at these pads. With power off, confirm owner D34.7 to known ground and D34.14 to known +5 V before treating the original-board supplies as closed.

Purpose: closes two omitted supply conductors on the video output logic device.

Evidence: [d34-package-supply-correction.json](../ref/schematics/d34-package-supply-correction.json); [k555lp5-eandc.pdf](../ref/datasheets/k555lp5-eandc.pdf); [main-board-erc-parity.md](../docs/main-board-erc-parity.md).

### P0: D104 pin16 supply conflict

The exact .009 sheet-1 power table assigns К170УП2 pin15 to +5 V and pin8 to ground but leaves its +12 V cell blank; the preserved device pinout calls pin16 a +12 V supply. All three PCB variants leave D104.16 netless, and a white cable covers its owner front contact. A D11-local four-corner cross-face fit photo-registers D104's solder field; pin16 is near (912,1620) in 200509593 / (2710,1480) in 200506061. With power off, test that joint against independently marked X8 +12 V, D104.15/+5 V, and ground before assigning a replica rail or receiver substitute. The earlier D11-based (181.88,31.90) mm D104 placement estimate is retracted: independent panorama registration places D104 near its current PCB centre and instead flags D11 placement for separate review.

Purpose: resolves the exact-source versus device-contract discrepancy at the serial receiver supply.

Evidence: [d104-pin16-rail-conflict.json](../ref/schematics/d104-pin16-rail-conflict.json); [k170up2-pinout.txt](../ref/datasheets/k170up2-pinout.txt); exact .009 sheet-1 power table; [juku-serial-19200-investigation.md](../docs/juku-serial-19200-investigation.md).

### P0: D11 physical placement and copper

Two-view owner registration places D11 near (201.01,71.49) mm, matching the source PCB; both routed boards remain centered at (185.50,65.70) mm. Correct routed D12 and D11 placements together using the [cross-view audit](../ref/photos/juku-pcb-2/d11-placement-crossview-audit.json), redesign both copper layers, preserve every pin-net assignment, and rerun DRC/connectivity.

Purpose: restores the photographed package location while retaining the established D11 electrical mapping.

Evidence: [d11-placement-crossview-audit.json](../ref/photos/juku-pcb-2/d11-placement-crossview-audit.json); [photo-registration.md](../docs/photo-registration.md); source and routed KiCad PCBs.

### P0: D41 shift-register supply closure

With power off, check D41.7 to known GND and D41.14 to known +5 V. Follow the two open-hole pairs in the [supply review](../ref/photos/juku-pcb-2/d41-supply-pin-review.json), checking each same-hole match and D41.14-to-D38.1 continuity separately: the candidate solder route reaches CAS, conflicting with the D41.14/VCC device contract. Revisit pin/hole registration if that conflict is confirmed. The replica routes do not prove the owner-board rails. Confirm both C83 front-to-solder lead matches using the [gap review](../ref/photos/juku-pcb-2/c83-d41-d40-gap-pair-review.json) before assigning either pad.

Purpose: confirms the owner D41 rails after the replica routes were repaired, and tests the C83 upper ground-side solder anchor.

Evidence: [d41-supply-pin-review.json](../ref/photos/juku-pcb-2/d41-supply-pin-review.json); [ir16-device-contract.json](../ref/video/ir16-device-contract.json); [main-board-erc-parity.md](../docs/main-board-erc-parity.md); [c83-d41-d40-gap-pair-review.json](../ref/photos/juku-pcb-2/c83-d41-d40-gap-pair-review.json).

### P0: D42/D43 orientation and supply closure

Owner photos establish right-facing notches and trace D42.7/D43.7 to GND and D42.14/D43.14 to +5 V through the D58/D26 shared strips. Optional power-off continuity provides independent electrical confirmation. The source PCB and generator use 270-degree footprints; both routed variants retain 90-degree pin sites. Correct the routed orientation with a pin-aware copper reroute and DRC/connectivity review; rotating the footprints alone creates shorts. See the [orientation audit](../ref/photos/juku-pcb-2/d42-d43-orientation-audit.json) for photo contacts and rail paths.

Purpose: prevents the photographed 14-pin end reversal from reaching fabrication.

Evidence: [d42-d43-orientation-audit.json](../ref/photos/juku-pcb-2/d42-d43-orientation-audit.json); [d26-d58-plus5-strip-review.json](../ref/photos/juku-pcb-2/d26-d58-plus5-strip-review.json); [d42-d43-orientation-copper-impact.json](../ref/routing/d42-d43-orientation-copper-impact.json); [sheet2-ir16-power-table-conflict.json](../ref/schematics/sheet2-ir16-power-table-conflict.json).

### P0: D58 and X9 landing placement

Register D58 against its photographed right-facing notch and approximate center (181.4,260.0) mm; the source center remains (183.0,243.1) mm and both routed variants retain the old rotation and center. Its pin10/GND and pin20/+5 V paths are photo-supported; optional power-off continuity provides electrical confirmation. For the fifteen-site band under D26, meter site10 through its via to D26.27/DB7 and separately D26.28/DB6. Physically identify the fourteen X9 conductor holes and map their factory A numbers before moving footprints or rerouting. Sites9/12 share the +5 V rail but their individual A53/A54 identities and cable membership remain open; the sheath hides conductor entries, so do not infer membership by subtracting site10. Use the linked registration records for probe coordinates.

Purpose: resolves the D58 physical position and X9 landings without moving one provisional footprint into another.

Evidence: [d58-x9-solder-relative-fit.json](../ref/photos/juku-pcb-2/d58-x9-solder-relative-fit.json); [d26-d58-plus5-strip-review.json](../ref/photos/juku-pcb-2/d26-d58-plus5-strip-review.json); [x9-fifteen-site-band-review.json](../ref/photos/juku-pcb-2/x9-fifteen-site-band-review.json); [x9-site10-via-review.json](../ref/photos/juku-pcb-2/x9-site10-via-review.json); [x9-solder-row-registration.json](../ref/photos/juku-pcb-2/x9-solder-row-registration.json); [x9-plus5-rail-site-review.json](../ref/photos/juku-pcb-2/x9-plus5-rail-site-review.json); factory X9 ribbon drawing.

### P0: D59 oscillator package orientation

The owner package has a right-facing notch; the source uses 270 degrees while both routed variants retain 90-degree pin sites. A footprint-only rotation creates shorts, so reroute with physical pin-net and DRC/connectivity review. With power off, check D59.7 to GND and D59.14 to +5 V. Confirm the photographed D59.14 joins to R32 right and the pale 1K0 body left in the R38 position, then test R32 left to D59.4 and D59.9. The observed R32/P5V join conflicts with the source OSC_FB/PST_CLK endpoints; resolve it before changing the model or routed copper. Use the [orientation audit](../ref/photos/juku-pcb-2/d59-orientation-audit.json) for registered contacts and trace evidence.

Purpose: prevents oscillator and supply nets from using the reversed physical pin sites.

Evidence: [d59-orientation-audit.json](../ref/photos/juku-pcb-2/d59-orientation-audit.json); [d26-d58-plus5-strip-review.json](../ref/photos/juku-pcb-2/d26-d58-plus5-strip-review.json); source and routed KiCad PCBs.

### P0: X8 power capacitors and routed rail correction

With power off, identify each fitted body and check it against independently marked X8 rails: C31 +5 V/GND; C32 +12 V/GND, positive at +12 V; C33 GND/−12 V, positive at GND; C92 GND/−12 V; C93 GND/+12 V. The corrected replica net assignments and routes do not establish these owner joins. Register all six electrolytic solder joints and the three E4 selector joints before replacing the 2 mm radial footprints still used in all PCB variants. A 25 mm axial trial overlaps E4; use the [footprint audit](x8-electrolytic-footprint-audit.md), then replace and reroute only after the joint fit.

Purpose: confirms the original-board capacitor identities and rails after the replica's modeled-pad/routed-copper mismatches were repaired.

Evidence: [x8-power-capacitor-rail-correction.json](../ref/schematics/x8-power-capacitor-rail-correction.json); [x8-electrolytic-footprint-audit.md](../docs/x8-electrolytic-footprint-audit.md); [main-board-erc-parity.md](../docs/main-board-erc-parity.md); [c93-power-corner-candidate-review.json](../ref/photos/juku-pcb-2/c93-power-corner-candidate-review.json); [c92-reset-corner-body-review.json](../ref/photos/juku-pcb-2/c92-reset-corner-body-review.json).

### P0: FDC interrupt/buffer continuity

First confirm physical D96.13 CLR2_N↔D99.10 B2 continuity and check D99.10↔D100.11 T separately; then identify each remote source. Also confirm D96.9 Q2↔D101.4/R92.1 continuity, D96.11 CLK2↔D94.2/D99.9/R89.1 continuity, D96.11↔D96.10 isolation at the unmarked drawing crossing, and D100.11 T's sheet-1 source; confirm D100.9 OE_N↔D99.12 Q2_N continuity separately. Exact sheet 3 closes raw D93 DRQ/INTRQ through D28.11/.13, wired outputs D28.10/.12, R93/R95, and D96.10/.12, and the SN74LS74A truth table makes that shared PRE2_N/D2 wiring set-only while CLR2_N is inactive. Capture D96.8-.13 during request and acknowledge; separately capture WREQ_N at D96.1/.4 with Q1/.5 and Q1_N/.6 because simultaneous async release does not define section-1 restart phase. Registered solder photo leaves D96.9 without a visible local B.Cu departure, but a narrow B.Cu line from D96.11 appears to reach registered D28.11/DRQ, contrary to the separate exact-source CLK2 and DRQ nets. Power off: check D96.11↔D28.11 directly before changing either model net; do not infer a PIC join from the non-unique drawing continuation marks. D100.6 is source-closed to D101.9 write precompensation; the adopted archive-0037 RomBios 3.43m pair already fixes the replica's direct-bus/NOP profile.

Purpose: resolves the set-only D96 section-2 contradiction without reopening source-closed paths or the adopted firmware profile.

Evidence: [d96-irq-photo-exhaustion.json](../ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json); [fdc-bus-polarity.md](../docs/fdc-bus-polarity.md); [fdc-hardware-handoff.md](../docs/fdc-hardware-handoff.md); [replica-bringup-verification-points.md](../docs/replica-bringup-verification-points.md); [PLAN.md](../PLAN.md) P0 gate.

### P0: memory-decode stragglers

D6.15-D105.1 is now closed to D7.8 as the I/O-cycle-active-high qualifier, and D105.3 is independently closed as qualified peripheral /WR. Recheck only the surprising D13.12-D16.13 report with D16 removed. Exact .009 sheet 1 closes C99.2 to the ground symbol. The corrected D9-local fit maps the provisional bare C99 front pair (2508,1782)/(2680,1782) in July photo 200411500 (or (1440,1990)/(1600,1990) in May 201933909) to distinct solder joints (3040,1492)/(2875,1495) in 200525009; a third joint near (2818,1515) matches R17 lower and visibly bridges to the right C99 candidate on B.Cu. With power removed, confirm each front-to-back same hole directly, then check the left candidate to known ground and the right candidate to R17/D9.6; the left candidate B.Cu trace visibly reaches registered D2.14 near (3450,1580) in 200525009, source-grounded on exact .009 sheet 1, so meter that photographed join and an independent ground contact. Inspect C99 population; confirm the source-drawn D7.5↔D29.3 -INHIB join at solder probes near (2300,1029) in 200525009 and (2393,1588) in 200509593, then chase its unread upstream source; close remaining D36 timing feeds; the D6.1<-D3.4<-/PC1, D6.2<-D3.6<-/PC0, D6.11/-WREQ, D6.12-D8.15, enable, and RAM-read endpoint chains are already closed.

Purpose: corroborates the validated D6 decode path and resolves the remaining INHIB, passive-return, and RAM/video timing boundaries before netlist freeze; the D6 I/O-cycle address qualifier is already owner-closed.

Evidence: [d6-runtime-path-diagnostic.md](../docs/d6-runtime-path-diagnostic.md); [d6-physical-decode.md](../docs/d6-physical-decode.md); [io-decode-boundary.md](../docs/io-decode-boundary.md); [memory-timing-boundary.md](../docs/memory-timing-boundary.md); [d41-timing-boundary.md](../docs/d41-timing-boundary.md); [PLAN.md](../PLAN.md) P0 connectivity gate.

### P0: D7.3 source join and owner continuity

With power off, verify the source-drawn D7.3↔D29.2 AMW_N join through the registered front ring, candidate opposite-face hole, far annulus, and D29.2 waypoint. The [D7 review](d7-gates-source-review.md) and [D29.2 chase](../ref/photos/juku-pcb-2/d29-pin2-front-chase.json) locate each probe; cable-covered ends and the first same-hole match still require continuity. Trace further loads. Preserve D7.11/PROM_EN and D105.3/qualified /WR as separate nets; their direct continuity check is optional, not a source-required tie. Separately confirm D104.7↔R30 lower, R30 lower↔known GND, and R30 upper↔D12.3/OC SOUT. Measure R30 isolated if needed (source nominal 33 kΩ; marking obscured). The photographed D104.7/R30 join does not prove the owner ground return or resistance.

Purpose: covers the D7 P0 pin boundary and checks whether the source-assigned D104/R30 ground polarity matches the owner board.

Evidence: [main-board-unresolved-endpoints.csv](../docs/main-board-unresolved-endpoints.csv); [d7-gates-source-review.md](../docs/d7-gates-source-review.md); [d105-pin3-photo-review.json](../ref/photos/juku-pcb-2/d105-pin3-photo-review.json); [d29-pin2-front-chase.json](../ref/photos/juku-pcb-2/d29-pin2-front-chase.json); [d104-pin7-r30-photo-review.json](../ref/photos/juku-pcb-2/d104-pin7-r30-photo-review.json); [io-decode-boundary.md](../docs/io-decode-boundary.md); [serial-handoff.md](../docs/serial-handoff.md).

### P0: factory Вид В pad mapping

The corrected marked D56 component fit cross-aligns with the independent solder fit, retaining D56.1/D56.9 ground and the D56.5/D56.12 pad identities. D56.5->D34.9 and D56.12->D55.15/.18 remain owner-closed functional nets. Identify only the installed item-159 material and auxiliary-annulus/adjacent-rail disposition. Note 11 proves position 150 is tubing, not a cut, and position 159 remains an unexpanded solder-location callout. D15 is photo-closed as the cut A2/A1 bridge and needs no continuity probe; D14 row numbering, the local D32.4/GND-to-D14.1 link, and D14.4-to-corrected-fifth-annulus stem are photo-registered; exact .009 sheet-1 power table assigns D14.4 to GND. Meter the annulus to D14.4 and independently known ground before accepting the owner rail. The D11-local cross-face fit places D14.2 solder near (2426,1376), D14.7 near (2288,1376), and the fifth auxiliary drill near (2424,1513) in 200506061; retire the older broad-projection and geometry-only seeds. Confirm these same-hole pairs and meter D14.2 and D14.7 to their remote endpoints, the fifth solder drill to its photo-joined west strip terminal near (2074,1521) in 200506061, repeated as fifth (604,1644) and west terminal (241,1656) in 200509593; in that second view the same strip photo-joins registered D29.10 near (2057,1588), named GND by the exact source. Meter fifth↔D29.10 and D29.10↔independently known ground, then search any other remote conductors, and the three long drawn traces and right-row dogleg. Position 159 does not prove replacements; at D11 the L trace and four front landings are registered in two component views. The lower_exit coordinate was corrected to a visible drill near (2209,2305) in 200358952 / (813,2456) in 200402344; its package-local solder projection near (2771,2078) in 200506061 has a nearby open-hole candidate near (2776,2094), repeated near (978,2234) in 200509593. Confirm that same-hole match by continuity before adopting it. The corrected D11 solder fit moves the field four joint rows, but the complete four-hole pattern remains unproved. Two native component crops show bare substrate in the local bridge_left-to-position159_junction gap. The D11-local solder projections near (2791,1961)/(2746,1941) in 200506061 fall close to two separate annuli with no visible local B.Cu bridge. Confirm each same-hole match, then test left-to-junction continuity for a remote or fitted connection, then map D11 pin/net and remote endpoints; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity.

Purpose: proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release.

Evidence: [factory-modification-disposition.md](../docs/factory-modification-disposition.md); [PXL_20260711_114626340.jpg](../ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg).

### P0: FDC support signal dispositions

pin-level continuity or an explicit redesign/DNP decision for the 4 still-open support devices D96, D99, D100, and D101. For D96, confirm Q2/pin9↔D101.4/R92.1 continuity, CLK2/pin11↔D94.2/D99.9 continuity, pin11↔D28.11/DRQ candidate copper and pin11↔pin10 isolation, and direct D96.13↔D99.10 continuity plus D99.10↔D100.11 T before tracing their sheet-1 sources independently; preserve its source-closed section-1 copper and exact local D28.10/.12-D96.10/.12 wiring. Section 1 divides after release but has undefined restart phase because WREQ asserts both async controls; the shared section-2 PRE2_N/D2 node is set-only while its D99.10-joined CLR2_N source is inactive. For D99 locate E12 and verify post-2 continuity to D99.2, post-1 continuity to D99.5, and the fitted 2-3 bridge; sheet 3 closes post 3 to D93.28/D100.3 HLD, so confirm that physical continuation. Locate E11 independently: source post 1 reaches D99.5 Q2, post 2 reaches D93.32 READY, and post 3 reaches D28.6/R84; verify those physical continuities and the fitted 2-3 bridge. Confirm D99.4↔D93.23 HLT continuity: the full sheet-3 overview joins them on the rail above the separate D94.14-D101.7 rail; optional D99.4↔D94.14 isolation can corroborate this distinction. Confirm D99.5 Q2↔D100.7 A7 and D99.12 Q2_N↔D100.9 OE_N continuity separately, identify D100.11 T remote source, then confirm D26.16↔D99.11 MOTOR EN continuity, and identify the shared D99.10/D96.13 source; pin3 is already physically grounded and pin13 is a source-proved NC. For D101 confirm D101.1↔D26.38 IMDRG continuity; optionally check D101.7↔D101.9 isolation to corroborate the exact sheet-3 unmarked crossing and separate target solder landings; owner continuity already closes D101.7↔D94.14, while sheet 3 sends D101.9 to D100.6; confirm D96.9 and pins 3, 5, and 6 each against pin4/R92.1/R99.2; test pin3 to its photo-traced solder annulus (2280,1213) and that annulus to pin4 separately, since their exposed B.Cu departures remain distinct; preserve the source-closed D97/D102/D101 write-precomp chain. Also preserve the source-closed D28/D95/D97/D98/D102/D106 paths. Exact-revision sheet 3 explicitly omits D97.13, D98.9/.10, and D102.4 in this area. Closed timing paths need waveform validation at bring-up, not another continuity probe.

Purpose: completes only the genuinely open support-circuit context without re-probing source-closed timing paths.

Evidence: [fdc-hardware-handoff.md](../docs/fdc-hardware-handoff.md); [d99-reconstruction-constraints.md](../docs/d99-reconstruction-constraints.md); [d101-reconstruction-constraints.md](../docs/d101-reconstruction-constraints.md); [fdc-unused-pin-dispositions.md](../ref/schematics/fdc-unused-pin-dispositions.md); [fdc-clock-mux-map.md](../ref/schematics/fdc-clock-mux-map.md); [fdc-recovery-counter-map.md](../ref/schematics/fdc-recovery-counter-map.md); [fdc-read-clock-toggle-map.md](../ref/schematics/fdc-read-clock-toggle-map.md); [fdc-write-precomp-map.md](../ref/schematics/fdc-write-precomp-map.md); [PLAN.md](../PLAN.md) P0 connectivity gate.

### P0: ROM-select and clock passive terminals

The assembly-to-owner photo comparison identifies the eight populated bank bodies left to right as R28 through R21; continuity-register both pads of each against D8 output pins and +5 V, since the schematic gives only collective R21...R28 labeling. Factory placement and owner photo identify the upper 330R body as R35 across the PHI2TTL/D35.13 split. Confirm its projected upper solder joint near (1830,2010) in 200522685 is the same hole as the R35 upper lead, then meter that lead and its visibly connected east annulus near (2190,2037) to D29.1/PHI2TTL; do not equate the annulus with PHI2TTL from the photo alone. Below it, the lower body occupies the R106 position and its upright photo marking reads 510R, conflicting with schematic 910; measure it and test both leads against D35.13 and ground. No separate C29 body is exposed left of R106; inspect the adjacent filled-looking joints at (2258,2517) and (2258,2576) and the downstream open annulus at (2264,2745), then continuity-confirm the photo-supported upper-to-R35-lower/R106-upper and middle-to-D56.8-ground routes, identify the post-R35 node's continuation to photographed D35.13 near (2408,1540) in 200445914 / solder candidate (1839,719) in 200530933.MP, and confirm population and physical value before fitting it (the native-sheet convention gives a 56 pF nominal). Exact sheet 2 defines rail B as +12 V and places R37 between +12 V and D35.10/PHI1, R36 separately between +12 V and D35.12/PHI2. Factory placement and overlapping owner photos identify the populated R37/R36 bodies immediately left of D1; continuity-register their individual pads against these three anchors. Record remaining clock-network values and owner population. All eight fitted ROM-bank bodies directly read 1K0 in the May close-up; map their individual D8 joins and confirm the common rail before promoting the bank from provisional individual D8-output mappings.

Purpose: closes physical ROM-select pull-up mappings and clock-shaping population before PCB routing.

Evidence: [omitted-resistor-census.md](../docs/omitted-resistor-census.md); [phi2ttl-d29-clock-route.md](../docs/phi2ttl-d29-clock-route.md); [board-fidelity-gap-ledger.md](../docs/board-fidelity-gap-ledger.md).

### P0: D38 factory-wire landing identities

With power off, test the white-wire front solder pool near (1810,2696) in owner component photo 200418174 against each adjacent vertical front strip and D38.8. The solder-side projection near (2400,2370) in 200522685 lands on bare substrate; separately test the nearby joint around (2380,2345) to the wire pool and D38.8 before calling it the same hole. The printed 9 near this search area does not identify A8B or A9B. Locate A9B/D38.12 independently, and verify each factory wire against its source-drawn endpoint before assigning a replica pad or route.

Purpose: resolves D38-side factory modification landings that remain on design hold after corrected photo registration.

Evidence: [a8b-corrected-trace-review.json](../ref/photos/juku-pcb-2/a8b-corrected-trace-review.json); [a9b-corrected-trace-review.json](../ref/photos/juku-pcb-2/a9b-corrected-trace-review.json); [factory-wire-route-fidelity.md](../docs/factory-wire-route-fidelity.md).

### P1: D25 shared-strip rail corroboration

Owner top-edge photos confirm the D25/D23/D24 КР580ВА87 and D29 КР580ВА86 row; clear left notches support the modeled 90-degree D23/D24/D29 footprints. The exact .009 assembly draws D25 with a left-facing notch beside C74, while its owner molded ends look flat. Its mirrored lower-left solder pair near x2755/2805 joins the same uninterrupted broad strip as D23's known pin9/pin10 ground pair, independently supporting the modeled left-facing D25 pin sequence on the owner board. With power off, meter that common strip and D25 physical pin10 to an independently marked ground landing, then D25 pin20 to marked +5 V, to confirm owner rail polarity. The corrected seam fit matches front gap annulus (1012,1255) to the +5 V-side upper spur near solder (2705,1390), and front lower hole (1005,1517) to a drilled spur on the shared ground strip near (2705,1647). The other lower front feature near y1465 may share the strip, but its backside drill is obscured. Confirm these rail joins and determine which lower hole was intended for C74 before assigning a footprint or population; keep the gap site separate from the D25 pin10 check.

Purpose: corroborates the shared strip's ground polarity independently of D23's device contract.

Evidence: [top-bus-buffer-population-audit.json](../ref/photos/juku-pcb-2/top-bus-buffer-population-audit.json); [d25-ground-strip-orientation-review.json](../ref/photos/juku-pcb-2/d25-ground-strip-orientation-review.json); [c74-d25-d23-gap-review.json](../ref/photos/juku-pcb-2/c74-d25-d23-gap-review.json); source and routed KiCad PCBs.

### P1: timing and video-source boundaries

With power removed, corroborate the photographed B.Cu join from D34.4 near (1055,2113) to D38.4 near (2245,2119) in July solder photo 200522685, and D34.4 to the open annulus near (970,2114). The two tag-2 pins are now one modeled net; identify its still-unknown upstream driver. Trace D58.11 tag 5 at solder (3730,2310) in 200530933.MP and D59.10 tag 10 at the reworked solder crown (2780,2450) in 200534267; both immediate B.Cu departures are visually absent or obscured. Check D41.6 rail-17 solder joint near (2274,1620) in 200522685 to D36.2, then trace its remote driver; the joint sits visibly apart from adjacent grounded straps. Keep D59.10 separate from D57.13 SOUND. The July and independent May component photos already show an F.Cu tie between D36.12 and D36.13; optionally meter the two joints near (1830,1195)/(1830,1250) in 200445914 as an electrical cross-check. In solder photo 200530933.MP, test whether either front joint is the same hole as the seven-contact candidate at x1715/x1895, rows y115-475; also match both physical R57 leads across faces. The D40-local projection misses the expected R57 solder leads and cannot identify this field. Only after a direct same-hole match, trace the common CAS-input source. Check whether the D39.10/D103.2/D42.9/D43.9 XTAL16M island actually joins D59.2/.3 OSC. Trace the downstream consumer of D57.17 SYNC B without restoring its disproved D56-trigger join. Record endpoints, resistance, and chip-in/chip-out state; powered waveforms can corroborate timing after connectivity is established.

Purpose: identifies the remaining timing-tag, CAS, crystal, and SYNC B remote drivers after the D34.4/D38.4 local copper join was photo-closed.

Evidence: [memory-timing-boundary.md](../docs/memory-timing-boundary.md); [owner-measured-facts.md](../docs/owner-measured-facts.md); [board-fidelity-gap-ledger.md](../docs/board-fidelity-gap-ledger.md); [d34-pin4-tag2-via-review.json](../ref/photos/juku-pcb-2/d34-pin4-tag2-via-review.json); [cas-timing-row-registration.json](../ref/photos/juku-pcb-2/cas-timing-row-registration.json).

### P1: D56 timing-resistor identities

With power removed, measure each lead of the left-of-D56 fitted 33K body to D56.15/C8.1 and known +5 V. The .009 assembly places R59 on D56's right, so its value alone does not identify the left body. Separately read or isolate-measure the single upright body to D56's right: its front lead search centers are near (3505,1005)/(3505,1245) in 200445914, projecting only broadly near (725,155)/(725,399) in solder view 200530933, where no unique same-hole pair is proved. Identify the actual holes, then test each lead against both timing branches: R59/D56.15/C8.1 and R47/D56.7/C7.1, plus +5 V. Do not assign either body from its drawing height or apparent front-side proximity alone; record which physical lead reaches each net and whether the resistor must be lifted for an isolated value measurement.

Purpose: distinguishes the two observed bodies from the source R47/R59 references and closes the physical timing network without relying on placement alone.

Evidence: [r59-candidate-registration.json](../ref/photos/juku-pcb-2/r59-candidate-registration.json); [r109-r110-d56-review.json](../ref/photos/juku-pcb-2/r109-r110-d56-review.json); exact .009 sheet-2 D56 detail.

### P1: control and peripheral continuation boundaries

Exact .009 sheet 1 draws D1.24 WAIT through a filled junction and fold into D105.1; owner continuity instead closes D105.1 to D7.8/D6.15 IO_CYCLE_H, with D1.24 untested. With power removed, test D1.24 directly to D105.1, D7.8, and D6.15 before merging or rejecting that source-drawn path; use the corrected D1.24 solder contact near (2580,2381) in 200527310 and the photo-closed westward B.Cu run to open annulus (1830,2395), four-hole matched to component annulus (1910,2635) in 200411500, as the next probe waypoint; the front line passes beneath the assembly-position R12 1K0 body beside D2 without a visible lead join. A four-feature two-face fit places R12 left/right joints at solder (1995,1945)/(1770,1945), and visible B.Cu closes the left joint to registered D4.11/source +5 V. The right joint reaches matched front/solder open hole (1993,2302)/(1745,2058), whose narrow B.Cu run goes west beyond the 200527310 tile without a known endpoint. Check the matched WAIT annulus separately to R12 left/+5 V, R12 right/-WREQ, and D2.15 before assigning its continuation. Check D9.7 decoder output separately from D94.15/D93.3 FDC enable; D10.22 IR4/TAPE RUN INT to its actual source or confirm the FDC-revision continuation ends; the owner front photo 200455512 visibly has the .009 assembly E8 3–4 white wire fitted below D26; confirm D26.22 PB4↔both wire ends↔E8.4/CONTRDAT continuation 909, D26.23 PB5↔E8.2, and PB5 isolation from the wire; probe E8.4 against full-band solder site6 near (2140,2375), whose front joint is reached by exposed E8.4 copper, then identify the physical A50 hole for source-proved X9.9 before restoring the now-open PB4-to-A50 route; the replica netlist and pads have been corrected to PB4 while the former PB5 route was removed; if a controlled powered PPI read is available, select columns 8–15, toggle one S21 switch, and record whether Port B bit4 or bit5 changes together with the installed D15/D16 ROM identity, since five archived Ekta images mask PB5 despite the fitted .009 PB4 bridge; D29.1 PHI2TTL/CCLCK through the D5/D105 crossing region; separately D29.2↔D7.3; D12.6/.7 to X1.114C -INT4 and D12.5 to X2.214/D10.IR0/R104.1 with R104.2 to +5 V; confirm R18 upper to D12.3/S_OC via their distinct local solder departures: D12.3 near (2723,200) runs to open hole (2837,185), while R18 upper near (3004,363) runs to separate open hole (2803,367) in 200522685; test each short branch and then the branches against each other, preserving the photo-closed R18 lower→D3.11/SER_TXD bar; and off-board S1.3. The exact .009 sheet draws R15=12k on D26.14/D3.5 and R16=12k on D26.15/D3.3 to ground. Assembly and owner photos place R15 vertically right of D3 and R16 horizontally below D3; the adjacent 2 kΩ pair left of D3 is R10/R9. The actual R15 lower solder joint is photo-bridged to D3.5; confirm that continuity, probe its upper joint near (2635,315) in 200522685 and the front annulus (1540,260) in 200418174 against +5 V/GND, then measure R15 isolated. The additional 200506061 solder tile has no unique same-hole annulus at the D3-local search near (2067–2115,1477), so do not select a neighboring rail by proximity. The R16 right candidate near (2635,855) is photo-closed through a front annulus and backside bar to D3.3; optionally meter-confirm it to D26.15, then probe the left return candidate near solder (2855,855), its short west spur to open hole (2800,860), and the separate front annulus near (1338,1255) against +5 V/GND; two local package fits exclude the west solder hole as the front annulus's direct counterpart. A separate open hole near (2860,910) in 200522685, repeated near (795,800) in 200525009, is the closest same-hole candidate but sits 26 px north of the local fit; test it separately. Measure R16 isolated. This resolves the owner-reported +5 V return against the source ground bars. Record exact remote pins or confirmed NC/unused dispositions. Keep the already-closed D94 local FDC controls, X2 PA1/PA5 contact pair, and S4 interrupt changeover distinct.

Purpose: covers the remaining control continuations and the two D26 pull-up identities and values without reopening source-closed X2 contacts or owner-measured signal joins.

Evidence: [board-fidelity-gap-ledger.md](../docs/board-fidelity-gap-ledger.md); `kicad/juku.board.json` X2 provenance; [io-decode-boundary.md](../docs/io-decode-boundary.md); [d94-reconstruction-constraints.md](../docs/d94-reconstruction-constraints.md); [s4-interrupt-boundary.md](../docs/s4-interrupt-boundary.md); [replica-bringup-verification-points.md](../docs/replica-bringup-verification-points.md).

### P1: .009 FDC/analog passive continuity

trace both leads of factory-positioned C9/C10/C11/C15; Later July photo 202708344 shows a fitted C12-position green bypass whose visible upper/lower lap leads reach D100.20/+5 V and D94.8/GND; earlier May and July views show the site bare. Meter those two joints if electrical corroboration is needed, identify its value and fitting history, and replace the provisional C12 through-hole pad geometry before assigning C12.1/.2. The factory table closes A:3/A:4 to bracket X6, but the A:3 joint is beside VT2/R65 and is not coincident with VD3; test A:3/X6.1 against VT2 emitter, both R65 leads, and both VD3 leads before assigning its net. Check A:4/X6.2 to ground. Identify VD3’s marked cathode end and test it to R66.2/R67.1, then test its other end to ground: the exact .009 drawing requires that polarity but the current model reverses the diode pin names. Test R67.2 to the source-drawn VT2 base/R62.2/R63.2/R64.1 junction. Confirm the corrected R67.2 upper joint near front (3365,1730) to solder (869,953) and its visible B.Cu run to open annulus (1295,958); then test that annulus and R67.2 separately to VT2 base/R62.2/R63.2/R64.1. D102/D97 inverse fits search for its front counterpart near (2937,1739)/(2905,1736), with no unique visible drill in either July or independently registered May view; do not snap it to nearby front annuli. The former no-via conclusion came from a wrong front coordinate; do not restore the revision-superseded .006 VT3/VT4 RF nets.

Purpose: turns the remaining eleven explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement.

Evidence: [video-analog-boundary.md](../docs/video-analog-boundary.md); [source-pcb-drc.md](../docs/source-pcb-drc.md); [r67-photo-exhaustion.json](../ref/photos/juku-pcb-2/r67-photo-exhaustion.json); [x6-cable-registration.json](../ref/photos/juku-pcb-2/x6-cable-registration.json); [vd3-polarity-photo-review.json](../ref/photos/juku-pcb-2/vd3-polarity-photo-review.json).

### P1: unidentified 220-ohm body near D98

Identify the historical refdes and measure both endpoints of the photographed 220-ohm body recorded as RUNK1 below-left of D98; test each lead against nearby D28/D98/FDC support pins with the board unpowered and record negative controls. Owner continuity already disproved its former R94 identity, so retain the actual R94=10 kΩ path above D28 separately.

Purpose: replaces a placement-only placeholder with the fitted component's measured circuit role.

Evidence: `kicad/juku.board.json` RUNK1 provenance and boundary nets; [r94-photo-exhaustion.json](../ref/photos/juku-pcb-2/r94-photo-exhaustion.json); [fdc-hardware-handoff.md](../docs/fdc-hardware-handoff.md).

### P1: C94 inspection and continuity

The separate factory-drawn C94 lies immediately right of VT2, and exact .009 sheet 1 groups it with +5 V/GND bypasses. May and July owner views show bare board at its locally projected centre. The routed replica's two through-hole pads project to bare substrate near (3252,2011)/(3250,1901) in July tile 200418174, so its footprint is provisional, not original drilling verified by photo. Inspect for a removed or relocated part, identify its actual two landings, and meter each to independently known +5 V and ground before choosing a footprint or value. The formerly assigned yellow Б/8901 body and VIDEO_OUT join belong to three-lead VT2.

Purpose: closes a target-revision capacitor without reusing the adjacent transistor's marking or emitter landing.

Evidence: [c94-endpoint-registration.json](../ref/photos/juku-pcb-2/c94-endpoint-registration.json); [analog-cluster-photo-placement.md](../docs/analog-cluster-photo-placement.md); [video-analog-boundary.md](../docs/video-analog-boundary.md); `kicad/juku.board.json` C94 boundary nets.

### P1: C83 physical landing and population

The exact .009 assembly labels C83 between D41/D40, and sheet 1 groups it with +5 V/GND bypasses. The promoted D41-local two-face fit maps front candidates (2283,1923)/(2283,2153) in 200418174 near solder crowns (1920,1585)/(1920,1813) in 200522685. A wider seven-contact D41/D38 fit still supports the upper candidate but misses the lower crown by about 12 px, so the lower same-hole match needs direct continuity. The upper solder crown joins the D41.7/GND run; the lower joins a wide run visibly connected to registered D39.14/P5V. The former x1374 projection came from an obsolete wrong-package D41 seed and is rejected. D41/D40-calibrated front holes map to (246.172,135.701)/(246.172,146.041) mm in the real gap; the folded-drawing x=239.15 mm projection lies inside D41 and is not a pad location. With power off, confirm each front-to-back same-hole match, then verify the lower joint to D39.14 and independently known +5 V/GND points. May and July component views both show no body across the gap; check for a hidden or removed part at the candidate holes, and seek a value only if a fitted part is found.

Purpose: confirms the two strong C83 photo matches, the lower rail, and target-board population.

Evidence: [c83-d41-d40-gap-pair-review.json](../ref/photos/juku-pcb-2/c83-d41-d40-gap-pair-review.json); [omitted-resistor-census.md](../docs/omitted-resistor-census.md); exact .009 sheet-1 bypass detail.

### P1: lower-FDC capacitor markings

view the opposite body faces or measure isolated capacitance to determine the unit/type behind C16's bare `27` and C19's bare `22`; record tolerance/voltage markings for C16/C19/C20/C22. The available May close-up shows only those digits, and the archived `.006` group parts list is not a `.009` value source. Recovered sheet 3 closes every endpoint and the +5 V timing-resistor rail; do not re-open connectivity from unread body codes.

Purpose: closes procurement attributes without guessing electrical topology.

Evidence: [fdc-lower-assembly-placement.md](../docs/fdc-lower-assembly-placement.md); [fdc-write-precomp-map.md](../ref/schematics/fdc-write-precomp-map.md).

### P1: C85 assembly position and rails

The exact .009 sheet-1 C82...C93 legend includes C85 but does not draw its individual branch. Neither the original-resolution assembly panels nor two OCR passes provide a secure C85 callout. Obtain a clearer factory placement image, native parts list, or board overlay that identifies C85 before assigning an owner-board hole. Once located, record whether it is fitted and meter each landing to known +5 V, ground, +12 V, and -12 V anchors with power off; read or isolate-measure its value if fitted. Treat the current +5 V/GND logical connection as provisional because C92 and C93 have separately drawn supply branches.

Purpose: establishes C85's individual placement and rail assignment before a footprint or procurement value is chosen.

Evidence: [c85-source-placement-boundary.json](../ref/photos/juku-pcb-2/c85-source-placement-boundary.json); [omitted-resistor-census.md](../docs/omitted-resistor-census.md); `kicad/juku.board.json` C85 provenance.

### P1: C84 physical landing and population

The exact .009 assembly puts C84 below D54, and sheet 1 groups it with +5 V/GND bypasses. May and July owner views show no body at that position. The three conspicuous same-height bare holes below D54 cannot form C84: the left hole visibly joins D54.4/D4 and the middle joins D54.10/OUT0, so both adjacent pairs contain a signal. Locate a different two-hole landing pair in the D54/X9 area before assigning a footprint or DNP status. With power off, register both faces, meter each hole to independently known +5 V and ground, and inspect for a removed or hidden part; read or isolate-measure its value only if fitted.

Purpose: avoids placing the supply bypass across timer signal holes and establishes owner population.

Evidence: [c84-region-review.json](../ref/photos/juku-pcb-2/c84-region-review.json); [omitted-resistor-census.md](../docs/omitted-resistor-census.md); exact .009 assembly C84 callout.

### P1: C34 original footprint and value

Exact .009 assembly places horizontal C34 immediately below D51 and above D78, while the current generated PCB footprint is far from D51 and provisional. July component photo 200411500 has cable and mastic over that strip; solder photo 200527310 has multiple unassigned holes below registered D51. With power removed, expose the strip, identify a distinct C34 body or bare pair, register both holes across faces, and check each to independently known +5 V and ground. Read or isolate-measure the value if populated. Do not copy the current footprint position as an original-board site.

Purpose: resolves a physically contradicted placement and unvalued source bypass before PCB fidelity is claimed.

Evidence: [c34-d51-locality-review.json](../ref/photos/juku-pcb-2/c34-d51-locality-review.json); exact .009 assembly photo 114604420; `kicad/gen_kicad_pcb.py`.

### P1: C73 trimmer range

Exact .009 sheet 2 draws C73 in series with Z1 but gives no capacitance range. The older .006 scan prints 4/20; July owner top views show no readable range, and a May side view reads only `8811` without an interpretable range. Identify its full manufacturer/part marking from the physical body or measure its isolated adjustment range before using 4–20 pF as a procurement or bring-up setting. Also confirm the photographed lower C73 terminal to Z1's lower right lug and the upper terminal to C4 upper/D40.2/D59.2/.3 as separate continuity checks; C4's other lead remains an independent open question.

Purpose: closes the exact-revision oscillator trimmer value without copying a legacy .006 range into the BOM.

Evidence: [c4-c73-shared-node-review.json](../ref/photos/juku-pcb-2/c4-c73-shared-node-review.json); [master-oscillator-boundary.md](../docs/master-oscillator-boundary.md); `kicad/juku.board.json` C73 provenance.

### P1: source-modeled passive physical checks

C4 and the R21–R28 bank are now represented in the logical model with unresolved physical terminals. The bank is covered by the preceding P0 row. C4: its upper fitted lead shares a visible front-copper strip with C73 upper, but sheet 2 draws no C4 branch in the local oscillator frame. Verify the shared terminal against Z1.2/XTAL_TRIM and D40.2/D59.2/.3/OSC, then meter C4 lower to C73 lower, ground, and +5 V and read its value before promoting the provisional terminal joins. For the other source-modeled passives with PCB placement pending, register each owner-board body or bare landing by drawing position; then measure both pads and value only for fitted parts. The two 2 kΩ bodies left of D3 are photo-identified as R10 (outer) and R9 (inner) and have source-PCB footprints only. A direct footprint copy into the routed board adds 65 DRC violations, including shorts to INTA, IR7, and P12V. Both routed variants still place D12 left of D3 at its old estimate, while the exact assembly and owner photo place D12 above D3 as on the source PCB; refresh D12 placement and its local copper together, preserving the photo-based R9/R10 positions. Confirm their upper leads to +5 V and lower leads to D3.1/D3.13 respectively on the owner board. Check R15/R16 at their separate right/below-D3 positions as requested in the control row. Give C95/C96 factory-wire corridors first attention. For C95, use the corrected D50/D51 assembly locality: the rotated native .009 callout beside the lower package reads R58, not R38. The pale upright body right of D51 reads 5K1 and its upper solder joint photo-joins D51.8/GND, matching R58 nominal value and grounded rail-E terminal. Power off: verify that join, test its lower lead to CAS, and measure the body before promoting R58 or using either hole for C95. The separate .009 assembly panel places R38 beside D59, where the owner pale horizontal 1K0 matches its nominal value; test its D59.14/+5 V-side lead and its far lead through front open hole near (1545,2532), whose plausible solder counterpart is near (2217,2640) in 200534267, to SHIFT_G/D42.8/D43.8/D35.6. Confirm that same-hole match before using it as a net target; the solder line then photo-chases west through the 200530933 overlap to an open hole near (1155,2390), another power-off SHIFT_G probe point. The source and routed R38 footprints already lie beside D59; the R58 footprints remain far from the D51-local photo estimate (106.632,155.905)/(106.818,166.537) mm and require placement/copper review. The native .009 sheet puts D35.4 at the D42.10/D37.13 junction, D37.12 on numbered rail 3 shared with D42.9/D43.9/XTAL16M, and D37.11 on a separate pixel line to D34.12. With power off, test D35.4 at its front hole near (2178,1655) against D37.13 near (2187,1253) in 200445914 and D42.10. The nearby front corridors are separate before the obscured wire area. Test D37.12↔D42.9/D43.9, and D37.11↔D34.12 using the D34.12 front via near (3418,2985), its six-control registered solder mate near (795,2642), and the visible B.Cu path to counted D37.11 pad near (2045,2620) in 200418174/200522685. Confirm electrical continuity across that photo-supported path. D37.11 is at owner contact near (2187,1139) in 200445914; check its isolation from D103.11/D57.9/CLK_123M. See d34-pin12-video-via-review.json. The two upright 2 kΩ bodies near actual D30 are outside this C95/R58 corridor. The separate red 12К body immediately left of D35 in 200445914 matches assembly R39; its lower joint is exposed near (2090,1665) but its upper lead is wire-covered. Meter both leads to D35.3/D35.5/POF and known +5 V before assigning pad polarity. For C98, use the factory diagonal over-D58 mounting and 25* mm span to inspect the leading two-angle candidate: a small filled feature above D58 left end and a protruding joint below its right end. Register both as actual holes on the solder face and meter each to +5 V/GND before assigning C98; the owner photos show no body on top. Sheet 1 prints C74–C78, C82–C93, C94–C98, and C100 beside a +5 V/GND bypass symbol, but explicitly draws C92 from GND to -12 V and C93 from GND to +12 V. Use those individual C92/C93 branches when probing and do not infer physical population from the collective text. Factory assembly puts C75 left of D29 and C76 between D29/D27; owner photo 200358952 places C75 at D29.20's shared upper landing near (490,1465) and a separate lower annulus near (490,1680) visibly routed toward modeled D24.10/GND. D29.20 is +5 V in the source model, but owner continuity is unmeasured. A D29-local reflection puts the proposed lower front hole near solder (2489,1649) in 200509593, where the native image shows a broad strip without a distinct drilled centre; do not adopt a nearby solder joint as its match. Find the actual opposite-face hole, then meter both C75 candidates to independently known +5 V/GND. C76 retains candidate annuli near (1120,1465)/(1120,1676); register and meter those separately before assigning a footprint. Factory assembly orders C78 above C77 left of D11; a D11-local re-registration in July component photo 200358952 puts C78 near (2180,1560) in the wire/open-hole corridor left of the small package and C77 near (2152,1853) in the bare field left of D11. The retired broad three-chip projection put C78 on top of the small package, contradicting the assembly left-of-D11 order. These revised locations are search regions, not pad identities; neither has a unique two-hole pair. The two holes at the ends of the conspicuous T-shaped copper feature near (2075,1670)/(2075,1775) are visibly joined by its stem, so exclude them as opposite bypass terminals. A D11-corner reflection predicts their solder counterparts near (2884,1515)/(2884,1608) in 200506061, beside exposed holes around (2898,1525)/(2896,1619). With power off, confirm those same-hole identities and the T stem continuity; test the upper broad corridor and lower narrow trace separately to known rails before assigning either net. The first bare-column hole below the T near front (2075,1825) has a candidate solder counterpart near (2896,1665) on a separate run from T-lower (2896,1619). The factory C77 outline projects to front y1772..1933, making the later bare hole near (2075,1925), with a provisional solder match near (2895,1760), a closer opposite-end search site. Register these holes across faces and meter each to +5 V/GND before considering a C77/C78 pad. The same D11-local fit projects the C78 outline to front x2139..2229/y1500..1651, in the white-cable corridor and away from the T column; inspect that corridor, including the exposed ring near (2230,1565), for a second registered hole before assigning C78. Inspect and probe the remaining candidate positions separately before mapping either refdes. For C91, the two bare R1-adjacent features near (1025,1620)/(1270,1620) in 200439607 form a strong two-feature photo match to the distinct D105-local solder sites near (2890,1122)/(2640,1120) in 200537608; all seven D105 contacts align as controls. The right front joint visibly joins R1 right, source-named +5 V, while its supposed D105.1/IO_CYCLE_H join has a visible gap; the left solder U-strip reaches source-grounded D105.7. Power off: confirm both exact same holes and meter left to D105.7/GND and right to R1 right/+5 V and D105.1 separately before footprint placement. For C86, a gap-local open-hole match (front 1963,1235 to solder 1767,973) registers the upper wired front joint near (1960,1315) to solder (1767,1055), visibly routed to D6.1/A6. Treat that leading vertical pair as excluded from the +5 V/GND bypass site by photo; with power off, confirm both same-hole matches and the D6.1 join, then seek a different two-rail pair. The separate lower front joint near (1967,1533) alone does not establish C86. For C87, inspect the two component-face candidate joints near (1420,1315)/(1420,1535) in 200411500 against D6 four-corner solder search windows near (2320,1053)/(2320,1269) in 200527310. The upper broad solder strip visibly joins D6.8/GND; the lower strip lacks a local B.Cu join to D6.16 or D8.16 and remains rail-open. An exposed lower-strip hole near (2407,1265) lies 87 px from the projected C87 lower joint and is not its matched drill. Its exposed right endpoint near (3355,1265) in 200527310 is an additional probe target. Prove the same holes and meter the lower rail before placement. For C88, corrected native D9 contact rows x2590..2977 reveal a rail-consistent pair: front upper hole (3030,1365) maps within ≈6 px to solder (2520,1082) on a strip photo-joined to D6.8/GND; lower front hole (2978,1530) visibly joins D9.16/P5V and maps within ≈4 px to solder (2574,1247). With power off, confirm both same-hole and rail joins before placing C88 or choosing a value. The corrected source D9 frame projects those holes near (119.21,111.61)/(116.82,119.37) mm; reconcile the lower site with source C35.1, calculated 1.56 mm away, before assigning a footprint. The D9-local owner photo projects both current C35 pads onto unperforated board; D67 top contacts have about (-113,+143) px offset and adjacent D66 top contacts about (-109,+143) px; direct four-corner photo fits agree on a row-level shift, so correct the DRAM-grid-to-D9 alignment as a group rather than moving C35 alone. The older .006 drawing labels C35 above D67, but the proposed first-grid pair midpoint matches D67.16/D66.1 package contacts within about 1.7 rectified px, and the D67-local solder projection of current C35 pads near (2678,1415)/(2570,1415) and alternate component view 200415237 near (1142,1792)/(1250,1792) both show no drills. Find a distinct pair before retaining that footprint as original artwork. RAIL_G is +5 V for the РУ5 E4 setting, so C35 and C88 share bypass rail roles without proving shared holes. The native solder C88 +5 V hole near (2574,1247) is about 247 px above those DRAM package contacts near y1494; cross-register and probe the actual capacitor site before changing the grid, then verify C88 rails. The candidate C88 hole spacing is about 8.12 mm rather than C35’s 5.00 mm pitch. Both routed boards still retain the old D9 placement and need a copper-aware correction. The shorter pair using front D7-side hole (3060,1420) is rejected because its proposed solder counterpart (2493,1137) traces to D5.25/IORD; verify that boundary separately. For C89, verify the middle filled joint's visible front route to D38.7/GND. A three-control local fit using the lower white-wire joint, lower open hole, and middle filled joint now projects the upper front annulus (1842,2298) within about 4 px of the solder hole (2356,1953) on D38.1/CAS; earlier package-only fits missed by 12–14 px. Directly confirm that same hole and its D38.1 join, then exclude it from the bypass pair if continuous. Separately meter D41.14 to its near via and D38.1 before any VCC/CAS model change. At the lower open annulus (1872,2694), a two-feature photo match with the adjacent lower white-wire solder joint strongly identifies solder counterpart (2327,2347), distinct from the wire joint (2383,2347). Confirm those same holes, test its trace to west open hole (1607,2342), then seek a +5 V partner; keep the upper exposed cable tip separate. For C90, front candidates near (370,1465)/(365,1680) in 200354648 project near solder x≈3270 by the D15 two-row fit. Nearby strip joints at x≈3310 visibly join D25.10/.9 GND and D15.26 +5 V but are roughly 40 px too far outboard to adopt as the front holes. Find same-hole solder counterparts first, then meter their rails. For C96, identify the hidden component beside the two candidate joints near printed 12: the right joint near solder (2170,605) has a stem into the broad strip above, while the left near (2075,600) is clear of that strip on the solder face. Probe the two separately to +5 V, ground, and D37.4; neither visibly carries an A12 wire and the broad strip has no proved rail polarity, so keep A12B open. Keep retired .006 RF positions and unproved number gaps separate.

Purpose: closes source-backed assembly omissions that chip and net coverage cannot see.

Evidence: [omitted-resistor-census.md](../docs/omitted-resistor-census.md); [board-fidelity-gap-ledger.md](../docs/board-fidelity-gap-ledger.md); [r9-r10-routed-collision-audit.md](../docs/r9-r10-routed-collision-audit.md); [factory-wire-route-fidelity.md](../docs/factory-wire-route-fidelity.md); [c96-a12-solder-review.json](../ref/photos/juku-pcb-2/c96-a12-solder-review.json); [d6-input-continuity.md](../docs/d6-input-continuity.md).

### P1: analog/video/sound/serial bring-up captures

On a surviving .009 board, capture D34.8/R62.1 (`D34_SYNC`), D34.11/R63.1 (`D34_SIG`), and the common R62.2/R63.2/R64.1/VT2.3 base node with the same timebase, ground reference, machine mode, and ROM recorded; compare timing and levels to A:3/X6.1, after confirming continuity to VIDEO_OUT. Record whether each drawn endpoint is continuous before powered capture. Separately retain audio output and X3 serial-loopback observations for first-article bring-up.

Purpose: closes the three still-indexed analog source-risk nets against original-board behavior; first-article audio and serial tests follow release.

Evidence: [video-analog-boundary.md](../docs/video-analog-boundary.md); [replica-bringup-verification-points.md](../docs/replica-bringup-verification-points.md); [beeper-readiness.md](../docs/beeper-readiness.md); [video-readout-readiness.md](../docs/video-readout-readiness.md); [serial-handoff.md](../docs/serial-handoff.md).

### P2: optional PROM provenance

Baltijets doc 007 programming files or further physical reads, if they surface; preserve any stable board variant without reopening the adopted content set.

Purpose: adds preservation provenance beyond the two-board small-PROM reads and third-source archival D15/D16 pair already adopted.

Evidence: [community-prom-media-request.md](../docs/community-prom-media-request.md); [prom-dump-procedure.md](../docs/prom-dump-procedure.md); [d2-reconstruction-constraints.md](../docs/d2-reconstruction-constraints.md).

### P2: JUKU-1 media provenance

independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM`.

Purpose: turns the public EKDOS boot image into stronger physical-media evidence.

Evidence: [community-prom-media-request.md](../docs/community-prom-media-request.md); [ekdos-media-acquisition.md](../docs/ekdos-media-acquisition.md).

### P2: cartridge BASIC truth

larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY`.

Purpose: closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary.

Evidence: [community-prom-media-request.md](../docs/community-prom-media-request.md); [cartridge-basic-boundary.md](../docs/cartridge-basic-boundary.md).

### P2: photos and passive values

target-revision placement/population disposition for C51-C53 and C70-C72 (their retired fit-to-space coordinates are no longer fabricated); identify distinct capacitor holes for the 28 optional .006 grid refs before treating their current PCB footprints as fabricated artwork; the first proposed C35 grid midpoint is confounded by D67.16/D66.1 package contacts. For factory-labeled C38/C42/C46/C50 above D91/D89/D87/D85, exclude the paired bright marks in owner component photo 200443117: each pair continues to its DRAM pin1/RAIL_H and pin16/GND top contacts, not the modeled capacitor RAIL_G/GND branch. Identify distinct capacitor holes at all four positions before measuring values or inferring owner-board removal; and collect macro photos for FDC/top-center and sound/video analog passives. At the D39/D34 gap, use the new D34/D39 two-face contact fits to bound the gap (component x about 2990-3155, solder x about 1055-1220), exclude the front open annulus near (3040,2375) that photo-routes to D39.10/XTAL16M, then confirm D34.2 to the upper R33-left gap joint near front (3098,2345)/solder (1110,2007) and D34.6 to the distinct lower joint near front (3098,2395)/solder (1110,2057). Native crops show the two joints separated on both faces, retracting the earlier photo-bridge claim. Their gap position matches the factory C5 outline and the two branches match its exact-source terminals; confirm each same-hole pair, their isolation, and whether these are C5's actual pads. The current source C5 footprint has horizontal 5.00 mm pitch, while the candidate pair is vertical and about 2.2 mm apart by D34 pin-pitch scale; correct its geometry only after confirmation. Check R33 right at solder (1005,1808) against ground/+5 V/D34.1 separately; its wide front strip disappears under the package, and both R33 solder joints are isolated from the nearby wide B.Cu rail, and inspect the C5 site for a cut, removal, or jumper before assigning either C5 pad; the factory C5 outline has no visible owner body in May and July views. For neighboring C82, the tempting front x≈3040 vertical pair includes a lower joint whose exposed copper reaches counted D39.9/LATCH_SIG, excluding that front joint as a bypass pad. The upper front hole (3040,2310) projects within about 1 px of solder (1166,1974), whose exposed broad strip joins registered D39.14/+5 V. Confirm that same-hole and rail path, then find a distinct ground partner; check the excluded lower feature against D39.9 independently. May owner photo reads apparent К62 (0.62 kΩ), corroborating source R33=620 Ω; isolate-measure R33 if its physical value must be confirmed.

Purpose: improves authenticity and reduces assembly substitutions.

Evidence: [decap-value-fidelity.md](../docs/decap-value-fidelity.md); [PLAN.md](../PLAN.md); generated BOM/sourcing docs.

### P2: factory insulated-wire lengths

Directly measure the paths and cut lengths for W7, W8, W11, W14, and W19. Photo review places the D1-side W7/W14 starts at visible surface joints, but their D35-side printed solder joints remain candidates under mastic; expose or continuity-check those terminations. Chords to the candidate joints are 213.303/201.046 mm against approximate 24/23 cm source readings; these are not qualified replacement cut lengths. W7.1/W14.1 replica pads still require relocation. W11's registered 119.177 mm chord also exceeds its approximate 11.5 cm entry. Record insulation path, routing side, slack, and any sleeve or strain relief. A8's final 19 cm source reading is retained; establish its remote landing and measure the installed lead before qualifying a replacement length.

Purpose: qualifies replacement lengths after unresolved physical landings are identified; logical package endpoints remain unchanged.

Evidence: [factory-wire-route-fidelity.md](../docs/factory-wire-route-fidelity.md); `kicad/juku.board.json` W7/W8/W11/W14/W19 provenance; [assembly-drawing-extraction.md](../docs/assembly-drawing-extraction.md).

## Board-fidelity gap handoff coverage

Every currently open chip and net row in `docs/board-fidelity-gap-ledger.md`
appears in exactly one measurement task above. This maps work; it does
not claim a measurement or release a circuit. The generator rejects a
new, missing, or multiply assigned gap instead of silently omitting it.

| Measurement task | Source-risk nets | Chip-level gaps |
| --- | --- | --- |
| D94 .092 D0 closure | `D94_D0_BOUNDARY` | - |
| D41 shift-register supply closure | - | `D41` |
| FDC support signal dispositions | `D100_CONTROL_SHEET1_BOUNDARY`, `D101_D02_R92_R99`, `D99_B2_SHEET1_BOUNDARY`, `D99_Q2N_BOUNDARY`, `FDC_HLD_TO_D100`, `FDC_IMDRG`, `FDC_MOTOR_EN` | `D100`, `D101`, `D99` |
| memory-decode stragglers | `INHIB_STATUS_BOUNDARY` | `D13` |
| D7.3 source join and owner continuity | - | `D104`, `D7` |
| D11 physical placement and copper | - | `D11` |
| factory Вид В pad mapping | `D14_I2_BOUNDARY`, `D14_O7_BOUNDARY` | - |
| timing and video-source boundaries | `D36_CAS_IN`, `D58_STB_TAG5`, `D59_O10_TAG10`, `SYNC_B`, `TIMING_TAG17`, `TIMING_TAG2`, `XTAL16M` | `D38` |
| control and peripheral continuation boundaries | `CPU_WAIT_STATUS`, `D26_PB5_E8_2_BOUNDARY`, `D26_PC0_D3_I5`, `D26_PC1_D3_I3`, `INT4_RAW`, `KBD_CONTRDAT`, `R20_RETURN_SOURCE_HOLD`, `S1_3_BOUNDARY`, `TAPE_RUN_INT` | `C1`, `D1`, `D12`, `R20`, `R4`, `S1` |
| .009 FDC/analog passive continuity | `C10_1_BOUNDARY`, `C10_2_BOUNDARY`, `C11_1_BOUNDARY`, `C11_2_BOUNDARY`, `C12_1_BOUNDARY`, `C12_2_BOUNDARY`, `C15_1_BOUNDARY`, `C15_2_BOUNDARY`, `C9_1_BOUNDARY`, `C9_2_BOUNDARY`, `R67_2_BOUNDARY`, `X6_A3_BOUNDARY` | `AX603`, `C10`, `C11`, `C12`, `C15`, `C9`, `R67` |
| unidentified 220-ohm body near D98 | - | `RUNK1` |
| source-modeled passive physical checks | - | `R35` |
| C94 inspection and continuity | `C94_1_BOUNDARY`, `C94_2_BOUNDARY` | `C94` |
| lower-FDC capacitor markings | - | - |
| C85 assembly position and rails | - | `C85` |
| ROM-select and clock passive terminals | `P5V`, `R21_D8_OUTPUT_HOLD`, `R22_D8_OUTPUT_HOLD`, `R23_D8_OUTPUT_HOLD`, `R24_D8_OUTPUT_HOLD`, `R25_D8_OUTPUT_HOLD`, `R26_D8_OUTPUT_HOLD`, `R27_D8_OUTPUT_HOLD`, `R28_D8_OUTPUT_HOLD` | `R21`, `R22`, `R23`, `R24`, `R25`, `R26`, `R27`, `R28` |
| C34 original footprint and value | - | `C34` |
| C84 physical landing and population | - | - |
| C73 trimmer range | - | `C73` |
| analog/video/sound/serial bring-up captures | `D34_SIG`, `D34_SYNC`, `VT2_BASE` | - |
| photos and passive values | - | `C35`, `C36`, `C37`, `C38`, `C39`, `C40`, `C41`, `C42`, `C43`, `C44`, `C45`, `C46`, `C47`, `C48`, `C49`, `C50`, `C54`, `C55`, `C56`, `C57`, `C58`, `C59`, `C60`, `C61`, `C62`, `C64`, `C65`, `C66`, `C67`, `C68` |
| factory insulated-wire lengths | `PHI1_D35`, `PHI2_D35` | `W11`, `W14`, `W19`, `W7`, `W8` |

## Current D94 blockers

- D94 failed evidence checks: `none`
- The [D94 constraints](d94-reconstruction-constraints.md) own the
  adopted content and closed pin-level continuity. The remaining D0
  hidden-load branch requires tracing beyond its measured R8 branch.
- For optional live steering, capture D0 and D93 `/RE`/`/WE` while
  selecting BA1:BA0=11 and changing A4/D101.Q0. Do not assign D0's
  unknown load from the observed transition alone.

## Pin-Level Closure

No unnetted pins were found among the generator's `PIN_CLOSURE_REFS` devices after excluding intentional no-connects. Source-risk net boundaries above remain open.

Bring-up net coverage and categories are maintained in
[the verification-point report](replica-bringup-verification-points.md).

## Practical sequencing

1. Use the owner-board session for the P0 D94, FDC-support,
   memory/decode, and factory-modification continuity asks; firmware content is closed.
2. Capture powered FDC timing only where the shortlist names a functional
   contradiction that continuity cannot resolve.
3. Treat programming files, further PROM/EPROM reads, JUKU-1 provenance,
   and cartridge BASIC artifacts as optional preservation follow-up.
