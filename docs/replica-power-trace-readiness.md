# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 2650
- Widened power segments (`>0.20 mm`): 284
- Total routed power length: 7190.106 mm
- Widened routed power length: 1208.486 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 1237 | 108 | 0.200 | 1.000 | 2977.603 | 493.041 | B.Cu, F.Cu |
| P5V | 938 | 150 | 0.200 | 1.000 | 2468.944 | 596.215 | B.Cu, F.Cu |
| P12V | 393 | 10 | 0.200 | 1.000 | 1091.132 | 29.959 | B.Cu, F.Cu |
| M12V | 61 | 10 | 0.200 | 1.000 | 564.841 | 68.298 | B.Cu, F.Cu |
| M5V_DERIVED | 21 | 6 | 0.200 | 1.000 | 87.586 | 20.973 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 2366 |
| 0.3 | 1 |
| 0.3235 | 1 |
| 0.3692 | 1 |
| 0.399 | 1 |
| 0.4187 | 1 |
| 0.42 | 15 |
| 0.4286 | 1 |
| 0.4483 | 1 |
| 0.4836 | 2 |
| 0.4864 | 1 |
| 0.5566 | 6 |
| 0.5651 | 1 |
| 0.5686 | 2 |
| 0.5717 | 1 |
| 0.5918 | 1 |
| 0.5949 | 1 |
| 0.6002 | 1 |
| 0.6103 | 1 |
| 0.6157 | 1 |
| 0.6164 | 1 |
| 0.6256 | 2 |
| 0.6316 | 1 |
| 0.648 | 1 |
| 0.6586 | 1 |
| 0.6688 | 1 |
| 0.7114 | 1 |
| 0.736 | 1 |
| 0.7596 | 1 |
| 0.781 | 2 |
| 0.7902 | 1 |
| 0.802 | 1 |
| 0.8145 | 1 |
| 0.8264 | 1 |
| 0.84 | 1 |
| 0.8458 | 1 |
| 0.85 | 1 |
| 0.8746 | 1 |
| 0.8764 | 2 |
| 0.8798 | 2 |
| 0.987 | 2 |
| 0.9958 | 2 |
| 0.9962 | 3 |
| 1 | 213 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 2650 power segments present, 284 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
