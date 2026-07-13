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
| Physical D2/D6 tables and D8 fallback are guarded | PASS |
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
| Video/RF analog boundary guarded | PASS |
| S4 interrupt boundary guarded | PASS |
| FDC functional-pin design hold is visible | PASS |
| Bring-up verification points generated | PASS |
| Source coverage audit current | PASS |
| Cartridge BASIC boundary documented | PASS |
| .009 assembly drawing extraction guarded | PASS |
| Factory Вид В modifications guarded | PASS |
| Source-PCB placement hold is current | PASS |

## Highest-value physical asks

| Priority | Ask | Exact deliverable | Evidence source | Why it matters |
| --- | --- | --- | --- | --- |
| P0 | programming disk / PROM truth | Baltijets doc 007 programming files; physical dumps of D8 RE3, D94 RE3, and D15/D16 EPROMs; an independent D2/D6 RT4 read only as corroboration of the validated captures | `docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md` | replaces the remaining D8 fallback, supplies the absent D94 truth, and cross-checks the already validated physical D2/D6 tables |
| P2 | JUKU-1 media provenance | independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM` | `docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md` | turns the public EKDOS boot image into stronger physical-media evidence |
| P2 | cartridge BASIC truth | larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY` | `docs/community-prom-media-request.md`; `docs/cartridge-basic-boundary.md` | closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary |
| P0 | D94 .092 continuity | test D94.15 specifically against D9.7/CS_FDC (and D9.9/CS_D57 as a negative control), trace D94 pins 4-7/9 destinations, and find every branch from D93.2/D93.4 beyond the visible D94.3/D94.1 segments on a .009 processor board | `docs/d94-reconstruction-constraints.md` | tests the forced PIT2/FDC row-alias enable candidate and resolves the PROM-only read/write-strobe impossibility before any defensible D94 replacement |
| P1 | FDC interrupt/buffer continuity | WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible | `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0/P1 gates | reduces first EKDOS-on-hardware debug risk |
| P0 | ВГ93 +12 V continuity | with power removed and D93 removed, test D93.40 first against the nearest proved P12V contacts D14.8 and D32.8, then confirm against A60.1 or X8.3; record positive and negative readings | `docs/d93-pin40-photo-chase.md`; `docs/fdc-hardware-handoff.md` | closes the controller's power-safety gate without inferring hidden clip-obscured copper |
| P0 | memory-decode stragglers | D6 V1/V2 feed, C99 far plate, D7/D25_T source inputs, and the remaining D36 timing feeds; D39/D41 package inputs and D53 output disposition are now source-closed | `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 connectivity gate | tightens the as-built netlist around RAM/video timing before netlist freeze |
| P1 | R94 220-ohm far endpoint | R94.1 is now photo-proved and modeled at D98.3; identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net | `ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` | closes the remaining endpoint of the now-modeled .009 R94 part without reopening the closed S1 harness |
| P0 | factory Вид В pad mapping | for D56, D15, D14, and D11 identify every position-150/159 cut pad/via, removed copper segment, and replacement connection; at D15 identify the auxiliary vertical segment cut between its second/third shown vias (roughly pad levels 8/9); at D14 identify the position-159 auxiliary hole, three long replacement traces, and right-row dogleg; at D11 use the validated solder fit that localizes rework beside pins 4-6 to map the four-hole auxiliary field and obscured bridge; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity | `docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg` | proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release |
| P0 | FDC support signal dispositions | pin-level continuity or an explicit redesign/DNP decision for D28, D95-D99, D101, D102, and D106; prioritize the FDC cluster | `docs/unmodeled-footprint-inventory.md`; `PLAN.md` P0 connectivity gate; `.009` assembly evidence | closes the functional signals on the 9 now-pin-modeled, power-routed FDC support devices |
| P0 | source-PCB collision placement | register exact target-board lead centres for C13, R68, R69, R73, and R74: C13.2 currently overlaps D95.2; R73.1 overlaps D97.9; R68.2/R69.2 overlap D102.4/.5; and R74.1 overlaps D102.12/.13. Use component- and solder-side photographs or direct hole-centre measurements; keep the already photo/factory-fitted D95/D97/D102 centres fixed. Do not use the factory-drawing capacitor beside D41: its label is C63, not C13 | `docs/source-pcb-drc.md`; `docs/analog-cluster-photo-placement.md`; `docs/fdc-lower-assembly-placement.md` | removes all six known source-board electrical shorts without inventing target-revision passive placement |
| P0 | D30/H continuity closure | trace D30.11 to its unique clock source, D30.8 to its unique destination, and identify the exact edge contact plus pull-up reference/value feeding H/D105.10/D13.13; independently spot-check the adopted D2.12->D30.2 and D105 paths if another board is available | `docs/d30-section-b-scan-chase.md`; `docs/d2-physical-dump-and-continuity.md`; `docs/rt4-dump-acquisition.md` | closes the remaining WAIT/READY edge conductors without reopening the adopted physical D2 table and measured D0 path |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `Enable pin D94.15 is traced, .092 firmware artifact exists, Repository-wide .092 artifact filename exists`
- D94 address pins are already traced to `BA11..BA15`; the useful physical
  work starts with D94.15-to-D9.7 continuity (D9.9 negative control),
  output-branch continuity, and a real `.092` dump/table.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |

## Bring-up verification scope

- Generated bring-up verification nets: `210`
- `FDC`: `24` net(s)
- `logic`: `153` net(s)
- `memory/decode`: `11` net(s)
- `sound/analog`: `2` net(s)
- `timing/I/O`: `6` net(s)
- `video/analog`: `14` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the reconstructed fallbacks.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
