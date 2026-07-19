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
the common tinned +5 V rail. Owner continuity, rather than photo geometry,
fixes the signal endpoints. A second, alternate-angle owner photo reads `6К2` on
R87 and R88. R89 is partly socket-obscured but visually identical; the factory
equipment list also assigns exactly three МЛТ-0,125 6.2 kΩ ±5% resistors
to `ДГШ5.087.009`. Because that designation differs from the target
`ДГШ5.109.009`, it is corroboration only; the photo-readable pair and identical
third body are the target-board value evidence.

| Ref | Value | Signal side | Proved nodes | Component signal px | Solder signal px |
| --- | ---: | --- | --- | ---: | ---: |
| R87 | 6.2 kΩ | `FDC_WE_N` | D94.4, D93.2 | 1485.0, 1553.0 | 2190.0, 1323.0 |
| R88 | 6.2 kΩ | `FDC_RE_N` | D94.3, D93.4 | 1539.0, 1553.0 | 2140.0, 1323.0 |
| R89 | 6.2 kΩ | `D94_D1_D99_A2N` | D94.2, D99.9 | 1594.0, 1553.0 | 2088.0, 1323.0 |

All three opposite resistor pads enter the same visibly tinned +5 V rail.
Owner continuity maps R87/R88/R89 to D94 D3/D2/D1 respectively.
The separate D94 D0 node is pulled up only by R8 2 kΩ in the measured scope.
