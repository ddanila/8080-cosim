# D7 sheet-1 gate-output crossing

Source: exact `.009 Э3` sheet-1 detail `ref/photos/dgsh5-109-009-e3/PXL_20260718_101805510.jpg`, native crop `(1180,2550)–(1550,3450)`. A fresh original-pixel read corrects the former gate identity: the lower pin-3 output is **D105.3**, visibly labeled `Д105` in crop `(750,3000)–(1540,3750)`, not D7.3. D7.11 leaves the upper D7 NAND section and follows the right-hand vertical stroke into D105.3. D7.8 joins the separate left-hand stroke at a filled dot. The pin-3 stroke crosses that left-hand stroke without a dot. The exact drawing therefore depicts a D7.11/D105.3 output tie, not the previously reported D7.3/D7.11 tie. Both are outputs, so this unusual source join requires owner continuity before it can enter the model.

The owner-board model keeps D7.11 on `PROM_EN` and D105.3 on qualified peripheral `/WR` (`IOWR`). Owner continuity closes D105.3 to D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36, but has not tested D7.11 against D105.3. With power removed, measure D7.11↔D105.3 directly: the counted D105.3 owner contact is near component (1108,1680) in 200439607 / solder (2807,1190) in 200537608, and D7.11 is near solder (2245,1193) in 200525009. See `ref/photos/juku-pcb-2/d105-pin3-photo-review.json`. Then test D7.11↔D94.13 and D105.3↔R17.2 as independent cross-checks. Preserve the separate model nets until that conflict is resolved. D7.3 remains a different source branch to D29.2 as read in the D29 detail below; its upstream continuation is still unresolved.

The exact sheet-1 D29 detail in `PXL_20260718_101813438.jpg` crop
`(1000,3040)–(1740,3540)` adds a readable destination: the D7 NAND
section output pin 3 runs right, turns up, and reaches D29 physical input
pin 2. Its riser crosses the separate D29.7 line without a marked junction.
An independent native crop `(800,2850)–(1900,3730)` keeps the `Д7` label,
pin-3 output, rising stroke, and D29.2 landing in one view; the preceding
D105 correction does not change this D7.3→D29.2 read.
This closes D7.3→D29.2 **on the source drawing**, while owner-board continuity
and the unusual D7.11/D105.3 source output tie still need direct checks. The
former D29.5 interpretation remains disproved by owner continuity.

The component-side board view `ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg` locates the marked D7 and its complete lead rows (pin 3 near `(3338,1320)`, pin 11 near `(3285,1485)`). The pin-3 visible copper runs north; no component-face bridge to pin 11 appears beside the package. This fits their separate source branches but does not prove the D7.11-to-D105.3 remote path. That output tie remains a targeted continuity question, not an adopted net.

The same owner crop `(3100,1100)–(3500,1650)` reads **КР1533ЛА3** on the populated D7 body (upside down in the photo). This confirms the D7 package identity and a later-series body marking than the generic drawn `ЛА3`. The body marking cannot establish whether D7.11 is physically tied to D105.3.

The global panorama transform alone misses the local solder field by hundreds of pixels. A direct local registration in solder tile `PXL_20260710_200525009.jpg` now identifies the complete D7 2×7 field at top-row joints `(2080,1029)`–`(2410,1029)` and bottom-row joints `(2080,1193)`–`(2410,1193)`. It sits immediately left of the 2×8 D9 field and then the 2×8 D8 field, the mirror image of their component-side order. The new fit in `ref/photos/juku-pcb-2/local-package-registration.json` passes all independent pad checks with zero rounded-pixel residual.

Physical D7.3 is the third top joint near `(2190,1029)`; D7.11 is the fourth bottom joint from the left near `(2245,1193)`. A close review of the original solder pixels shows separate annuli and no local solder-face bridge or visible outgoing solder trace from either joint. The component photo likewise shows no local bridge beside the package. These two D7 contacts have no source-drawn tie to each other; their remote connectivity is independently unresolved. The source-drawn output tie to test is D7.11↔D105.3.

A renewed native crop of component tile `PXL_20260710_200411500.jpg`,
`(3030,750)–(3630,1750)`, places D7.11 at the fourth bottom-row
contact, near `(3285,1485)`. The independent July component tile
`PXL_20260710_200415237.jpg`, crop `(1300,1200)–(1950,1850)`, repeats
that contact near `(1580,1571)` with its exposed lead ending without a
visible front-copper departure beyond the package edge. D7.3 instead has
a distinct northbound front trace in both views. Together with the
separated solder joints this excludes a visible local two-face bridge at
the package, while leaving hidden or remote copper as open possibilities for each separate signal.

