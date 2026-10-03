# Factory insulated-wire route fidelity

Status: **FACTORY WIRE LANDING EVIDENCE HOLD**

The `.009` assembly table proves ten on-board insulated links. Their
logical endpoints are source-closed, but logical net equality is not
permission to replace the original flying wire with PCB etch. This report
separates those two claims. Source/routed parity and electrical DRC are held,
but factory-construction release remains held until all ten links are
represented as explicit assembly wires between split copper islands.

## Command and scope

Run `/usr/bin/python3 kicad/report_factory_wire_route_fidelity.py`
with KiCad Python bindings available. It reruns the landing evidence
guards and DRC on both routed variants, then compares source pad
identities, nets, and centers. A successful exit means the invoked
evidence guards passed; release additionally requires the report status
and every parity, DRC, and construction condition below to be ready.

## Guarded state

- Logical endpoint check: `PASS`
- Landing-registration check: `PASS`
- Board-fit photo/copper evidence checks: `FAIL (5/9)`
- Drawing-image landing endpoints registered: `20/20`
- Landing endpoints fitted to PCB coordinates/islands: `10/20`
- Paired A-point landing terminals modeled: `14/20`
- Photo-confirmed modeled landing relocations still required: `W7.1, W14.1`
- Promoted/source pad identities equal: `FAIL`
- Promoted/source pad-net mismatches: `3`
- Promoted/source moved pads (>50 nm): `210`
- Explicit assembly-wire island splits: `7/10`
- Same-net copper substitutions still held: `3/10`
- Promoted DRC unconnected items: `59`
- Historical pre-promotion candidate audit:
  - Candidate/source pad identities equal: `FAIL`
  - Candidate/source pad-net mismatches: `3`
  - Candidate/source moved pads (>50 nm): `210`
  - Link nets carrying historical candidate copper: `9/10`
  - Historical candidate DRC unconnected items: `59`
- Required release state: twenty registered and modeled landing terminals,
  ten split island pairs, ten explicit assembly-wire closures, exact source
  parity, and zero electrical/unconnected DRC findings.

The current parity and DRC results above remain release blockers. Seven
links (A7/A8/A10/A11/A14/A19/A20) are explicit W-footprint assembly wires
between separately named copper islands. A9/A12/A13 lack five evidence-gated
landing coordinates, so their endpoints remain same-net copper routes. A7B
and A14B are also masked candidates, and W7.1/W14.1 still need relocation. This
construction hold is additional to the electrical and placement holds.
The candidate audit is a separate snapshot and does not authorize the promoted board.

## Link audit

| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Promoted construction | Copper items on primary island |
| ---: | ---: | ---: | --- | --- | ---: | ---: | --- | ---: |
| 3 | А:7 | ~24 | `PHI1` | D1.22, D35.10 | 2 | 2 | explicit wire / split islands | 95 |
| 4 | А:8 | ~19 | `STSTB` | D38.8, D5.1 | 2 | 2 | explicit wire / split islands | 4 |
| 5 | А:9 | ~12 | `SYNC` | D1.19, D38.12 | 2 | 0 | same-net copper / landing hold | 236 |
| 6 | А:10 | 13.5 | `W10_QA_SEL` | D41.13, D50.1 | 2 | 2 | explicit wire / split islands | 1 |
| 7 | А:11 | ~11.5 | `MEMR` | D7.1, D92.13 | 2 | 2 | explicit wire / split islands | 213 |
| 8 | А:12 | ~20 | `RAM_OUT_EN` | D13.2, D37.4 | 2 | 0 | same-net copper / landing hold | 208 |
| 9 | А:13 | ~15 | `ROE` | D13.1, D92.1 | 2 | 0 | same-net copper / landing hold | 286 |
| 10 | А:14 | ~23 | `PHI2` | D1.15, D35.12 | 2 | 2 | explicit wire / split islands | 48 |
| 13 | А:19 | ~9.5 | `MEMW` | D5.26, D7.2 | 2 | 2 | explicit wire / split islands | 378 |
| 14 | А:20 | ~6 | `S_TTL` | A23.1, D3.10, X3.3 | 2 | 2 | explicit wire / split islands | 0 |

## Remaining release closure

