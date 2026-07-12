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
| C16 | 267.094, 101.055 | absent | - | horizontal capacitor between the upper and lower IC rows |
| C15 | 280.230, 110.120 | 280.230, 110.120 | +0.000, -0.000 | vertical capacitor between D97 and D102; owner component view is cable-obscured |
| C19 | 292.893, 93.574 | absent | - | vertical capacitor immediately right of D99 |
| R92 | 253.869, 101.194 | absent | - | horizontal resistor below D95 |
| R99 | 241.207, 103.467 | absent | - | horizontal resistor below-left of D95 |
| R100 | 299.776, 94.000 | absent | - | upper resistor in the four-part row right of C19 |
| R102 | 299.253, 97.229 | absent | - | second resistor in the four-part row right of C19 |
| R108 | 298.731, 100.458 | absent | - | third resistor in the four-part row right of C19 |
| R86 | 298.208, 103.688 | absent | - | lowest resistor in the four-part row right of C19 |
| C20 | 299.917, 110.117 | absent | - | first vertical capacitor at the right end of D102 |
| C22 | 302.204, 110.093 | absent | - | second vertical capacitor at the right end of D102 |
| C63 | 240.224, 141.607 | 176.100, 145.600 | +64.124, -3.993 | factory label reads C63, not C13, immediately right of D41; body-centre projection is placement evidence only and does not establish lead holes |

D93, C10, C11, and C15 have source-PCB footprints at their projected
factory-drawing positions. The other named parts remain explicit physical/BOM omissions until their package and electrical endpoints
are reconciled with the `.009` board; do not silently merge them with `.006` analog parts.
The lower drawing also labels the vertical part beside D41 as `C63`, not `C13`.
Its body-centre projection is retained as a placement lead, but moving the generic
two-pin footprint there would overlap D41.13; owner-side lead-hole registration is
required before promoting C63, and this site must not be used to clear C13's D95 collision.
The owner component view does not expose a complete electrical path at either corrected
site: C11's landings are visible without an unambiguous body, while C15 is hidden by the
factory cable. Neither placement is connectivity evidence.