In component tile `PXL_20260710_200411500.jpg`, D7.3's front copper runs north from the lead and reaches an open plated hole near `(3352,955)`, partly occluded by a white insulated wire. Another front annulus is near `(3420,1008)`, on a separate vertical trace. The D7-only component-to-solder affine extrapolation places the first hole near `(2175,666)` in solder tile `200525009`, on a broad trace between distinct drilled holes. A wider crop `(2000,500)–(2400,800)` contains open solder holes near `(2190,700)` and `(2138,732)`, but their separation and offset do not uniquely register them to the two front holes. That single fit extrapolates beyond the package rows and cannot identify the opposite-face hole by itself. Probe D7.3 to the visible front hole first; use the paired-hole check below to prioritize its possible solder landing.

A second local extrapolation from the independently registered D9 package in
the same component/solder photo pair narrows that search. The white wire hides
the centre of D7.3's front ring; its exposed lower crescent puts a plausible
centre near `(3356,975)`, about 20 px below the old estimate. Using this
occluded centre, the D7 four-corner fit predicts solder `(2171,686)` and the
D9 four-corner fit predicts `(2199,685)`. The hole `(2190,700)` is about
17–24 px from those predictions, while `(2138,732)` is about 57–77 px away
and lies on a different narrow parallel run. The independent component tile
`200415237` crop `(1500,850)–(1850,1230)` repeats a wire-obscured ring on
the D7.3 northbound trace, distinct from the adjacent ring; it still
does not reveal the drill centre. A native grid recheck corrects that adjacent
open ring to about `(3420,1008)`, 30 px below the earlier y estimate. The D9
four-corner reflection projects it to solder `(2136,718)`, near the separate
open hole `(2138,732)`. That pair gives a local offset of about `(2,14)` px
beyond the package fit. Applying the same offset to the covered D7.3 ring
`(3356,975)` projects `(2201,699)`, about 11 px from the preferred solder
hole `(2190,700)`. This two-hole pattern supports the preferred same-hole
identity much more strongly than a single extrapolation; the D7.3 drill
centre remains wire-covered and the pair is still unmeasured. Probe
`(2190,700)` first, and retain its same-hole identity as conditional until
continuity or direct inspection confirms it. The paired coordinates and fit
are recorded in `ref/photos/juku-pcb-2/d7-pin3-via-pair-review.json`.

The native solder strip `(2100,640)–(4080,850)` follows the preferred
`(2190,700)` hole east on its own narrow conductor. It runs near y700,
bends down near x2690, and ends at a second open annulus around `(3065,730)`.
The separate `(2138,732)` hole is on the neighboring westbound line; the
bright tinned bar just east of `(3065,730)` has a visible gap from this
annulus. These are two possible probe sites on one photographed B.Cu run
**only if** continuity establishes the first hole as D7.3's front via.

An independent D9 four-corner reflection in the same two photos projects
back annulus `(3065,730)` to front `(2481,1020)`; a unique open ring is
visible at `(2480,1015)` in native front crop `(2350,900)–(2650,1200)`.
The D7-only fit independently predicts about `(2495,1019)`. The D9 fit is
within 5 px of the front ring, and the D7 fit within about 16 px despite
its longer extrapolation. This photo-registers the **second** annulus across
faces at the ring above the D8/D9 gap. Native crop
`(2460,990)–(2600,1420)` shows its own narrow front trace rising north
under the white cable; a thicker zigzag trace descending beside it has a
visible brown gap and belongs to a different conductor. The northbound
conductor aligns with D29.2 at the cropped upper package edge. The saved
component-grid panorama maps the independently reviewed D29.2 waypoint
`(2255,2352)` in `200354648` to `(2482,1005)` in `200411500`, within about
10 px of this same ring. A direct two-ring fit between the native component
tiles independently matches this waypoint to `(2480,1015)` and a neighboring
ring `(2366,1830)` to `(2590,465)`; it projects the separately counted D29.2
lead to `(2479,54)` at the visible cropped package edge. Thus the far B.Cu
annulus is the photo-registered opposite face of the D29.2 **waypoint**,
not an arbitrary gap hole. The white cable still hides a short
D29.2-to-waypoint segment, and the first
`(2190,700)` hole remains only a D7.3 same-hole candidate. Verify both ends
by continuity before promoting the entire owner-board AMW_N path; see
`ref/photos/juku-pcb-2/d29-pin2-front-chase.json`.

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
photo tiles and do not prove the source-drawn join. See
`ref/schematics/d7-d29-inhibit-upstream-review.json`. The full-sheet photo `PXL_20260718_101754468.jpg` shows this
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