10 PCB landing coordinates/island assignments remain evidence-gated:
`A7B`, `A8B`, `A9A`, `A9B`, `A10B`, `A12A`, `A13A`, `A13B`, `A14B`, and `A12B`. Existing registered component and
solder views either occlude the termination or leave its through-hole
pairing, copper path, or cable identity unproved. A13B now has a
strong photo-traced D92.1/ROE candidate, still awaiting continuity.
The former A14B and A7B metric projections from D41 are withdrawn
after the common lower-cluster solder correction. Their printed
joints remain visible, but wire termination is hidden by mastic; W14's landing and cut length
remain under measurement hold.
The routed board and fabrication package remain under design
hold because A8/A9/A10/A12/A13 physical landings or construction
remain unproved, and because the broader functional P0 netlist is open.
A:7, A:8, A:10, A:11, A:14, A:19, and A:20 are already split into modeled landing pairs and
explicit assembly-wire components. After owner continuity or a newly exposing
photograph closes the unresolved joints:

1. Finish the twenty landing terminals and split each remaining logical
   net into its two original copper islands joined by an explicit wire-link
   assembly object.
2. Add W9/W12/W13 assembly footprints, split their island net names, reroute
   only the affected islands, and achieve zero electrical/unconnected DRC
   findings.
3. Regenerate the fabrication package and emit a wire cut/installation table
   with the factory lengths before design release.

