# D7 sheet-1 gate-output crossing

Source: exact `.009 Э3` sheet-1 detail
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101805510.jpg`, native crop
`(950,3220)–(1600,3760)`. The lower pin-3 output is visibly labeled
**D105.3**, not D7.3. Its horizontal stroke at y≈3360 turns north near
`(1398,3360)`. The separate D7.11 output runs east around y≈3590,
roughly 230 px below that turn; no line or junction joins the two in this
native crop. No source-drawn D7.11/D105.3 output tie is established here.
The exact pixel coordinates and model disposition are recorded in
`ref/schematics/d7-d105-output-crossing-correction.json`.

The owner-board model already keeps D7.11 on `PROM_EN` and D105.3 on
qualified peripheral `/WR` (`IOWR`), matching the separate local source
strokes. Owner continuity closes D105.3 to D94.13, D29.5, D10.2,
D11.10, D26.36, and D27.36. D7.11 has not been tested directly against
D105.3, but such a measurement is an optional check for a hidden remote or
factory-modified path, not a source-required tie. Its probe sites are D7.11
near solder `(2245,1193)` in `200525009` and D105.3 near component
`(1108,1680)` in `200439607` / solder `(2807,1190)` in `200537608`.
Keep the model nets separate; see
`ref/photos/juku-pcb-2/d105-pin3-photo-review.json`. D7.3 remains a
different source branch to D29.2 as read in the D29 detail below.

The exact sheet-1 D29 detail in `PXL_20260718_101813438.jpg` crop
`(1000,3040)–(1740,3540)` adds a readable destination: the D7 NAND
section output pin 3 runs right, turns up, and reaches D29 physical input
pin 2. Its riser crosses the separate D29.7 line without a marked junction.
An independent native crop `(800,2850)–(1900,3730)` keeps the `Д7` label,
pin-3 output, rising stroke, and D29.2 landing in one view; this is the separate D7.3→D29.2 branch.
This closes D7.3→D29.2 **on the source drawing**, while owner-board continuity
remains to be checked. D29.5 instead belongs to the owner-closed D105.3/IOWR island.

The component-side board view `ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg` locates the marked D7 and its complete lead rows (pin 3 near `(3338,1320)`, pin 11 near `(3285,1485)`). The pin-3 visible copper runs north; no component-face bridge to pin 11 appears beside the package. This fits their separate source branches. Any remote D7.11-to-D105.3 path would need independent physical evidence.

The same owner crop `(3100,1100)–(3500,1650)` reads **КР1533ЛА3** on the populated D7 body (upside down in the photo). This confirms the D7 package identity and a later-series body marking than the generic drawn `ЛА3`. The body marking does not establish remote connectivity.

## Registered physical probes

The local registration in `ref/photos/juku-pcb-2/local-package-registration.json`
places D7.3 at solder `(2190,1029)` and D7.11 at `(2245,1193)` in
`PXL_20260710_200525009.jpg`. Their separate annuli have no visible local
B.Cu departure or bridge. Two component views, `200411500` and `200415237`,
show D7.3's northbound trace and no exposed D7.11 departure. Hidden or remote
copper remains possible.

The D7.3 front trace reaches a wire-covered ring near `(3356,975)` in
`200411500`. Independent D7 and D9 reflections and an adjacent-hole offset
favor solder hole `(2190,700)` over `(2138,732)` as its opposite face. The
covered drill centre prevents a definitive same-hole assignment; retain this
as a continuity candidate. Fit calculations and native crops are preserved in
`ref/photos/juku-pcb-2/d7-pin3-via-pair-review.json`.

The preferred solder hole has a visible B.Cu run east to annulus `(3065,730)`.
That far annulus registers to front ring `(2480,1015)` above the D8/D9 gap,
the independently reviewed D29.2 waypoint. Its northbound front trace aligns
with D29.2 at the cropped package edge, but cable hides a short segment.
Registration and tile-fit evidence are recorded in
`ref/photos/juku-pcb-2/d29-pin2-front-chase.json`.

With power removed, check D7.3 to its front ring, the preferred solder hole,
the far annulus, and D29.2 separately. The visible B.Cu run does not prove
the complete AMW_N path until both hidden ends pass continuity.

## D7.5 / D29.3 inhibit-input chase

Original-resolution sheet-1 `PXL_20260718_101813438.jpg` crop
`(850,2900)–(1850,3650)` shows D7 NAND input pin 5 on the same
conductor as D29 physical input pin 3. The two meet at a filled T junction.
D7.4 passes across this conductor without a junction and continues to
MEMW/D29.8. The D7.5/D29.3 conductor runs west out of this crop; the
archived image section does not identify its upstream endpoint. Preserve
`INHIB_STATUS_BOUNDARY` until that continuation or original-board continuity
is resolved. The registered owner solder probes are D7.5 near (2300,1029) in
200525009 and D29.3 near (2393,1588) in 200509593; the latter is the
third contact counted from D29.1 near (2489,1588). These are in separate
photo tiles and do not prove the source-drawn join. The full-sheet photo `PXL_20260718_101754468.jpg` shows this
conductor inside the dense central control bundle, but folds and overlapping
strokes prevent a unique upstream device-pin attribution. See
`ref/schematics/d7-d29-inhibit-upstream-review.json`; do not assign a nearby
D5, D22, or ROM-select line by proximity.
An overlap recheck aligns distinctive upper package landmarks across
`101813438`, `101809608`, and `101805510`, but the lower fold shifts the
projected conductor by about 14 pixels among parallel control lines. No
remote pin or unique junction is established by those photo translations.
The original-pixel `101805510` crops `(0,2850)–(2150,3450)` and
`(2050,2800)–(3072,3550)` expose D5.25 `/IORD`, D5.27 `/IOWR`, and D5.26
MWR as distinct nearby departures; their strokes are broken or shifted by
the vertical fold. None can be assigned to the projected inhibit row from
these photographs.
