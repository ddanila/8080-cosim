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
| P0 | D2/D105 wait-chain revision handoff | reconcile the older-sheet D95 inverter after D105.6 with the `.009` D95 FDC-multiplexer assignment and obtain the `.037` truth table; all D2 inputs are now traced | `docs/unmodeled-footprint-inventory.md`; `ref/schematics/p3_sheet1.png`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` | closes the remaining target-revision WAIT handoff without undoing the now-modeled and routed D105 gates |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `Enable pin D94.15 is traced, .092 firmware artifact exists, Repository-wide .092 artifact filename exists`
- D94 address pins are already traced to `BA11..BA15`; the useful physical
  work is enable/output continuity plus a real `.092` dump/table.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |
| `D10` | `12:CAS0, 13:CAS1, 15:CAS2, 20:IR2, 21:IR3, 22:IR4` | continuity from an actual `.009` FDC-populated board |
| `D100` | `9:OE_N, 11:T` | continuity from an actual `.009` FDC-populated board |
| `D101` | `1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N` | continuity from an actual `.009` FDC-populated board |
| `D102` | `1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` | continuity from an actual `.009` FDC-populated board |
| `D106` | `1:D1, 2:Q1, 3:Q0, 4:DOWN, 5:UP, 6:Q2, 7:Q3, 9:D3, 10:D2, 11:LOAD_N, 12:CO, 13:BO, 14:CLR, 15:D0` | continuity from an actual `.009` FDC-populated board |
| `D11` | `14:RXRDY, 15:TXRDY, 16:SYNDET, 18:TXEMPTY` | sheet-1 continuity plus `docs/serial-handoff.md` |
| `D28` | `1:A1, 2:Y1, 3:A2, 4:Y2, 5:A3, 6:Y3, 8:Y4, 9:A4, 10:Y5, 11:A5, 12:Y6, 13:A6` | continuity from an actual `.009` FDC-populated board |
| `D3` | `3:I3, 4:O4, 5:I5, 6:O6` | sheet-1 serial/interrupt continuity or source-proved NC |
| `D35` | `1:I1, 2:O2, 3:I3, 5:I5, 6:O6, 8:O8, 9:I9` | sheet-2 timing-chain continuity |
| `D41` | `1:DS, 2:A, 3:B, 4:C, 5:D, 6:LD, 8:G, 9:CK, 10:QD, 11:QC` | sheet-2 timing-chain continuity |
| `D53` | `7:Y_N7, 9:Y_N6, 10:Y_N5, 11:Y_N4` | sheet-2 memory-timing continuity or source-proved NC |
| `D59` | `1:XIN, 5:I5, 6:O6, 8:O8, 9:I9, 10:O10` | sheet-2 timing-chain continuity |
| `D93` | `1:NC_BACK_BIAS, 15:STEP, 16:DIRC, 17:EARLY, 18:LATE, 19:MR_N, 22:TEST, 23:HLT, 24:CLK, 25:RG, 26:RCLK, 27:RAW_READ, 28:HLD, 29:TG43, 30:WG, 31:WDATA, 32:READY, 33:WF_VFOE, 34:TR00, 35:INDEX, 36:WPRT, 40:VDD_12V` | continuity from an actual `.009` FDC-populated board |
| `D95` | `1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N` | continuity from an actual `.009` FDC-populated board |
| `D96` | `1:CLR1_N, 2:D1, 3:CLK1, 4:PRE1_N, 5:Q1, 6:Q1_N, 8:Q2_N, 9:Q2, 10:PRE2_N, 11:CLK2, 12:D2, 13:CLR2_N` | continuity from an actual `.009` FDC-populated board |
| `D97` | `1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` | continuity from an actual `.009` FDC-populated board |
| `D98` | `1:OE14_N, 2:A1, 4:A2, 5:Y2, 6:A3, 9:Y4, 10:A4, 11:Y5, 12:A5, 13:Y6, 14:A6, 15:OE56_N` | continuity from an actual `.009` FDC-populated board |
| `D99` | `1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1` | continuity from an actual `.009` FDC-populated board |
| `S4` | `1:P1, 2:P2` | `docs/s4-interrupt-boundary.md` plus sheet-1/SB switch continuity |

## Bring-up verification scope

- Generated bring-up verification nets: `49`
- `FDC`: `4` net(s)
- `logic`: `21` net(s)
- `memory/decode`: `6` net(s)
- `sound/analog`: `2` net(s)
- `timing/I/O`: `5` net(s)
- `video/analog`: `11` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the reconstructed fallbacks.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
