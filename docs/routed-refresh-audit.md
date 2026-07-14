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
python3 kicad/close_unconnected_gaps.py OUTPUT_M.kicad_pcb OUTPUT_WIDE.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --timeout 30
python3 kicad/close_unconnected_gaps.py OUTPUT_WIDE.kicad_pcb OUTPUT_FINE.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --grid-step 0.25 --timeout 60
python3 kicad/close_unconnected_gaps.py OUTPUT_FINE.kicad_pcb OUTPUT_SHAPED.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --grid-step 0.10 \
  --route-clearance 0.45 --timeout 180
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
`M5V_DERIVED`, and `X4_STOP_N`, before exhausting the band. The 75-100 mm band
accepted 10 more routes, including `HLDA`, `IORC_N`, `MEMW`,
and `D6_MEM_SELECT_N`; a second pass accepted none. The guarded candidate then
accepted eight routes in the 100-125 mm band, including `IORD`, `IOWR`,
`MEMW`, `ROE`, and `SYNC`, while rejecting its first `VIDEO_OUT` proposal.
The remaining 125-225 mm distance bands accepted 14 routes and reached 76
unconnected items; no DRC gap is longer than 232 mm.

The multilayer search corridor is now an explicit `--search-margin` parameter
instead of a fixed 30 mm. Exhaustive 60, 90, and 120 mm corridor sweeps accepted
8, 3, and 1 additional routes respectively, including `VIDEO_OUT`, `SER_DTR`,
`MEMW`, BA4/BA5, and another `P5V` island. The 120 mm sweep therefore establishes
the current corridor-expansion limit at 64 unconnected items on 50 nets and
10,326 copper items, a cumulative reduction of 125 from the Freerouting import.

The A* lattice is likewise explicit through `--grid-step`. A 0.25 mm sweep
accepted 21 routes that the default 0.5 mm grid could not represent, including
dense address/data-bus links plus `XTAL16M`, `PHI1`, `PHI2TTL`, `PIT_BAUD`,
`D26_PC5_RN_IN`, and `D39_O8`; a second complete pass accepted none. The
current temporary board has 43 unconnected items on 35 nets and 11,888 copper
items, a cumulative reduction of 146 from the Freerouting import. A subsequent
0.20 mm sweep accepted four routes and closed five more gaps, primarily in the
remaining `MA6`/`CAS` cluster. Its second-order result is 38 unconnected items
on 35 nets and 12,113 copper items, a cumulative reduction of 151. A 0.125 mm
sweep then accepted two more routes for `CAS` and `DB5`; the current temporary
board has 36 unconnected items on 34 nets and 12,161 copper items, a cumulative
reduction of 153. A final 0.10 mm sweep accepted one `DB1` route and reached 35
unconnected items on 33 nets with 12,306 copper items; further global lattice
reduction is no longer productive. Rejected proposals now report their exact
unconnected and DRC-count deltas to guide route-specific remediation.

Route-specific diagnosis then exposed a keep-out approximation error: the
router represented every pad by a circle based on its largest dimension. A
proposed diagonal P5V segment therefore cleared the circular approximation but
clipped the corner of square pad E2.1, producing 0.1546 mm actual clearance
against a 0.2 mm rule. Pad obstacles now use KiCad's shape- and
rotation-aware hit test on the applicable copper layer. Proposal clearance is
also exposed as `--route-clearance` so a wider keep-out can be tested without
changing the acceptance invariant. With the corrected pad geometry, the same
0.10 mm sweep legally closed P5V and BA13 and reached 33 unconnected items on
31 nets with 12,705 copper items, a cumulative reduction of 156 from the
Freerouting import. A complete second-order sweep accepted no other routes.

The next rejected MEMR proposal identified an independent layer-change bug:
its new via landed only 0.0198 mm from the drilled hole in same-net pad D92.13,
while the board rule requires 0.2495 mm. Same-net copper overlap is legal, but
hole spacing is net-independent. The multilayer router now keeps new vias away
from every drilled pad using the existing hole radius, the 0.3 mm proposal-via
drill, and a 0.25 mm edge-to-edge allowance. The corrected proposal closed
MEMR and reached 32 unconnected items on 30 nets with 12,844 copper items, a
cumulative reduction of 157. A complete hole-aware residual sweep accepted no
further routes.

P12V and RESET proposals then revealed that the old 0.4 mm hard-coded outer
rectangle was not an adequate board-edge model. In particular, P12V passed
only 0.35 mm from the circular Edge.Cuts hole centered at `(10.1,135.6)`;
the configured copper-to-edge rule is 0.5 mm. The router now rasterizes every
actual Edge.Cuts primitive through KiCad's shape-aware hit test, including the
internal mounting holes, with the rule clearance plus half the proposed track
width. Alternate P12V and RESET routes pass the strict transaction guard and
reach 30 unconnected items on 29 nets with 13,117 copper items, a cumulative
reduction of 159. The remaining M12V edge-related proposal becomes correctly
unroutable rather than producing a new violation.

The initial candidate also retained one imported GND segment only 0.2257 mm
from the circular Edge.Cuts hole at `(199,251.2)`. A reproducible targeted
repair in `kicad/repair_residual_copper_findings.py` preserves both live-chain
endpoints and replaces that segment with a three-segment F.Cu dogleg on the
open side of the hole; the lower side was rejected because it conflicts with
RAM_RD_OE. The accepted dogleg removes the last copper-to-edge finding without
changing the 30-open count. One intermediate pypcbnew save stopped reporting
the 53 `pth_inside_courtyard` entries, while subsequent router saves reported
them again with unchanged geometry; that transient count change was not
treated as a routing improvement.

Two final router assumptions explained the residual false proposals. DRC gap
items identify whether each endpoint is on F.Cu, B.Cu, or a through-hole pad,
but the wrapper discarded that information and let A* choose either endpoint
layer. OSC and DB3 routes therefore reached the right coordinates on the wrong
layers without closing their gaps. The wrapper now passes explicit F/B/A
endpoint constraints. Layer changes also used track-width keep-outs for a
0.6 mm via; a separate via-copper obstacle map now checks the full 0.3 mm via
radius against both layers. With those corrections, OSC closes at a guarded
0.30 mm proposal clearance, DB3 closes, and the residual cleanup removes the
now-redundant 1.555 mm OSC tail only after another OSC route reaches its
junction. This reached 28 unconnected items with zero electrical-category DRC
findings.

A complete rule-accurate 0.30 mm sweep then accepted 21 more routes: CAS,
BA11, PST_CLK, S3_2, BA4, IOM_N, MWC_N, INHIB_N, BA10, IOWC_N, DB7, AMWC_N,
BA12, SYNC, W10_QA_SEL, RESET, INT7_RAW, M12V, MEM_MODE0, STSTB, and
MEM_MODE1. The current candidate has 7 unconnected items on 7 nets (`BA1`,
`BA11`, `DB4`, `INTR`, `PHI2`, `MA6`, and `RAM_OUT_EN`) and 16,747 copper
items, a cumulative reduction of 182 from the Freerouting import. A complete
second pass accepted nothing.

The current authoritative DRC has zero shorts, copper-clearance violations,
track crossings, hole-clearance violations, dangling tracks, or copper-to-edge
findings. All 663 remaining non-electrical violation counts equal the prior
counts after removing the former GND edge and OSC dangling findings. Exact
identity/net parity with all 2,383 source pads also remains proved. This
candidate is still temporary and cannot replace the tracked routed board.
