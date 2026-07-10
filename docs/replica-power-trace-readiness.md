# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 742
- Widened power segments (`>0.20 mm`): 430
- Total routed power length: 4878.740 mm
- Widened routed power length: 2260.334 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 320 | 168 | 0.200 | 1.000 | 1833.836 | 878.279 | B.Cu, F.Cu |
| P5V | 313 | 209 | 0.200 | 1.000 | 1975.140 | 954.811 | B.Cu, F.Cu |
| P12V | 46 | 26 | 0.200 | 1.000 | 471.387 | 224.428 | B.Cu, F.Cu |
| M12V | 44 | 16 | 0.200 | 1.000 | 515.643 | 161.729 | B.Cu, F.Cu |
| M5V_DERIVED | 19 | 11 | 0.200 | 1.000 | 82.733 | 41.088 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 312 |
| 0.3217 | 1 |
| 0.3368 | 1 |
| 0.3382 | 1 |
| 0.3412 | 1 |
| 0.363 | 1 |
| 0.366 | 1 |
| 0.3664 | 1 |
| 0.38 | 2 |
| 0.388 | 2 |
| 0.4183 | 1 |
| 0.4194 | 1 |
| 0.4198 | 2 |
| 0.42 | 11 |
| 0.4256 | 2 |
| 0.4326 | 1 |
| 0.434 | 1 |
| 0.46 | 1 |
| 0.4712 | 2 |
| 0.4832 | 1 |
| 0.4834 | 5 |
| 0.4896 | 1 |
| 0.5 | 1 |
| 0.5092 | 1 |
| 0.5175 | 1 |
| 0.5188 | 1 |
| 0.52 | 2 |
| 0.5361 | 1 |
| 0.5566 | 7 |
| 0.5599 | 1 |
| 0.577 | 1 |
| 0.5835 | 1 |
| 0.6042 | 1 |
| 0.6103 | 1 |
| 0.6302 | 1 |
| 0.6306 | 2 |
| 0.6345 | 1 |
| 0.6358 | 1 |
| 0.7084 | 1 |
| 0.7354 | 1 |
| 0.7596 | 1 |
| 0.768 | 1 |
| 0.7862 | 1 |
| 0.8145 | 1 |
| 0.8203 | 1 |
| 0.8344 | 1 |
| 0.855 | 1 |
| 0.8656 | 2 |
| 0.8674 | 2 |
| 0.8742 | 2 |
| 0.8744 | 1 |
| 0.8798 | 1 |
| 0.9042 | 1 |
| 0.9227 | 1 |
| 0.9516 | 2 |
| 0.9553 | 1 |
| 0.9566 | 1 |
| 1 | 343 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 742 power segments present, 430 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
