# `.009` display connector identity audit

## Source identity

The factory assembly wire table (`ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, PDF page 2, drawing sheet 3, item 151) assigns board point A:3 to X6 conductor 1 and A:4 to X6's marked return conductor 2. The independent system drawing `ДГШ3.031.011 Э6` identifies X6 as the two-conductor cable to display A5 МС6105.09 (`ref/schematics/system-bus-connector-map.md`). Exact `.009 Э3` sheet 2 (`ref/photos/dgsh5-109-009-e3/PXL_20260718_101932581.jpg`) labels output contact 3 VIDEO/601 and contact 4 ground/602. This is cross-source evidence that the documented display cable is X6/A:3/A:4.

The original-resolution factory assembly sheet-1 view `ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` labels the top-edge connector **X6** directly above VT2/VD3; the callout for item 151 reaches the same analog cluster. No X7 is marked in this top-right view. The cited `.009` output crop also does not name X7. No indexed `.009` source supports a separate physical X7 video footprint or BOM line. An unindexed source could still exist, so this is an evidence gap, not proof that no X7 was ever fitted.

## Current model and continuity hold

X6 is the off-board `DISPLAY_CONN`. Its board joints are modeled as:

| Cable conductor | Board joint | Footprint pad | Modeled net |
| --- | --- | --- | --- |
| X6.1 | A:3, beside VT2/R65 | AX603.1 | X6_A3_BOUNDARY |
| X6.2 | A:4 | AX604.1 | GND |

A:3 is separate from VD3, but its copper path to VT2 emitter/R65.1 remains
unmeasured. Keep `X6_A3_BOUNDARY` separate from `VIDEO_OUT` until direct
board evidence proves the join. The routed `VIDEO_OUT` connection between
VT2.1 and R65.1 remains. X7 is absent from board JSON, all three PCB
variants, and BOM.

The source-board mapping guard is `kicad/check_x6_offboard_landings.py`.
It checks modeled surface joints and their evidence mapping; a PASS does
not prove physical continuity. Photo registration is retained in
[the cable record](../ref/photos/juku-pcb-2/x6-cable-registration.json).

The default mode of `kicad/repair_fdc_route_gaps.py` still targets X7 in a
provenance-hashed historical recipe; do not replay that mode on the current
board.

## Release boundary

Current routed/source parity and DRC remain held; see
[the routed audit](routed-refresh-audit.md) and
[factory-wire fidelity](factory-wire-route-fidelity.md).
The connector correction does not establish whole-board routing readiness.
