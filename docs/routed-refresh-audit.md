# Routed PCB refresh audit

The routed fabrication snapshot predates substantial photo-driven placement and
connectivity work. It cannot safely receive the current source PCB's pad nets by
name alone: added and moved footprints now intersect old copper corridors.

## Reproducible audit

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py
```

The script compares complete endpoint sets and exact pad coordinates per net.
It classifies copper as reusable only when both are identical between
`juku.kicad_pcb` and `juku_routed.kicad_pcb`. Candidate generation is explicit:

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --output /tmp/juku-routed-refresh.kicad_pcb
```

The temporary candidate is an audit artifact, not a fabrication deliverable.

## Current result

| Item | Count |
| --- | ---: |
| Source footprints | 296 |
| Routed-snapshot footprints | 240 |
| Source-only footprints | 76 |
| Routed-only footprints | 20 |
| Routed copper nets classified by the refresh | 325 |
| Nets with initially reusable routed copper | 167 |
| Routed nets quarantined before DRC | 158 |
| Initially reusable track/via items | 3,574 |
| Initially quarantined/duplicate items | 5,091 |
| Additional nets quarantined from candidate copper DRC | 13 |
| Reusable items after DRC quarantine | 3,269 |

The source-only set includes `A17`, `A21-A32`, `AX401-AX423`, `A45-A62`, newly
modeled FDC support/passive parts, and the photo-fitted serial and oscillator
parts. The routed-only set contains superseded `.006` option parts and the
off-board `S1`, `S4`, `X3`, `X8`, and `X9` bodies; the authoritative source
represents the applicable cable landings instead. X4 is likewise
schematic-only in the source; its modeled `AX401-AX423` landing row is absent
from the stale routed snapshot.

The July-2026 refresh audit found 48 short violations in the first candidate.
Feeding that DRC JSON back through `--exclude-drc` quarantines 16 implicated
routed nets and removes every transplanted-track short. The remaining 12 DRC
short violations were six duplicated pad-to-pad placement collisions already
present in that source snapshot: approximate analog-part positions overlapped the
factory-registered D95/D97/D102 cluster. Later evidence briefly raised the
source count to ten, then complete `.009` assembly/owner coverage proved that
the colliding bodies belonged to the `.006`-only VT3/VT4 RF option. The current
source dispositions those fifteen parts DNP and has zero electrical placement
collisions. S4 is likewise correctly schematic/off-board. The old routed
candidate still remains rejected because it predates these source changes.
This corrected audit supersedes the earlier false zero-short
statement, which inspected a nonexistent top-level JSON field instead of
`violations[type=shorting_items]`.

## Direct MEMR/wire-11 promotion

The native `.006` sheets make one later source correction independently of a
full routed refresh: sheet 1 exports `-MRD`, and both sheet-2 arrivals bearing
that same label land on D33.3 and D92.13. Factory wire 11 continues D92.13 to
D7.1. The former `W11_D7_D92` net was therefore an artificial split and is now
merged into `MEMR` in the board JSON, source PCB, routed PCB, and structural
HDL/LVS contract.

The routed board's twelve existing wire-11 segments were retained as MEMR
copper. The first attempted 2.01 mm F.Cu join was rejected because strict DRC
showed it crossing four select traces. The adopted route instead places
0.6/0.3 mm vias at `(227.0497,127.5849)` and `(230,123)` and joins them on
B.Cu. The independent `M5V_DERIVED` islands are also closed with a via at
`(35,213)`, five short B.Cu segments around D105, and a direct F.Cu landing on
R19.2. Strict KiCad DRC now reports zero copper clearance, crossing, short, or
unconnected findings. These targeted promotions do not imply that the stale
fabrication ZIP has passed the full refresh audit.

A clean refresh therefore requires this order:

1. keep the now-clear source-placement gate guarded while functional connectivity stabilizes;
2. generate the compatible-copper candidate only after netlist freeze;
3. iteratively quarantine any transplanted net implicated by DRC using `--exclude-drc`;
4. route the quarantined nets against the current placement;
5. replace `juku_routed.kicad_pcb` only after endpoint parity and zero electrical
   DRC findings are both proved.

## Current full-refresh routing experiment

