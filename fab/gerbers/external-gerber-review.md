# Main board external Gerber/drill review

Package: `fab/gerbers`
Viewer: `@tracespace/cli` via `npx --yes @tracespace/cli --quiet`
Status: **NOT READY**

This report records the result of an attempted Tracespace render and
Chrome/Chromium screenshot capture of the fabrication inputs. `NOT READY`
means the attempt or an output check failed; it does not record a successful
visual review. The script checks SVG structure/viewBox and PNG size/signature,
not board geometry, layer correctness, readable labels, or vendor acceptance.

Regenerate with `python3 kicad/report_external_gerber_review.py`.
It requires `npx`, Tracespace, Chrome/Chromium, and the listed Gerber/drill files.
Output rows describe files present after the attempt. If rendering cannot
start, existing outputs may remain; a row's `PASS` alone does not prove a
fresh render. PNG table rows check size; capture/signature failures appear
in the failure list. Input hashes and PCB identity are not verified here.

## Inputs

- `fab/gerbers/juku_routed-F_Cu.gtl`
- `fab/gerbers/juku_routed-B_Cu.gbl`
- `fab/gerbers/juku_routed-F_Mask.gts`
- `fab/gerbers/juku_routed-B_Mask.gbs`
- `fab/gerbers/juku_routed-F_Silkscreen.gto`
- `fab/gerbers/juku_routed-B_Silkscreen.gbo`
- `fab/gerbers/juku_routed-Edge_Cuts.gm1`
- `fab/gerbers/juku_routed.drl`

## Rendered SVG Outputs

| File | Bytes | ViewBox | Status |
| --- | ---: | ---: | --- |
| fab/gerbers/review/tracespace/juku_routed-F_Cu.gtl.top.copper.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-B_Cu.gbl.bottom.copper.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-F_Mask.gts.top.soldermask.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-B_Mask.gbs.bottom.soldermask.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-F_Silkscreen.gto.top.silkscreen.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-B_Silkscreen.gbo.bottom.silkscreen.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-Edge_Cuts.gm1.all.outline.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed.drl.all.drill.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed.top.svg | - | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed.bottom.svg | - | - | FAIL |

## Browser Screenshots

| File | Bytes | Status |
| --- | ---: | --- |
| fab/gerbers/review/tracespace/juku_routed-tracespace-top.png | - | FAIL |
| fab/gerbers/review/tracespace/juku_routed-tracespace-bottom.png | - | FAIL |

## Failures

- npx executable not found
- juku_routed-F_Cu.gtl.top.copper.svg: missing or empty
- juku_routed-B_Cu.gbl.bottom.copper.svg: missing or empty
- juku_routed-F_Mask.gts.top.soldermask.svg: missing or empty
- juku_routed-B_Mask.gbs.bottom.soldermask.svg: missing or empty
- juku_routed-F_Silkscreen.gto.top.silkscreen.svg: missing or empty
- juku_routed-B_Silkscreen.gbo.bottom.silkscreen.svg: missing or empty
- juku_routed-Edge_Cuts.gm1.all.outline.svg: missing or empty
- juku_routed.drl.all.drill.svg: missing or empty
- juku_routed.top.svg: missing or empty
- juku_routed.bottom.svg: missing or empty
- juku_routed-tracespace-top.png: missing source SVG juku_routed.top.svg
- juku_routed-tracespace-bottom.png: missing source SVG juku_routed.bottom.svg
