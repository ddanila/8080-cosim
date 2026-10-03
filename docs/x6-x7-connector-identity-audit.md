# `.009` display connector identity audit

The factory assembly wire table (`ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, PDF page 2, drawing sheet 3, item 151) assigns board point A:3 to X6 conductor 1 and A:4 to X6's marked return conductor 2. The independent system drawing `ДГШ3.031.011 Э6` identifies X6 as the two-conductor cable to display A5 МС6105.09 (`ref/schematics/system-bus-connector-map.md`). Exact `.009 Э3` sheet 2 (`ref/photos/dgsh5-109-009-e3/PXL_20260718_101932581.jpg`) labels output contact 3 VIDEO/601 and contact 4 ground/602. This is cross-source evidence that the documented display cable is X6/A:3/A:4.

The original-resolution factory assembly sheet-1 view `ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` labels the top-edge connector **X6** directly above VT2/VD3; the callout for item 151 reaches the same analog cluster. No X7 is marked in this top-right view. The cited `.009` output crop also does not name X7. The former board model assigned X7 a separate physical video footprint and BOM line without a supporting `.009` source. An unindexed source could still exist, so this is an evidence gap, not proof that no X7 was ever fitted.

The photographed A:3 joint is beside VT2/R65 and clearly separate from VD3; its exact copper path to VT2 emitter/R65.1 remains unmeasured. Keep A:3's physical continuity boundary until the board joint is tested or traceable in a registered solder-side image. The corrected model keeps VIDEO_OUT at VT2.1/R65.1, classifies X6 as the off-board `DISPLAY_CONN`, and removes X7 from the board JSON, generated source PCB, both routed snapshots, and BOM. The two short routed VIDEO_OUT segments between VT2.1 and R65.1 remain; 172 obsolete X7-route copper items and its four-segment ground spur were removed from each routed snapshot. Resolve the conductor-to-stage join only with direct board evidence. The legacy route-repair script still names X7 inside a provenance-hashed historical recipe and must not be replayed on the current board.

Current routed/source parity and DRC remain held; see
[the routed audit](routed-refresh-audit.md) and
[factory-wire fidelity](factory-wire-route-fidelity.md).
The connector correction does not establish whole-board routing readiness.
