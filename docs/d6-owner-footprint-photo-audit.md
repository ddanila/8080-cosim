# D6 owner footprint photo audit

The `.009` assembly `PXL_20260711_114604420.jpg` places D6 beside D8. Owner component photo `ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg` shows the marked КР556РТ4А in the left blue 2×8 socket, immediately left of the registered К155РЕ3 D8. A native crop `(1430,1240)`–`(1950,1550)` resolves D6's right-facing notch. The upper socket row runs approximately `(1503,1317)`–`(1897,1317)` and the lower row `(1503,1480)`–`(1897,1480)`. Thus physical pin 1 is at the upper **right**, pin 8 at upper left, pin 9 at lower left, and pin 16 at lower right in this photo.

The adjacent D8 photo registration in `ref/photos/juku-pcb-2/local-package-registration.json` fixes D8.8/.1 at image x=2058/2444 and source PCB x=74.442/92.222 mm. Its local scale is 17.78 mm/386 px horizontally and 7.62 mm/165 px vertically. The D9 native row was subsequently corrected from stale x2640..3011 to x2590..2977; combining corrected D8/D9 anchors gives a 0.615 mm RMS fit and shifts a D6-center extrapolation about 1.0 mm left of the D8-local result, exposing source-PCB/package-spacing uncertainty. D8 is the closer package, so the table uses its local scale as an **approximate** owner-board estimate:

| Pin | Owner front photo px | D8-local board estimate mm | Corrected source PCB mm | Routed variants still at mm |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1897, 1317 | 67.03, 109.36 | 66.55, 109.36 | 54.91, 117.905 |
| 8 | 1503, 1317 | 48.88, 109.36 | 48.77, 109.36 | 72.69, 117.905 |
| 9 | 1503, 1480 | 48.88, 116.89 | 48.77, 116.98 | 72.69, 110.285 |
| 16 | 1897, 1480 | 67.03, 116.89 | 66.55, 116.98 | 54.91, 110.285 |

The source PCB D6 footprint has now been changed from `+90°` at pin 1 `(54.91,117.905)` to `−90°` at `(66.55,109.36)`, putting its center near the D8-local photographed `(57.95,113.12)` mm estimate. Both routed variants still have the old `+90°` footprint. The original horizontal discrepancy was about 5.9 mm under this local fit. Absolute photo coordinates remain approximate because D6's apparent socket pitch is a little larger than D8's and the fit extrapolates left of D8. The end reversal is direct notch evidence independent of the millimetre estimate.

The older `endpoints.csv` seeds for D6.13/.14 sat on the component body
and between solder rails. Counting the marked socket's lower row now places
those two pins near `(1728,1480)/(1784,1480)` in `200411500`, reflected
to `(2016,1215)/(1961,1215)` in `200527310`. These are photo contact
centres; the separate chip-removed owner record already closes
`D6.13↔D6.14↔D13.12` on `D6_V_ENABLE`.

The generator now reproduces the saved source center `(57.66,113.165)` mm
and 270° rotation. The source/generator chip placement check covers D6 with
the other 105 modeled chips.

The source PCB has no tracks in the proposed D6 footprint window, so this source-only edit does not strand local routed copper. `kicad-cli pcb drc --format json` before/after reports 770→765 violations and 499→499 unconnected items. The original D6/D8 courtyard and pad overlaps disappear; no D6-specific violation remains. The board still has many unrelated design-rule findings and is not fabrication-ready.

This is a physical placement and orientation correction, **not** a change to D6's logical pin net assignments or the verified physical `.038` dump. Refit D6's neighboring copper against multiple package contacts before editing either routed board; then run full DRC and connection checks. C87's front candidate column `(1420,1315)`/`(1420,1535)` projects only approximately to `(45.05,109.27)`/`(45.05,119.43)` mm under the D8-local fit, outside D6's left end. Those remain unproved C87 holes.
