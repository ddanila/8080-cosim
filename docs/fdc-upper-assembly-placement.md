# FDC upper assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / ELECTRICAL MAPPING PENDING**

The factory drawing places C12 between photo-fitted D94/D100 and C9 between
photo-fitted D100/D98. Each target is interpolated only between its adjacent
package centres. An independent D94-to-D98 interpolation predicts held-out
D100 within `1.309` mm.

| Ref | Bracket | Fraction | Projected x,y mm | Current x,y mm | Delta mm | Observation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| C12 | D94/D100 | 0.486906 | 253.218, 33.954 | 253.218, 33.954 | -0.000, +0.000 | vertical C12 between D94 and D100; owner component view shows the landing area without an unambiguous fitted body |
| C9 | D100/D98 | 0.561111 | 285.807, 33.590 | 285.807, 33.590 | -0.000, +0.000 | vertical C9 between D100 and D98; owner component view is hidden by the black factory cable |

Neither owner-photo site exposes a complete electrical path: C12 has no
unambiguous visible body and C9 is cable-obscured. These remain placement-only
records and do not validate the inherited `.006` analog net assignments.
