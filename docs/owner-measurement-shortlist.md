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
| P0 | D94 .092 continuity | first test D94.13/D104.7 continuity to D5.27 IOWR; if open, simultaneously scope D94.13 and active-low IOWR during known FDC reads/writes. The physical table requires equal levels on those cycles (firmware-derived functional prediction, not copper proof). Also identify the pull-up resistors on D94.13-D104.7, D94.14-D101.7, and D94.1; trace D104.10 and D5-D7 far destinations (D4/pin5 is photo-closed to the internally NC/back-bias D93.1 socket contact). The minimized table proves D101.Q0/A4 is exactly a register-3 transfer-steering qualifier: at BA1:BA0=11, A4 low asserts D94.1 independently of A3/A2 and releases D93 /RE and /WE, while A4 high restores the normal D93 strobe. Scope D101.7, D94.1, /RE, and /WE together on port 1F data transfers; do not infer D0's load. Later recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 because direct continuity places D94.12/D27.5/D29.4 on IORD contrary to the older IOM_STATUS scan interpretation | `docs/d94-reconstruction-constraints.md`; `docs/photo-registration.md`; exact two-sided local-fit rows in `ref/photos/juku-pcb-2/endpoints.csv` | uses the recovered PROM equations to target D0's hidden branch, replaces the retired same-as-D8 BA mapping with measured row semantics, and resolves the read/write control path before an FDC hardware release |
| P0 | FDC interrupt/buffer continuity and fitted ROM profile | WD1793 DRQ/INTRQ to 8259 inputs and D93 MR/CLK. Dump D15/D16 twice and identify the guarded CMA or NOP VG93 profile; factory sheet 1 proves D93 pins 7..14 connect directly to DB0..DB7. Trace only the shared D100 pins 9/11 continuation `1`; recovered sheet 3 already closes D100.6 to D101.9 write precompensation | `docs/fdc-bus-polarity.md`; `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 gate | identifies the exact board/EPROM configuration and closes the remaining drive-output-buffer inputs without reopening source-closed paths |
| P0 | memory-decode stragglers | find the source or obscured branch on the measured D6.15-D105.1 input-only boundary; D6-removed resistance to both +5V and GND fluctuates around 100-200 kohm, excluding a simple low-value pull. D6.1<-D3.4<-/PC1 and D6.2<-D3.6<-/PC0 are closed. Chip-removed continuity closes D6.12-D8.15 and proves D6.11/D6.12 separate; follow-up continuity closes the combined D2.15/-WREQ-D6.11-D92.5-R12.2 conductor. D13.12-D6.14 continuity plus visually confirmed bottom-layer D6.13-D6.14 copper closes the enable branch; recheck only the surprising D13.12-D16.13 report with D16 removed. The D6.9-D13.1, D13.2-D37.4, D37.6-D58.9 endpoint chain is owner-confirmed, and native sheet 2 separately closes MEMR-D33.3/D33.4-D37.5 as the other D37 NAND input. During the known B37A RAM read scope D6.9, D13.2, D37.6, D58.9, and D58.11. All eight raw A7..A5 rows leave pin9 high at B37A. Still close C99 far plate, the upstream D7.5/D29.3 -INHIB source, and remaining D36 timing feeds. Separately chase D105.3 bundle code 7 and D7.8 code 8; the full-resolution sheet proves those adjacent driven-output risers are distinct and does not junction D29.2 onto either | `docs/d6-runtime-path-diagnostic.md`; `docs/d6-physical-decode.md`; `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `PLAN.md` P0 connectivity gate | corroborates the now-direct corrected D6 decode path, closes its missing address qualifier, and tightens the remaining RAM/video timing nets before netlist freeze |
| P1 | R94 220-ohm far endpoint | R94.1 is photo-proved and modeled at D98.3; continuity-identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net. Two overlapping component views are cable-obscured at the landing and two registered solder regions are non-unique, so imagery is exhausted | `ref/photos/juku-pcb-2/r94-photo-exhaustion.json`; `ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` | closes the remaining endpoint of the now-modeled .009 R94 part without reopening the closed S1 harness |
| P0 | factory Вид В pad mapping | at D56 the three physical callout locations are fixed as the separate left annulus plus D56.5/D56.12 and bare-board gaps to the adjacent rail are visible; continuity-map the installed item-159 conductor/material among those three locations and the rail. Note 11 proves position 150 is tubing, not a cut, and position 159 remains an unexpanded solder-location callout. D15 is photo-closed as the cut A2/A1 bridge and needs no continuity probe; D14 row numbering, the local D32.4/GND-to-D14.1 link, and fifth-landing geometry are photo-registered, so continuity-test the fifth landing's conductor, three long drawn traces, and right-row dogleg/D14.7—both component and solder faces are photo-exhausted there, and position 159 does not prove replacements; at D11 the L trace and four solder locations are registered in two component views, the older pins-4-6 solder scar is excluded, and validated two-sided package fits exhaust four solder views without a unique through-hole match—continuity-test the bridge, D11 pin/net, and upper/lower remote endpoints; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity | `docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg` | proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release |
| P0 | FDC support signal dispositions | pin-level continuity or an explicit redesign/DNP decision for the still-open D28, D95-D99, D101, D102, and D106 pins. Preserve the source-closed D106.7-D28.9-D28.8-D96.3-D96.5-D93.26 chain and recovered sheet-3 D97/D102/D101 write-precomp chain. Resistance-test D106.11-D93.27 and D106.14-D93.33 for hidden handoffs, then meter D106's bounded setup pins. D101.1/.3/.5/.6, D97.13, and D102.4 remain the specific precomp-area boundaries | `docs/fdc-hardware-handoff.md`; `ref/schematics/fdc-write-precomp-map.md`; `PLAN.md` P0 connectivity gate | completes only the genuinely open support-circuit context without re-probing source-closed timing paths |
| P1 | .009 FDC/analog passive continuity | trace both leads of factory-positioned C9/C10/C11/C12/C15; X6 is already photo-closed through bracket cable A:3/X6.1 at VD3.2/SOUND_CLAMP and A:4/X6.2 at GND. Continuity-test the now-photo-exhausted R67.2 joint, whose two component views stop at its solder pool and whose D102-local cross-side projection proves the coincident backside trace has no via; do not restore the revision-superseded .006 VT3/VT4 RF nets | `docs/video-analog-boundary.md`; `docs/source-pcb-drc.md`; `ref/photos/juku-pcb-2/r67-photo-exhaustion.json`; `ref/photos/juku-pcb-2/x6-cable-registration.json` | turns the remaining eleven explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement |
| P1 | C94 inspection and continuity | inspect whether the separate factory-drawn C94 immediately right of VT2 is populated, read its value, and identify both endpoint destinations; the formerly assigned yellow body and VIDEO_OUT join are retracted because two July views plus a May angle identify that three-lead Б/8901 body and its joints as VT2 | `ref/photos/juku-pcb-2/c94-endpoint-registration.json`; `docs/analog-cluster-photo-placement.md`; `docs/video-analog-boundary.md`; `kicad/juku.board.json` C94 boundary nets | closes a target-revision capacitor without reusing the adjacent transistor's marking or emitter landing |
| P1 | lower-FDC capacitor markings | determine the unit/type behind C16's bare `27` and C19's bare `22`, plus tolerance/voltage markings for C16/C19/C20/C22. Recovered sheet 3 closes every endpoint and the +5 V timing-resistor rail; do not re-open connectivity from unread body codes | `docs/fdc-lower-assembly-placement.md`; `ref/schematics/fdc-write-precomp-map.md` | closes procurement attributes without guessing electrical topology |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | target-revision placement/population disposition for C51-C53 and C70-C72 (their retired fit-to-space coordinates are no longer fabricated), readable bypass-cap values by refdes/position (the complete 4x8 inherited DRAM-field artwork and population are closed), plus macro photos for FDC/top-center and sound/video analog passives | `docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `none`
- D94 A0-A4/pins 10-14 are owner-closed onto BA0, BA1, IORD, D104.7+pull-up, and D101.7+pull-up.
  D94.15->D93.3, D94.2->D99.8/GND, D94.3->D93.4, and D94.4->D93.2 are owner-closed.
  Exposed-socket front copper closes D94 D4/pin5 to D93.1. Pull-up references and D104.10 remain unknown. D94.1 has a separate unidentified +5 V pull-up with no other observed branch; D5-D7 remain PCB-fidelity asks.
  Because A2 is measured to active-low IORD, the minimized `/RE`/`/WE` equations require A3 to equal active-low IOWR during selected FDC cycles. Probe D94.13/D104.7 against D5.27; this functional prediction does not authorize a source-net merge.
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

- Generated bring-up verification nets: `106`
- `FDC`: `8` net(s)
- `logic`: `75` net(s)
- `memory/decode`: `3` net(s)
- `sound/analog`: `1` net(s)
- `timing/I/O`: `1` net(s)
- `video/analog`: `18` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the validated physical tables and retained historical evidence.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
