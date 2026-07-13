# FDC lower assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / ELECTRICAL MAPPING PENDING**

The photographed factory assembly drawing is registered to the five package centres
already fitted in the owner board photograph. D95, D101, and D102 define the affine
fit; D99 and D97 are independent checks. This establishes reference identity and
placement only, not component value or connectivity.

Held-out errors: D99 `0.910` mm; D97 `0.851` mm.

| Ref | Projected x,y mm | Current x,y mm | Delta mm | Drawing observation |
| --- | ---: | ---: | ---: | --- |
| D93 | 235.941, 73.335 | 235.941, 73.340 | -0.000, -0.005 | physical КР1818ВГ93 socket centre; factory drawing corrects the former D95-overlapping global placement |
| C10 | 252.361, 73.163 | 252.361, 73.163 | +0.000, -0.000 | vertical C10 immediately right of D93; replaces the former lower-row collision with D102 |
| C11 | 268.232, 93.540 | 268.232, 93.540 | +0.000, +0.000 | vertical capacitor between D95 and D99; owner component view shows its landings but no unambiguous body |
| C16 | 267.094, 101.055 | 267.094, 101.055 | +0.000, +0.000 | horizontal capacitor between the upper and lower IC rows |
| C15 | 280.230, 110.120 | 280.230, 110.120 | +0.000, -0.000 | vertical capacitor between D97 and D102; owner component view is cable-obscured |
| C19 | 292.893, 93.574 | 292.893, 93.574 | +0.000, -0.000 | vertical capacitor immediately right of D99 |
| R92 | 253.869, 101.194 | 253.869, 101.194 | +0.000, +0.000 | horizontal resistor below D95 |
| R99 | 241.207, 103.467 | 241.207, 103.467 | +0.000, -0.000 | horizontal resistor below-left of D95 |
| R100 | 299.776, 94.000 | 299.776, 94.000 | -0.000, -0.000 | upper resistor in the four-part row right of C19 |
| R102 | 299.253, 97.229 | 299.253, 97.229 | +0.000, +0.000 | second resistor in the four-part row right of C19 |
| R108 | 298.731, 100.458 | 298.731, 100.458 | -0.000, +0.000 | third resistor in the four-part row right of C19 |
| R86 | 298.208, 103.688 | 298.208, 103.688 | +0.000, -0.000 | lowest resistor in the four-part row right of C19 |
| C20 | 299.917, 110.117 | 303.997, 110.024 | -4.080, +0.093 | factory C20 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 303.997,110.024 mm drill-span centre |
| C22 | 302.204, 110.093 | 306.537, 110.024 | -4.333, +0.069 | factory C22 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 306.537,110.024 mm drill-span centre |
| C63 | 240.224, 141.607 | 176.100, 145.600 | +64.124, -3.993 | factory label reads C63, not C13, immediately right of D41; body-centre projection is placement evidence only and does not establish lead holes |

D93, C10, C11, C15, C16, C19, R92, R99, and the populated R100/R102/R108/R86 right-edge row have source-PCB footprints at their projected
factory-drawing positions. C20/C22 are also restored, but their table deltas are intentional: the drawing points identify the
overlapping body labels, whereas registered owner component and solder photos prove the actual adjacent 2.54 mm drill columns
at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans. The C63 target site remains an explicit
placement/BOM discrepancy until its lead holes and endpoints are reconciled with the `.009` board; do not silently merge it with `.006` analog parts.
Owner component photo `PXL_20260710_200418174.jpg` independently shows C19's grey vertical axial body and the four stacked resistor bodies in the same top-to-bottom order;
that corroborates population and orientation, while values and lead destinations remain continuity tasks. The registered solder view
`PXL_20260710_200522685.jpg` exposes C19's two distinct joints. Its value and both remote destinations remain boundaries. The same owner views
also show populated grey horizontal C16 between the IC rows and the red horizontal R92/R99 pair below D95. Their component-side landings and
backside joints corroborate the factory identities and 12.5/10.16 mm spans; unread markings and all six remote destinations remain boundaries.
Those owner views additionally show the two grey C20/C22 axial bodies and all four solder joints independently of the factory identity drawing; enhanced C20
pixels read `1Н5` verbatim, while its unit interpretation and C22's marking remain deliberately unpromoted.
The lower drawing also labels the vertical part beside D41 as `C63`, not `C13`.
Its body-centre projection is retained as a placement lead, but moving the generic
two-pin footprint there would overlap D41.13; owner-side lead-hole registration is
required before promoting C63, and this site must not be used to clear C13's D95 collision.
The owner component view does not expose a complete electrical path at either corrected
site: C11's landings are visible without an unambiguous body, while C15 is hidden by the
factory cable. Neither placement is connectivity evidence.
