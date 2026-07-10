# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 748
- Widened power segments (`>0.20 mm`): 451
- Total routed power length: 4977.528 mm
- Widened routed power length: 2341.088 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 351 | 184 | 0.200 | 1.000 | 1926.969 | 805.041 | B.Cu, F.Cu |
| P5V | 301 | 210 | 0.200 | 1.000 | 1994.650 | 1050.610 | B.Cu, F.Cu |
| P12V | 37 | 25 | 0.200 | 1.000 | 461.706 | 206.048 | B.Cu, F.Cu |
| M12V | 46 | 22 | 0.200 | 1.000 | 509.045 | 225.919 | B.Cu, F.Cu |
| M5V_DERIVED | 13 | 10 | 0.200 | 1.000 | 85.159 | 53.470 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 297 |
| 0.3031 | 1 |
| 0.3202 | 1 |
| 0.3216 | 1 |
| 0.322 | 1 |
| 0.3265 | 1 |
| 0.3454 | 2 |
| 0.3622 | 1 |
| 0.3664 | 1 |
| 0.377 | 2 |
| 0.3772 | 1 |
| 0.38 | 2 |
| 0.3836 | 1 |
| 0.4047 | 1 |
| 0.4052 | 2 |
| 0.4075 | 1 |
| 0.4198 | 2 |
| 0.42 | 16 |
| 0.4256 | 2 |
| 0.4322 | 2 |
| 0.4342 | 2 |
| 0.4427 | 1 |
| 0.4461 | 1 |
| 0.46 | 1 |
| 0.4832 | 1 |
| 0.4834 | 3 |
| 0.4835 | 1 |
| 0.4836 | 2 |
| 0.4865 | 1 |
| 0.4904 | 1 |
| 0.4938 | 2 |
| 0.5 | 1 |
| 0.5022 | 2 |
| 0.5166 | 2 |
| 0.5175 | 1 |
| 0.52 | 3 |
| 0.5474 | 1 |
| 0.5566 | 6 |
| 0.5599 | 1 |
| 0.5758 | 1 |
| 0.5865 | 1 |
| 0.6124 | 2 |
| 0.6143 | 1 |
| 0.6157 | 1 |
| 0.62 | 1 |
| 0.6236 | 1 |
| 0.6282 | 1 |
| 0.6418 | 1 |
| 0.6422 | 1 |
| 0.6507 | 1 |
| 0.6538 | 1 |
| 0.656 | 1 |
| 0.6685 | 1 |
| 0.6688 | 1 |
| 0.6852 | 1 |
| 0.7176 | 1 |
| 0.738 | 1 |
| 0.7444 | 3 |
| 0.7544 | 1 |
| 0.7596 | 2 |
| 0.7674 | 1 |
| 0.8038 | 1 |
| 0.8145 | 1 |
| 0.8206 | 1 |
| 0.8293 | 1 |
| 0.833 | 1 |
| 0.84 | 1 |
| 0.8498 | 1 |
| 0.8656 | 1 |
| 0.8674 | 2 |
| 0.8798 | 1 |
| 0.885 | 2 |
| 0.8949 | 1 |
| 0.937 | 1 |
| 0.9465 | 1 |
| 0.9852 | 1 |
| 0.996 | 3 |
| 1 | 331 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 748 power segments present, 451 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
