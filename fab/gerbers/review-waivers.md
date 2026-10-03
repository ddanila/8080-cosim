# Main board DRC waiver review

Source DRC: `fab/gerbers/juku_routed-drc.json`
Status: **NOT ACCEPTED**

This report is intentionally exact-count based. If the board changes and
any remaining DRC count changes, the waiver must be reviewed again rather
than silently carrying an old disposition forward.

## Waived DRC Classes

| Type | Count | Rationale |
| --- | ---: | --- |
| courtyards_overlap | 108 | Dense authentic placement; assembly-fit review item, not a copper/routing fault. |
| pth_inside_courtyard | 68 | Dense authentic placement; through-hole/socket fit review item, not an electrical fault. |
| silk_over_copper | 199 | Silkscreen clipped by mask/copper; cosmetic unless assembly-critical marks become unreadable. |
| silk_overlap | 199 | Silkscreen-to-silkscreen overlap in dense labels/outlines; cosmetic assembly-readability item. |
| text_thickness | 199 | GOST/TrueType stroke warning; manufacturing-readability item, not fabrication geometry. |

## Independent Gerber Render

Independent render smoke command used for this package:

```sh
npx --yes @tracespace/cli --quiet --out=/tmp/juku-tracespace fab/gerbers/juku_routed-F_Cu.gtl fab/gerbers/juku_routed-B_Cu.gbl fab/gerbers/juku_routed-F_Mask.gts fab/gerbers/juku_routed-B_Mask.gbs fab/gerbers/juku_routed-F_Silkscreen.gto fab/gerbers/juku_routed-B_Silkscreen.gbo fab/gerbers/juku_routed-Edge_Cuts.gm1 fab/gerbers/juku_routed.drl
```

The automated order-readiness gate now runs
`kicad/report_external_gerber_review.py`, which renders the same package
through Tracespace and writes `fab/gerbers/external-gerber-review.md` plus
top/bottom review screenshots.

## Failures

- Unconnected items are not waivable here: 56
- `courtyards_overlap` count changed: expected 107, got 108
- `pth_inside_courtyard` count changed: expected 0, got 68
- Unexpected non-waived DRC type(s): `track_dangling`=24, `via_dangling`=1