A source-complete candidate was generated after feeding its first two KiCad
DRC reports back through `--exclude-drc`. The second report contributed the two
clearance-implicated nets that the older short-only filter missed. The resulting
candidate retained 3,269 compatible copper items on 154 nets, quarantined 13
DRC-implicated nets, and began with zero KiCad shorts, copper-clearance
violations, track crossings, or placement collisions. Its 296 footprints and
2,383 pad identities/net assignments exactly match the source; Specctra import
quantized 54 pad coordinates by at most 38 nm, which is not a topology change.

Freerouting 2.2.4 reduced its internal incomplete count from 1,001 to 270 in
pass 1 (41 minutes 42 seconds), then to 195 in pass 2 (43 minutes 39 seconds).
After importing the session, KiCad reported 189 unconnected items across 83
nets, zero shorts, zero copper-clearance violations, and zero track crossings.
The two remaining non-connectivity copper findings are one dangling `OSC` track
and one `GND` track 0.2257 mm from an edge where the configured minimum is
0.3 mm. The temporary candidate is therefore a substantial convergence result,
not an adoptable routed board. Further routing must close all 189 connections
and both residual copper findings before replacing the tracked snapshot.

A continuation experiment re-exported that imported board and began with 222
Freerouting incompletes across 4,602 route items. Its first pass required 1 hour
48 minutes and reduced the count only to 207. Freerouting also recovered from
two `ShapeSearchTree.merge_entries_in_front` null-entry exceptions while
normalizing the dense imported traces. The remaining three configured passes
were stopped: this route was converging at only 15 internal connections per
pass, did not establish an improvement over the existing 189-item KiCad result,
and had not produced a trustworthy replacement session. Further automated work
should partition or simplify the residual nets instead of repeating whole-board
rip-up passes on this geometry.

Marking all 6,516 imported copper items locked before DSN export did not provide
that partition: Freerouting still reported the same 222 incompletes across
4,602 route items and reproduced the normalization exception within two
minutes. That duplicate run was stopped. KiCad's Specctra export therefore does
not turn the dense imported geometry into a cheap residual-only routing problem
merely by setting the board-item lock flag.

The deterministic follow-up uses the existing two-layer A* gap router through a
strict DRC transaction wrapper. Each proposal is made on a temporary board and
is accepted only if KiCad reports fewer unconnected items, no shorts,
clearance violations, or crossings, and no increase in any other DRC violation
type. The single-layer distance bands and bounded multilayer pass are
reproducible with:

```sh
python3 kicad/close_unconnected_gaps.py INPUT.kicad_pcb OUTPUT.kicad_pcb \
  --max-distance 30 --timeout 20
python3 kicad/close_unconnected_gaps.py OUTPUT.kicad_pcb OUTPUT_50.kicad_pcb \
  --min-distance 30 --max-distance 50 --timeout 20
python3 kicad/close_unconnected_gaps.py OUTPUT_50.kicad_pcb OUTPUT_M.kicad_pcb \
  --max-distance 15 --mode M --timeout 60 --limit 10
```

The first two single-layer bands accepted 14 proposals and reduced KiCad's
unconnected count from 189 to 175. The initial bounded multilayer pass then
accepted 10 short residual gaps, including power, ground, `MA6`, and `CAS`, and
reached 165 unconnected items.

Profiling the next pass exposed an invariant full-board scan inside every A*
state: each possible layer change re-enumerated roughly 6,800 copper items to
check its distance from existing vias. `repair_fdc_route_gaps.py` now rasterizes
those existing-via keep-outs once per proposal. A previously 60-second timeout
then produced the same raw candidate in 1.3 seconds; the transaction wrapper
correctly rejected that particular candidate for a new short and clearance
violation. With no acceptance-rule relaxation, subsequent 0-30 mm multilayer
passes accepted 28 more routes. Two bounded 30-50 mm passes accepted another 15
across ground, data, timing, density, and latch nets before exhausting that
band's remaining legal proposals. Two 50-75 mm passes accepted 14 more routes,
including `IORD`, `IOWR`, `POF`, `FDC_DDEN`, `FDC_DAL7`, `DC1`,
`M5V_DERIVED`, and `X4_STOP_N`, before exhausting the band. The current
temporary board has 108 unconnected items and 8,312 copper items, a cumulative
reduction of 81 from the Freerouting import.

The final authoritative DRC still has zero shorts, copper-clearance violations,
track crossings, or hole-clearance violations; all 665 non-connectivity
violation counts are unchanged, including the original dangling `OSC` track and
`GND` edge-clearance finding. Exact identity/net parity with all 2,383 source
pads also remains proved. This candidate is still temporary and cannot replace
the tracked routed board.