`А:20` remains on `S_TTL`: enlarged sheet-1 review reads the adjacent
vertical package as `Д104`, not `Д14`, consistent with owner continuity
D3.10-A23-X3.3 and inconsistent with moving the link onto `SER_TXD`.
Its two drawing endpoints are now guarded at `(2022,1408)` and
`(2503,2325)` original-image pixels (each ±6 px). The D3-side white wire
terminates at `(1232,872)` in owner image `200418174`; its short tinned
departure reaches locally fitted D3.10, proving A20B/S_TTL at
`(213.571,78.499)` mm. At the other end, three component overlaps put
the entering white wire and mastic over A23.1; independent solder views
`200506061`/`200509593` show the third-from-right A23 joint with no
solder-side copper departure. This proves the shared A20A/A23.1/X3.3
through-hole joint at `(178.780,15.200)` mm rather than merely net equality.
`А:19` is likewise guarded across two overlapping views: R7 lies between
the left `(1310,3122)` and right `(1283,3110)` image-local endpoints.
At its D5 end, the marked КР580ВК38's complete contact field and
right-facing notch identify D5.26 at `(1214,1480)` in owner image
`200411500`; a straight 113 px copper segment reaches the distinct
white-wire surface joint `(1218,1593)`. This proves A19A/MEMW at
`(35.308,122.281)` mm. The same uninterrupted insulated lead ends at
the distinct `(3255,1585)` surface joint below the marked black D7.
The terminal is `(130.027,121.736)` mm: its 94.721 mm span from A19A
matches the factory approximately 9.5 cm conductor and proves the
D7.2-side MEMW landing rather than a neighboring white-wire endpoint.
The same overlap method guards `А:11` at `(1563,3155)` in `114556899`
and `(1898,2837)` in `114600417`. Two-sided D92 fits place owner pin
D92.13 at `(2654.333,2345.833)` component and `(1552.167,2007)`
solder pixels; neither pad face carries the wire. The distinct white
surface joint printed `11` at `(2620,1764)` in `200418174` is the
factory-table D92.13 end. Independent D40/D41 transforms agree within
0.013 mm and promote A11B at `(261.325,128.548)` mm on `MEMR`; the
overlapping D7 tile separates the known A19 joint from the second
white joint at `(1825,1706)`, promoting A11A at
`(142.256,123.468)` mm. Their 119.177 mm chord exceeds the approximate
revised 11.5 cm table entry (earlier value crossed out); endpoint geometry
is adopted while cut length is held for direct measurement.
`А:10` is complete in one drawing view at `(821,3778)` and
`(3016,3702)` in `114556899`, with a right-side overlap in
`114600417`. The left mark is beside native-labeled D50/C95;
the right mark continues toward the D41 region. The former D41-end joint
`(2148,2174)` is a trace point without a visible wire termination;
its supposed solder counterpart `(1506,1834)` came from the displaced
D41 field. The old D30-tile owner candidates are withdrawn.
Factory-right A10B still has no identified owner joint.
At factory-left A10A beside D50,
component joint `(2804,2266)` and reflected solder joint `(915,2000)`
agree within 0.012 mm and a 4.370 mm spur reaches D50.1. This proves
A10A `(108.865,152.813)` mm remains fitted. The former 131.355 mm
chord is invalid; the drawing still gives the corrected 13.5 cm
conductor length and A10B needs a new physical landing fit.
Corrected D41.13 solder contact near `(2054,1790)` runs visibly to a
soldered endpoint near `(2415,2090)`. A close component crop shows
the exposed white-wire metal tip near `(1825,2435)` over the trace
field without a discernible solder pool or pad. The cross-face
projection of the solder endpoint is near `(1777,2424)`, about
50 px west beneath insulation. Do not promote this tip as A10B
without direct cable-to-D41.13 continuity.
`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`
immediately before C95 and `(1625,3443)` immediately after D38/before
R35. Two-face fits place D13.1 at `(1426,906)` component /
`(2682,825)` solder pixels and D92.1 at `(2484,2290)` /
`(1719,1951)`; none of those owner-pad faces carries the wire. In the
corrected D50/C95 component tile `200411500`, a white wire joint near
`(2400,2330)` is an A13A position candidate. It is a separate lower
cable from the upper fitted A10A/D50.1 wire. Its D50-local projection
near solder `(1334,2065)` lies on a bare trace without a distinct
through-hole joint. A closer front crop reveals a short copper spur
from the joint to open annulus `(2430,2377)`; its reflected solder
prediction is `(1303,2111)` from D50 or `(1306,2136)` from nearby
D51. The latter misses the plausible open hole `(1294,2149)` by
about 18 px, versus 39 px from D50. The through counterpart, ROE continuity,
and cable destination remain open.
Interpolating that candidate from D50 pitch gives a board search point
near `(90.05,155.75)` mm; independent D51 pitch gives
`(89.91,156.27)` mm, only 0.54 mm apart. Its straight-line chord to D92.1 is
166.2 mm, about 16 mm over the approximate 150 mm factory A13 length;
the chord to D38.1 is 140.8 mm. A D38-adjacent remote surface
landing therefore remains geometrically plausible; A13A itself
still lacks ROE continuity and a traced opposite cable end.
In the A13B corridor near D38,
the right-side white-wire/annulus pair near `(2286,2450)`/`(2288,2298)`
is the same physical feature formerly logged as A9B. A D92-local
two-face fit places its front annulus about 9.5 px from the solder
annulus `(1916,1950)`, which visibly traces west to registered
D92.1/ROE `(1719,1951)`. This strongly favors A13B over A9B; exact
through-hole pairing and cable continuity still hold formal landing
promotion. The candidate A13A-to-A13B straight chord is about
157.1 mm, 7 mm beyond the table's approximate 15 cm cut length
before wire routing. Measure the installed cable; A13A remains open.
`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`
and `(1159,3623)` on its shallow diagonal run. Projecting the fitted
D51 field across six overlapping component tiles places the A9A
drawing region beneath the same factory-wire bundle and mastic patch
in every view. A visible wire approach does not identify the hidden
joint. The old A9B-to-D38.12 solder trace used the displaced D38/D41
field. A corrected D38 three-pin cross-face fit projects the visible
A9 candidate front annulus `(2288,2298)` to solder `(1907,1982)`,
while a wider four-package fit places it near `(1914,1964)`, only
14 px from the open solder annulus `(1916,1950)`. The D92-local fit
narrows that miss to about 9.5 px, and the solder copper connects the
annulus directly to D92.1/ROE, not corrected D38.12/SYNC `(2076,2064)`.
This white joint is withdrawn as the preferred A9B candidate; see
`a9b-corrected-trace-review.json`. D38.12 itself has a visible short
solder spur west to an open annulus near `(2025,2063)`. Its candidate
front counterpart near `(2176,2404)` has no visible wire; it is a
better SYNC search anchor. Its front trace reaches a second bare
annulus near `(2178,2520)`; the likely solder counterpart near
`(2028,2170)` has a spur that visibly stops short of D38.10.
Do not merge SYNC with D38.10/13 from proximity. Both A9 ends
remain unpromoted.
`А:14` is the upper of two close parallel lines at `(1277,1832)` in
`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.
That lower `А:7` line is separately guarded at `(1161,1845)` and
`(1761,4062)` in the same respective views.
The owner backside identifies raw candidate right-hand printed joints
in `200522685`: A14B `(1825,2827)` and A7B `(1757,2854)`.
Their former D41-based board coordinates are withdrawn because the
D41 solder field was displaced about 500 pixels. The component face over
both D35-side candidate joints is covered by wire bundle and mastic;
no insulated-wire termination is directly visible there. At the D1
end, overlapping component
views `200411500` and `200439607` show two actual white-wire surface
starts below the fitted CPU: the printed-7 A7A joint `(607,2898)` maps
by the local D1 fit to `(14.597,184.485)` mm, and the adjacent A14A
joint `(803,2897)` maps to `(23.621,184.440)` mm. Their corrected
chords are 213.303 and 201.046 mm respectively. The old backside
through-hole positions `(1.697,179.350)` and `(10.449,179.305)` mm
have no matching white-wire terminations and are retracted as A7A/A14A.
The W7.1 and W14.1 source-PCB pads still occupy those stale positions;
relocate them to the proved surface joints and rework their copper
before fabrication. Exact wire cut lengths remain held for measurement.
`А:12` is guarded at `(1714,2216)` in `114604420` and `(1349,2148)`
in `114611058`, spanning the D13/R20-to-C96/D35 drawing regions.
The former reflected `D37` solder fit is now correctly identified as
upper-row D39 from the `.006` assembly order and adjacent decapped D92;
it does not constrain lower-row D37. The photographed `12` is beside
two through-hole joints at `(2075,600)` and `(2170,605)` in the mirrored
solder view `200530933`. Their global projection separates them by
4.100 mm, but neither joint visibly carries an insulated wire. The
drawing line ends after the C96 symbol, which does not prove a wire
termination at either joint or even their C96 identity while the
component face is hidden by the wire bundle/mastic. A12B therefore
has no accepted board coordinate or island assignment.
The exact `.009` sheet-1 supply group in `101827714` includes C96
among `C94...C98` on its +5 V-to-ground bypass branch. This supports
checking those two candidate joints as a bypass location, but does not
identify the hidden component or justify a RAM_OUT_EN assignment.
Direct component/reflected-solder D13 fits place D13.2 at `(1369,906)` in
`200450127` and `(2743.5,825)`
in `200537608`; neither face has an insulated-wire termination at the
pad. A tempting tinned white-wire end at `(1405,1479)` in `200439607`
is not a proved pad landing: the component cross-view is bare, while
its solder extrapolation leaves the fitted D13 field. The remote D13-side departure remains
unidentified, so both A12 ends remain pending.
`А:8` completes the drawing-image inventory at `(1624,276)` in
`114604420` and `(1105,443)` in `114611058`; both are plain endpoint
marks, not the separate circled drawing callout after R13. The D5-side
white-wire joint `(1335,1103)` in `200411500` has a visible 42 px
copper spur to fitted D5.1, proving A8A/STSTB at `(40.811,99.989)` mm.
The duplicate's revised 19 cm A8 length remains a source reading.
The former 195.9 mm chord is invalid after A8B's demotion.
The D38-side candidate white joints `(2286,2450)` and `(1810,2696)`
remain visible in `200418174`. The former A9B candidate is now
strongly associated with A13B/D92.1/ROE by a two-face trace; its
A9B/D38.12 assignment is withdrawn. The A8B/D38.8 assignment used
the displaced D38/D41 solder fit. The corrected
D38 cross-face projection sends the former A8B candidate near
`(2403,2363)` solder pixels, roughly 335 px from D38.8 and close to
the region printed `9`; this is an extrapolated search clue, not a
joint identity. A four-package D38/D41/D92/D39 fit independently
places it near `(2397,2379)`, 17 px away, confirming only the search
area (`a8b-corrected-trace-review.json`). Both board
coordinates and island assignments are withdrawn pending copper review.
