# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **NOT READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 2744
- Widened power segments (`>0.20 mm`): 284
- Total routed power length: 7219.757 mm
- Widened routed power length: 1208.486 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 1333 | 108 | 0.200 | 1.000 | 3041.178 | 493.041 | B.Cu, F.Cu |
| P5V | 940 | 150 | 0.200 | 1.000 | 2480.041 | 596.215 | B.Cu, F.Cu |
| P12V | 388 | 10 | 0.200 | 1.000 | 1050.510 | 29.959 | B.Cu, F.Cu |
| M12V | 62 | 10 | 0.200 | 1.000 | 560.442 | 68.298 | B.Cu, F.Cu |
| M5V_DERIVED | 21 | 6 | 0.200 | 1.000 | 87.586 | 20.973 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 2460 |
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

Do not use this routed package until the failures below are resolved.

## Failures

- Expected 2738 routed power segments, found 2744.
