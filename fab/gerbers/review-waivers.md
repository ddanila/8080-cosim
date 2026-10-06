# Main board DRC waiver review

Source DRC: `fab/gerbers/juku_routed-drc.json`
Status: **NOT ACCEPTED**

This report is intentionally exact-count based. If the board changes and
any remaining DRC count changes, the waiver must be reviewed again rather
than silently carrying an old disposition forward. The generator reads
saved DRC JSON; it does not rerun DRC, verify the current PCB identity,
or compare individual finding geometry. A matching count preserves the
recorded rationale; it is not a new visual assembly review.

Regenerate with `python3 kicad/report_review_waivers.py`.
The command overwrites this report, returning 0 for accepted counts or 3
for a hold. Optional arguments are the saved DRC JSON and output path.

## Waiver baselines

| Type | Count | Accepted count | Count check | Recorded rationale |
| --- | ---: | ---: | --- | --- |
| courtyards_overlap | 108 | 107 | HOLD | Dense authentic placement; assembly-fit review item, not a copper/routing fault. |
| pth_inside_courtyard | 68 | 0 | HOLD | Dense authentic placement; through-hole/socket fit review item, not an electrical fault. |
| silk_over_copper | 199 | 199 | MATCH | Silkscreen clipped by mask/copper; cosmetic unless assembly-critical marks become unreadable. |
| silk_overlap | 199 | 199 | MATCH | Silkscreen-to-silkscreen overlap in dense labels/outlines; cosmetic assembly-readability item. |
| text_thickness | 199 | 199 | MATCH | GOST/TrueType stroke warning; manufacturing-readability item, not fabrication geometry. |

## Independent Gerber Render

Render verification is a separate command:

```sh
python3 kicad/report_external_gerber_review.py
```

It renders the fabrication inputs through Tracespace and writes
`fab/gerbers/external-gerber-review.md` plus top/bottom review images.
The waiver generator does not run that command or establish render freshness.

## Failures

- Unconnected items are not waivable here: 59
- `courtyards_overlap` count changed: expected 107, got 108
- `pth_inside_courtyard` count changed: expected 0, got 68
- Unexpected non-waived DRC type(s): `track_dangling`=24, `via_dangling`=1
