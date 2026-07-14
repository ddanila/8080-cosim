# Owner measurement shortlist

Status: **READY**

This generated report compresses the remaining physical-owner asks into
the shortest useful list. It is not a bench log and does not claim any
measurement has been performed; it records what still cannot be derived
automatically from the current repo evidence.

## Command

```sh
python3 scripts/report_owner_measurement_shortlist.py
```

## Evidence freshness

| Check | Status |
| --- | --- |
| Community request packet ready | PASS |
| PROM dump procedure exists | PASS |
| Physical D2/D6/D8/D94 tables are guarded | PASS |
| D2 constraint report generated | PASS |
| D30 section-B scan chase guarded | PASS |
| D94 constraint report generated | PASS |
| FDC hardware handoff generated | PASS |
| Beeper source/handoff guarded | PASS |
| Serial USART behavior guarded | PASS |
| Decap value boundary guarded | PASS |
| D41 timing connectivity source-closed | PASS |
| Memory timing boundary guarded | PASS |
| I/O decode boundary guarded | PASS |
| .009 video / .006 RF disposition guarded | PASS |
| S4 interrupt boundary guarded | PASS |
| FDC functional-pin design hold is visible | PASS |
| Bring-up verification points generated | PASS |
| Source coverage audit current | PASS |
| Cartridge BASIC boundary documented | PASS |
| .009 assembly drawing extraction guarded | PASS |
| Factory Вид В modifications guarded | PASS |
| Source-PCB placement collision gate passes | PASS |

## Highest-value physical asks

