# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 745
- Widened power segments (`>0.20 mm`): 452
- Total routed power length: 4901.731 mm
- Widened routed power length: 2253.284 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 311 | 188 | 0.200 | 1.000 | 1866.942 | 907.353 | B.Cu, F.Cu |
| P5V | 306 | 217 | 0.200 | 1.000 | 1992.597 | 1095.858 | B.Cu, F.Cu |
| P12V | 41 | 17 | 0.200 | 1.000 | 458.965 | 133.528 | B.Cu, F.Cu |
| M12V | 67 | 21 | 0.200 | 1.000 | 497.155 | 71.870 | B.Cu, F.Cu |
| M5V_DERIVED | 20 | 9 | 0.200 | 1.000 | 86.073 | 44.675 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 293 |
| 0.3007 | 1 |
| 0.3038 | 1 |
| 0.3121 | 2 |
| 0.326 | 2 |
| 0.3265 | 2 |
| 0.3557 | 1 |
| 0.3622 | 2 |
| 0.371 | 1 |
| 0.377 | 1 |
| 0.38 | 5 |
| 0.4092 | 1 |
| 0.4163 | 3 |
| 0.42 | 15 |
| 0.4256 | 1 |
| 0.4468 | 1 |
| 0.46 | 1 |
| 0.4686 | 1 |
| 0.4741 | 1 |
| 0.4822 | 1 |
| 0.4834 | 4 |
| 0.4846 | 1 |
| 0.486 | 1 |
| 0.488 | 2 |
| 0.493 | 1 |
| 0.4954 | 3 |
| 0.4956 | 1 |
| 0.5175 | 1 |
| 0.5199 | 1 |
| 0.52 | 2 |
| 0.5236 | 1 |
| 0.5258 | 3 |
| 0.55 | 2 |
| 0.5566 | 6 |
| 0.5676 | 1 |
| 0.6032 | 1 |
| 0.6102 | 1 |
| 0.6156 | 1 |
| 0.6157 | 1 |
| 0.6236 | 1 |
| 0.6278 | 2 |
| 0.6279 | 1 |
| 0.637 | 1 |
| 0.6477 | 1 |
| 0.6529 | 1 |
| 0.6562 | 1 |
| 0.6584 | 1 |
| 0.6686 | 1 |
| 0.6688 | 1 |
| 0.68 | 1 |
| 0.6838 | 1 |
| 0.7209 | 1 |
| 0.7432 | 1 |
| 0.7678 | 1 |
| 0.768 | 1 |
| 0.7894 | 2 |
| 0.8216 | 1 |
| 0.825 | 1 |
| 0.8283 | 1 |
| 0.8477 | 1 |
| 0.85 | 1 |
| 0.8684 | 1 |
| 0.8784 | 1 |
| 0.8798 | 1 |
| 0.8866 | 1 |
| 0.9804 | 1 |
| 0.9932 | 1 |
| 0.9962 | 1 |
| 1 | 344 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 745 power segments present, 452 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
