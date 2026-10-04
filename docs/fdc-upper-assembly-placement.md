# FDC upper assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / D94 PULL-UPS IDENTIFIED**

Regenerate from the repository root with
`/usr/bin/python3 kicad/report_fdc_upper_assembly_placement.py`.
That interpreter needs KiCad's `pcbnew` module and Pillow; materialize
the original images through [Git LFS](git-lfs-policy.md#local-use).
The command overwrites this report, its JSON companion, and its review overlay.

The guard checks recorded pull-up mappings and selected value-source hashes,
then calculates placement from recorded anchors and reads source-PCB pad
centres. The D100 held-out error must be at most 1.5 mm, but missing
target footprints and nonzero placement deltas do not cause failure.
A pass does not prove pad-net assignments or metered continuity.

The factory drawing places C12 between photo-fitted D94/D100 and C9 between
photo-fitted D100/D98. Each target is interpolated only between its adjacent
package centres. An independent D94-to-D98 interpolation predicts held-out
D100 within `1.309` mm.

| Ref | Bracket | Fraction | Projected x,y mm | Current x,y mm | Delta mm | Observation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| C12 | D94/D100 | 0.486906 | 253.218, 33.954 | 253.218, 33.954 | -0.000, +0.000 | vertical C12 between D94 and D100; May and early July views show a bare gap, but later July owner image 202708344 shows a fitted green axial body in that exact gap, with one lead to D100.20/+5 V and the other to D94.8/GND; its value and permanent population history remain open |
| C9 | D100/D98 | 0.561111 | 285.807, 33.590 | 285.807, 33.590 | -0.000, +0.000 | vertical C9 between D100 and D98; earlier overhead owner view is cable-hidden, but later July image 202708344 exposes a green two-lead body in this gap; value and individual rail joins remain open |

The later owner image `PXL_20260710_202708344.jpg` shows green two-lead
bodies in both gaps. C12's visible leads reach D100.20/+5 V and D94.8/GND.
C9 remains partly cable-obscured; its individual rail joins and both values
are unproved. The `.009` sheet-1 bypass symbols establish +5 V/GND function
for both references. Neither site verifies the replica's numbered pad mapping.
See [late bypass evidence](../ref/photos/juku-pcb-2/fdc-bypass-late-population-review.json).

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