| Priority | Ask | Exact deliverable | Evidence source | Why it matters |
| --- | --- | --- | --- | --- |
| P0 | programming disk / PROM truth | Baltijets doc 007 programming files; physical dumps of D15/D16 EPROMs; independent future D2/D6/D8/D94 reads only as corroboration of the validated captures | `docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md` | cross-checks all four validated physical PROM tables and supplies missing Tier-3 EPROM truth |
| P2 | JUKU-1 media provenance | independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM` | `docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md` | turns the public EKDOS boot image into stronger physical-media evidence |
| P2 | cartridge BASIC truth | larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY` | `docs/community-prom-media-request.md`; `docs/cartridge-basic-boundary.md` | closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary |
| P0 | D94 .092 continuity | resistance-map D94 inputs 10-14 and enable 15 to identified package pins/rails, trace active output D3/pin4 first, then D4-D7 for copper fidelity, and find every branch from D93.2/D93.4 beyond the visible D94.3/D94.1 segments on a .009 processor board | `docs/d94-reconstruction-constraints.md`; `docs/photo-registration.md`; exact two-sided local-fit rows in `ref/photos/juku-pcb-2/endpoints.csv` | replaces the retired same-as-D8 BA mapping with measured row semantics and resolves the PROM read/write control path before an FDC hardware release |
| P1 | FDC interrupt/buffer continuity | WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible | `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0/P1 gates | reduces first EKDOS-on-hardware debug risk |
| P0 | ВГ93 +12 V continuity | with power removed and D93 removed, test D93.40 first against the nearest proved P12V contacts D14.8 and D32.8, then confirm against A60.1 or X8.3; record positive and negative readings | `docs/d93-pin40-photo-chase.md`; `docs/fdc-hardware-handoff.md` | closes the controller's power-safety gate without inferring hidden clip-obscured copper |
| P0 | memory-decode stragglers | first find the source, pull device, or obscured branch on the measured D6.15-D105.1 input-only boundary; D6.1<-D3.4<-/PC1 and D6.2<-D3.6<-/PC0 are now closed. Chip-removed continuity closes D6.12-D8.15, proves D6.11/D6.12 separate, and routes D6.11 to D2.15/-WREQ; find the actual target-board driver for the older-sheet D92.5/R12.2 RAM branch. D13.12-D6.14 continuity plus visually confirmed bottom-layer D6.13-D6.14 copper closes the enable branch; recheck only the surprising D13.12-D16.13 report with D16 removed. The complete D6.9-D13.1, D13.2-D37.4, D37.6-D58.9 endpoint chain is owner-confirmed. During the known B37A RAM read scope D6.9, D13.2, D37.6, D58.9, and D58.11. All eight raw A7..A5 rows leave pin9 high at B37A. Still close C99 far plate, the upstream D7.5/D29.3 -INHIB source, and remaining D36 timing feeds | `docs/d6-runtime-path-diagnostic.md`; `docs/d6-physical-decode.md`; `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `PLAN.md` P0 connectivity gate | resolves the now-all-mode B37A endpoint/polarity/D58-path contradiction and finds the missing address qualifier before retiring the D6 runnable oracle, then tightens the remaining RAM/video timing nets before netlist freeze |
| P1 | R94 220-ohm far endpoint | R94.1 is now photo-proved and modeled at D98.3; identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net | `ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` | closes the remaining endpoint of the now-modeled .009 R94 part without reopening the closed S1 harness |
| P0 | factory Вид В pad mapping | for D56, D15, D14, and D11 identify every position-150/159 cut pad/via, removed copper segment, and replacement connection; at D15 identify the auxiliary vertical segment cut between its second/third shown vias (roughly pad levels 8/9); at D14 identify the position-159 auxiliary hole, three long replacement traces, and right-row dogleg; at D11 use the validated solder fit that localizes rework beside pins 4-6 to map the four-hole auxiliary field and obscured bridge; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity | `docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg` | proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release |
| P0 | FDC support signal dispositions | pin-level continuity or an explicit redesign/DNP decision for D28, D95-D99, D101, D102, and D106. D106.7-D93.26 RCLK is photo-closed, selecting the IE7-only output; resistance-test D106.11-D93.27 and D106.14-D93.33 specifically for hidden layer handoffs because calibrated solder-crop review rejects both direct same-layer paths. Meter the now-photo-bounded D106 setup probes: pins 15/1/5 to a known P5V anchor, pins 10/9 to a known GND anchor, and pin 4 to its clock source; pins 9/10 are rail-obscured and the others show only local copper or handoffs, so visual overlap is not continuity. Do not assume the now-excluded WD RCLK chain D106.3-D96.3/D96.5-D93.26, but still identify D96 section 1's actual role. For write precompensation, the photo now closes the R92/R99 ladder at D95.14, D101.4, and D101.8/GND; test the remaining D95/D101 select candidates against D93.18/.17, pins 1 to ground, and pin 7 toward an inverter/write-data path. Recheck legacy-NC D28.5/.6 only if that path approaches them. D96 section 2 and D99 section 1 are already excluded from the WD roles | `docs/fdc-hardware-handoff.md`; `docs/unmodeled-footprint-inventory.md`; `PLAN.md` P0 connectivity gate; Western Digital June-1980 application note Figure 11; Kovalenko et al. МПСС 1986 No. 3 pp. 3-8; `.009` assembly/photo evidence | the recovered-clock output is now closed from target copper; the remaining probes complete its loading/reset context and test the mux family that the WD-only comparison left unexplained |
| P1 | .009 FDC/analog passive continuity | trace both leads of factory-positioned C9/C10/C11/C12/C15, the far end of R67.2, and X6.1 on the .009 owner board; do not restore the revision-superseded .006 VT3/VT4 RF nets | `docs/video-analog-boundary.md`; `docs/source-pcb-drc.md`; `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json` | turns twelve explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement |
| P0 | D30/H continuity closure | trace D30.11 to its unique clock source, D30.8 to its unique destination, and identify the exact edge contact plus pull-up reference/value feeding H/D105.10/D13.13; independently spot-check the adopted D2.12->D30.2 and D105 paths if another board is available | `docs/d30-section-b-scan-chase.md`; `docs/d2-physical-dump-and-continuity.md`; `docs/rt4-dump-acquisition.md` | closes the remaining WAIT/READY edge conductors without reopening the adopted physical D2 table and measured D0 path |
| P1 | C94 endpoint continuity | identify the two lead destinations of the now-restored 680п C94 below D102; its factory identity, populated body, and `(287.07,132.26)` mm centre are already proved | `docs/analog-cluster-photo-placement.md`; `docs/video-analog-boundary.md`; `kicad/juku.board.json` C94 boundary nets | completes the electrical disposition of a target-revision component that was previously absent from the physical model |
| P1 | C63 population disposition | determine whether the factory-drawn C63 between D41 and D40 was intentionally DNP on the .009 build or physically removed later; inspect the two package-bracketed landing area for lead remnants and test whether any candidate pads join the expected array bypass rails | `docs/fdc-lower-assembly-placement.md`; `docs/photo-registration.md`; raw component photo `PXL_20260710_200418174.jpg` | resolves the conflict between the factory assembly outline and the bare owner-board gap without inventing a through-hole footprint |
| P1 | lower-FDC C16/R92/R99 continuity | read C16, R92, and R99 values and identify both C16 lead destinations; calibrated component copper already closes every R92/R99 endpoint to D95.14, D101.4, or D101.8/GND | `docs/fdc-lower-assembly-placement.md`; `docs/analog-cluster-photo-placement.md`; `kicad/juku.board.json` C16/R92/R99 boundary nets | turns three restored target-board passives into functional FDC-area circuitry without guessing from unread body markings or nearby solder rails |
| P1 | right-edge resistor column | read C19's value and both lead destinations plus the values and lead destinations of the restored .009 R100/R102/R108/R86 column beside it; factory identities, population, orientation, and placements are already registered | `docs/fdc-lower-assembly-placement.md`; `docs/analog-cluster-photo-placement.md`; `kicad/juku.board.json` C19/R100/R102/R108/R86 boundary nets | turns five restored physical parts into functional FDC-area circuitry without guessing connectivity from C19's bent body overlap or the obsolete .006 sheet |
| P1 | C20/C22 endpoint and value continuity | confirm C20's enhanced-photo `1Н5` body reading, read C22's obscured value, and identify both remote lead destinations of the restored grey axial pair immediately right of D102; their identities, adjacent 2.54 mm columns, and 10.00 mm vertical drill spans are already component/solder-photo proved | `docs/analog-cluster-photo-placement.md`; `docs/fdc-lower-assembly-placement.md`; `kicad/juku.board.json` C20/C22 boundary nets | turns two newly restored target-board capacitors into functional circuitry without mistaking their leaning bodies for D102 pin connections |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `D94 address input sources are traced, Enable pin D94.15 is traced`
- D94 A0-A4/pins 10-14 are explicit input boundaries: resistance-map each
  before interpreting the captured rows. Then map D94.15 and D3/pin4; D4-D7
  remain PCB-fidelity asks but never assert in the captured `.092` table.
  The content table itself is already closed.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |

## Bring-up verification scope

- Generated bring-up verification nets: `236`
- `FDC`: `23` net(s)
- `logic`: `175` net(s)
- `memory/decode`: `8` net(s)
- `sound/analog`: `1` net(s)
- `timing/I/O`: `5` net(s)
- `video/analog`: `24` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the validated physical tables and retained historical evidence.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
