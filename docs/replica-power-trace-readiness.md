# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **NOT READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 986
- Widened power segments (`>0.20 mm`): 485
- Total routed power length: 5527.740 mm
- Widened routed power length: 2305.810 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 391 | 201 | 0.200 | 1.000 | 2123.226 | 1007.903 | B.Cu, F.Cu |
| P5V | 470 | 236 | 0.200 | 1.000 | 2405.230 | 1045.186 | B.Cu, F.Cu |
| P12V | 57 | 23 | 0.200 | 1.000 | 446.234 | 98.025 | B.Cu, F.Cu |
| M12V | 52 | 18 | 0.200 | 1.000 | 481.070 | 133.590 | B.Cu, F.Cu |
| M5V_DERIVED | 16 | 7 | 0.200 | 1.000 | 71.981 | 21.106 | B.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 501 |
| 0.3 | 1 |
| 0.3235 | 1 |
| 0.3296 | 1 |
| 0.3692 | 1 |
| 0.384 | 2 |
| 0.399 | 1 |
| 0.4187 | 1 |
| 0.4198 | 1 |
| 0.42 | 29 |
| 0.4286 | 1 |
| 0.4483 | 2 |
| 0.4606 | 2 |
| 0.4832 | 1 |
| 0.4834 | 2 |
| 0.4836 | 2 |
| 0.4864 | 1 |
| 0.4954 | 1 |
| 0.5 | 1 |
| 0.514 | 1 |
| 0.52 | 3 |
| 0.5404 | 1 |
| 0.5488 | 1 |
| 0.5566 | 6 |
| 0.5651 | 1 |
| 0.5686 | 2 |
| 0.5716 | 1 |
| 0.5717 | 1 |
| 0.5918 | 1 |
| 0.5949 | 1 |
| 0.6002 | 1 |
| 0.6103 | 1 |
| 0.6157 | 1 |
| 0.6158 | 1 |
| 0.6164 | 1 |
| 0.6213 | 1 |
| 0.6256 | 2 |
| 0.6303 | 1 |
| 0.6316 | 1 |
| 0.648 | 1 |
| 0.6514 | 1 |
| 0.6578 | 2 |
| 0.6583 | 1 |
| 0.6586 | 1 |
| 0.6593 | 1 |
| 0.6688 | 1 |
| 0.6791 | 1 |
| 0.6792 | 1 |
| 0.7114 | 1 |
| 0.736 | 1 |
| 0.7596 | 2 |
| 0.781 | 2 |
| 0.7902 | 1 |
| 0.802 | 1 |
| 0.8145 | 1 |
| 0.8184 | 1 |
| 0.8264 | 1 |
| 0.84 | 1 |
| 0.8458 | 1 |
| 0.85 | 1 |
| 0.86 | 2 |
| 0.8746 | 1 |
| 0.8764 | 2 |
| 0.8798 | 2 |
| 0.9095 | 1 |
| 0.944 | 1 |
| 0.9506 | 1 |
| 0.97 | 1 |
| 0.9729 | 2 |
| 0.987 | 2 |
| 0.9958 | 2 |
| 0.9962 | 3 |
| 1 | 361 |

## Disposition

Do not use this routed package until the failures below are resolved.

## Failures

- Expected 992 routed power segments, found 986.
- Expected 491 widened power segments, found 485.
