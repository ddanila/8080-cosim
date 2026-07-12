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
| D6/D8 reconstructed fallback exported | PASS |
| D2 constraint report generated | PASS |
| D94 constraint report generated | PASS |
| FDC hardware handoff generated | PASS |
| Beeper source/handoff guarded | PASS |
| Serial USART behavior guarded | PASS |
| Decap value boundary guarded | PASS |
| D41 timing boundary guarded | PASS |
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
| P0 | programming disk / PROM truth | Baltijets doc 007 disk files, or dumps of D2/D6 RT4, D8 RE3, D94 RE3, D15/D16 EPROMs | `docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md` | unblocks preservation-grade PROM truth and validates/replaces reconstructed D6/D8 fallbacks |
| P2 | JUKU-1 media provenance | independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM` | `docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md` | turns the public EKDOS boot image into stronger physical-media evidence |
| P2 | cartridge BASIC truth | larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY` | `docs/community-prom-media-request.md`; `docs/cartridge-basic-boundary.md` | closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary |
| P0 | D94 .092 continuity | D94 pin 15 enable, pins 4-7/9 destinations, and every branch from D93.2/D93.4 beyond the visible D94.3/D94.1 segments on a .009 processor board | `docs/d94-reconstruction-constraints.md` | required to resolve the PROM-only read/write-strobe impossibility before any defensible D94 replacement |
| P1 | FDC interrupt/buffer continuity | WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible | `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0/P1 gates | reduces first EKDOS-on-hardware debug risk |
| P0 | memory-decode stragglers | D6 V1/V2 feed, C99 far plate, D7/D25_T source inputs, D36/D39/D53 RAM-strobe ambiguous feeds, and D41 timing-bus input/control pins | `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 connectivity gate | tightens the as-built netlist around RAM/video timing before netlist freeze |
| P1 | R94 220-ohm far endpoint | R94.1 is now photo-proved and modeled at D98.3; identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net | `ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` | closes the remaining endpoint of the now-modeled .009 R94 part without reopening the closed S1 harness |
| P0 | factory Вид В pad mapping | for D56, D15, D14, and D11 identify every position-150/159 cut pad/via, removed copper segment, and replacement connection; at D15 identify the auxiliary vertical segment cut between its second/third shown vias (roughly pad levels 8/9); at D14 identify the position-159 auxiliary hole, three long replacement traces, and right-row dogleg; at D11 use the validated solder fit that localizes rework beside pins 4-6 to map the four-hole auxiliary field and obscured bridge; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity | `docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg` | proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release |
| P0 | FDC support signal dispositions | pin-level continuity or an explicit redesign/DNP decision for D28, D95-D99, D101, D102, and D106; prioritize the FDC cluster | `docs/unmodeled-footprint-inventory.md`; `PLAN.md` P0 connectivity gate; `.009` assembly evidence | closes the functional signals on the 9 now-pin-modeled, power-routed FDC support devices |
| P0 | source-PCB collision placement | register exact target-board lead centres for C13, R68, R69, R73, and R74: C13.2 currently overlaps D95.2; R73.1 overlaps D97.9; R68.2/R69.2 overlap D102.4/.5; and R74.1 overlaps D102.12/.13. Use component- and solder-side photographs or direct hole-centre measurements; keep the already photo/factory-fitted D95/D97/D102 centres fixed | `docs/source-pcb-drc.md`; `docs/analog-cluster-photo-placement.md`; `docs/fdc-lower-assembly-placement.md` | removes all six known source-board electrical shorts without inventing target-revision passive placement |
| P0 | D2/D30/D105 continuity adoption | owner continuity proves D2.12->D30.2, D1.17/H gating through D105 to D5.4, and a joined D13.12/D6.11/D6.12 net; preserve one power-cycled raw `.037` capture and independently spot-check the corrected endpoints | `docs/d2-physical-dump-and-continuity.md`; `docs/rt4-dump-acquisition.md` | replaces the stale older-sheet D2->D105 interpretation and enables a physical READY-path simulation |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `Enable pin D94.15 is traced, Every unresolved D94 output has a photographed copper departure, .092 firmware artifact exists, Repository-wide .092 artifact filename exists`
- D94 address pins are already traced to `BA11..BA15`; the useful physical
  work is enable/output continuity plus a real `.092` dump/table.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |
| `D10` | `12:CAS0, 13:CAS1, 15:CAS2` | continuity from an actual `.009` FDC-populated board |
| `D11` | `18:TXEMPTY` | sheet-1 continuity plus `docs/serial-handoff.md` |
| `D3` | `3:I3, 4:O4, 5:I5, 6:O6` | sheet-1 serial/interrupt continuity or source-proved NC |
| `D35` | `1:I1, 2:O2, 5:I5, 6:O6, 8:O8, 9:I9` | sheet-2 timing-chain continuity |
| `D41` | `10:QD, 11:QC` | sheet-2 timing-chain continuity |
| `D53` | `7:Y_N7, 9:Y_N6, 10:Y_N5, 11:Y_N4` | sheet-2 memory-timing continuity or source-proved NC |
| `D59` | `5:I5, 6:O6` | sheet-2 timing-chain continuity |
| `D93` | `1:NC_BACK_BIAS` | continuity from an actual `.009` FDC-populated board |

## Bring-up verification scope

- Generated bring-up verification nets: `219`
- `FDC`: `24` net(s)
- `logic`: `165` net(s)
- `memory/decode`: `9` net(s)
- `sound/analog`: `1` net(s)
- `timing/I/O`: `8` net(s)
- `video/analog`: `12` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the reconstructed fallbacks.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
