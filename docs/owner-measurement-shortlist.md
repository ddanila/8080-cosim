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
| D30 section-B continuity closure guarded | PASS |
| D94 constraint report generated | PASS |
| FDC hardware handoff generated | PASS |
| FDC firmware profiles proved; physical D100 attribution retired | PASS |
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
| P0 | D94 .092 shared-enable/D0 closure | Trace the upstream source beyond the owner-closed D94.15/D93.3 shared-enable conductor. With D94 removed, repeat-check D94.1 against D101.1 and nearby support pins; either identify its hidden load or confirm the R8 2 kΩ pull-up is the only branch. Optionally scope D101.7, D94.1, /RE, and /WE on port 1F to observe register-3 steering | `docs/d94-reconstruction-constraints.md`; `docs/photo-registration.md`; exact two-sided local-fit rows in `ref/photos/juku-pcb-2/endpoints.csv` | closes the only two remaining D94 physical boundaries; the optional runtime capture validates steering but does not replace continuity |
| P0 | FDC interrupt/buffer continuity and fitted ROM profile | Continuity-identify the remote destination of conditioned D96.9 Q2 and the remote source of D96.11 CLK2, plus the shared D100.9/.11 control continuation. Exact sheet 3 closes raw D93 DRQ/INTRQ through D28.11/.13, wired outputs D28.10/.12, R93/R95, and D96.10/.12. Registered two-sided photos prove neither D96 endpoint departs on B.Cu, while F.Cu is obscured; do not infer a PIC join from the non-unique drawing continuation marks. Dump D15/D16 twice and identify the guarded CMA or NOP VG93 profile; D100.6 is source-closed to D101.9 write precompensation | `ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json`; `docs/fdc-bus-polarity.md`; `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 gate | identifies the exact board/EPROM configuration and the remote destinations after the local interrupt conditioner without reopening source-closed paths |
| P0 | memory-decode stragglers | D6.15-D105.1 is now closed to D7.8 as the I/O-cycle-active-high qualifier, and D105.3 is independently closed as qualified peripheral /WR. Recheck only the surprising D13.12-D16.13 report with D16 removed. Still close C99 far plate, the upstream D7.5/D29.3 -INHIB source, and remaining D36 timing feeds; the D6.1<-D3.4<-/PC1, D6.2<-D3.6<-/PC0, D6.11/-WREQ, D6.12-D8.15, enable, and RAM-read endpoint chains are already closed | `docs/d6-runtime-path-diagnostic.md`; `docs/d6-physical-decode.md`; `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `PLAN.md` P0 connectivity gate | corroborates the now-direct corrected D6 decode path, closes its missing address qualifier, and tightens the remaining RAM/video timing nets before netlist freeze |
| P0 | factory Вид В pad mapping | D56.5->D34.9 and D56.12->D55.15/.18 are owner-closed, while the three physical callout locations remain fixed as the separate left annulus plus D56.5/D56.12; identify only the installed item-159 material and auxiliary-annulus/adjacent-rail disposition. Note 11 proves position 150 is tubing, not a cut, and position 159 remains an unexpanded solder-location callout. D15 is photo-closed as the cut A2/A1 bridge and needs no continuity probe; D14 row numbering, the local D32.4/GND-to-D14.1 link, and fifth-landing geometry are photo-registered, so continuity-test the fifth landing's conductor, three long drawn traces, and right-row dogleg/D14.7—both component and solder faces are photo-exhausted there, and position 159 does not prove replacements; at D11 the L trace and four solder locations are registered in two component views, the older pins-4-6 solder scar is excluded, and validated two-sided package fits exhaust four solder views without a unique through-hole match—continuity-test the bridge, D11 pin/net, and upper/lower remote endpoints; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity | `docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg` | proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release |
| P0 | FDC support signal dispositions | pin-level continuity or an explicit redesign/DNP decision for the 3 still-open support devices D96, D99, and D101. For D96, probe only the remote destination of Q2/pin9 and source of CLK2/pin11; preserve its source-closed section-1 toggle and local D28.10/.12-D96.10/.12 conditioner. Also preserve the source-closed D28/D95/D97/D98/D102/D106 paths and D97/D102/D101 write-precomp chain. Exact-revision sheet 3 explicitly omits D96.13, D97.13, D98.9/.10, and D102.4 in this area; D101.1/.3/.5/.6 remain the specific precomp-area boundaries. Closed timing paths need waveform validation at bring-up, not another continuity probe | `docs/fdc-hardware-handoff.md`; `ref/schematics/fdc-unused-pin-dispositions.md`; `ref/schematics/fdc-clock-mux-map.md`; `ref/schematics/fdc-recovery-counter-map.md`; `ref/schematics/fdc-read-clock-toggle-map.md`; `ref/schematics/fdc-write-precomp-map.md`; `PLAN.md` P0 connectivity gate | completes only the genuinely open support-circuit context without re-probing source-closed timing paths |
| P1 | .009 FDC/analog passive continuity | trace both leads of factory-positioned C9/C10/C11/C12/C15; X6 is already photo-closed through bracket cable A:3/X6.1 at VD3.2/SOUND_CLAMP and A:4/X6.2 at GND. Continuity-test the now-photo-exhausted R67.2 joint, whose two component views stop at its solder pool and whose D102-local cross-side projection proves the coincident backside trace has no via; do not restore the revision-superseded .006 VT3/VT4 RF nets | `docs/video-analog-boundary.md`; `docs/source-pcb-drc.md`; `ref/photos/juku-pcb-2/r67-photo-exhaustion.json`; `ref/photos/juku-pcb-2/x6-cable-registration.json` | turns the remaining eleven explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement |
| P1 | C94 inspection and continuity | inspect whether the separate factory-drawn C94 immediately right of VT2 is populated, read its value, and identify both endpoint destinations; the formerly assigned yellow body and VIDEO_OUT join are retracted because two July views plus a May angle identify that three-lead Б/8901 body and its joints as VT2 | `ref/photos/juku-pcb-2/c94-endpoint-registration.json`; `docs/analog-cluster-photo-placement.md`; `docs/video-analog-boundary.md`; `kicad/juku.board.json` C94 boundary nets | closes a target-revision capacitor without reusing the adjacent transistor's marking or emitter landing |
| P1 | lower-FDC capacitor markings | determine the unit/type behind C16's bare `27` and C19's bare `22`, plus tolerance/voltage markings for C16/C19/C20/C22. Recovered sheet 3 closes every endpoint and the +5 V timing-resistor rail; do not re-open connectivity from unread body codes | `docs/fdc-lower-assembly-placement.md`; `ref/schematics/fdc-write-precomp-map.md` | closes procurement attributes without guessing electrical topology |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | target-revision placement/population disposition for C51-C53 and C70-C72 (their retired fit-to-space coordinates are no longer fabricated), readable bypass-cap values by refdes/position (the complete 4x8 inherited DRAM-field artwork and population are closed), plus macro photos for FDC/top-center and sound/video analog passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `none`
- D94 A0-A4/pins 10-14 are owner-closed onto BA0, BA1, IORD, D105.3 qualified /WR, and D101.7.
  D94.15->D93.3, D94.2->D99.9/R89, D94.3->D93.4/R88, and D94.4->D93.2/R87 are owner-closed.
  D94 outputs D4-D7/pins5,6,7,9 are owner/drawing-closed NC; D93.1 alone owns the visible open stub. R8 2 kΩ is the only measured D94.1 branch; its hidden-load status and the shared-enable upstream source remain open.
  D5.27->D7.10 is raw IOWR_N; D7.8->D105.1/D6.15 and D13.4->D105.2 produce D105.3 qualified peripheral /WR. D104.7 is separate at about 84 kΩ from D94.13.
  A4/D101.Q0 only affects BA1:BA0=11: low selects D0 and releases D93 `/RE`/`/WE`; high selects the normal D93 data-register strobe. Scope that four-node transition without assigning D0's unknown load.
  The content table itself is already closed.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |

## Bring-up verification scope

- Generated bring-up verification nets: `45`
- `logic`: `23` net(s)
- `memory/decode`: `1` net(s)
- `sound/analog`: `1` net(s)
- `timing/I/O`: `1` net(s)
- `video/analog`: `19` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the validated physical tables and retained historical evidence.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
