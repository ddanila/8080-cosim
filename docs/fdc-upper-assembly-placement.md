# FDC upper assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / D94 PULL-UPS IDENTIFIED**

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

## D94 pull-up row

The same factory view labels the three vertical bodies immediately left of D94
as R87, R88, and R89 from left to right. The owner component photograph preserves
that order. Its reflected solder mate exposes three non-crossing signal traces and
the common tinned +5 V rail, closing the resistor identities without inferring a
hidden D94.1 consumer.

| Ref | Signal side | Proved nodes | Component signal px | Solder signal px |
| --- | --- | --- | ---: | ---: |
| R87 | `D94_A3_D104_X4_PULLUP` | D94.13, D104.7 | 1485.0, 1553.0 | 2190.0, 1323.0 |
| R88 | `D94_A4_D101_Q0_PULLUP` | D94.14, D101.7 | 1539.0, 1553.0 | 2140.0, 1323.0 |
| R89 | `D94_D0_BOUNDARY` | D94.1 | 1594.0, 1553.0 | 2088.0, 1323.0 |

All three opposite resistor pads enter the same visibly tinned +5 V rail.
R89 identifies the pull-up on D94.1, but the absence of an additional hidden
branch remains a continuity/operating-capture boundary.
