# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 815
- Widened power segments (`>0.20 mm`): 455
- Total routed power length: 4879.608 mm
- Widened routed power length: 1977.866 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 352 | 192 | 0.200 | 1.000 | 1901.961 | 838.397 | B.Cu, F.Cu |
| P5V | 340 | 218 | 0.200 | 1.000 | 1992.953 | 955.012 | B.Cu, F.Cu |
| P12V | 57 | 20 | 0.200 | 1.000 | 445.747 | 87.884 | B.Cu, F.Cu |
| M12V | 50 | 17 | 0.200 | 1.000 | 455.864 | 68.131 | B.Cu, F.Cu |
| M5V_DERIVED | 16 | 8 | 0.200 | 1.000 | 83.084 | 28.443 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 360 |
| 0.3007 | 1 |
| 0.3038 | 1 |
| 0.3218 | 1 |
| 0.3248 | 2 |
| 0.3265 | 1 |
| 0.3302 | 1 |
| 0.331 | 1 |
| 0.3366 | 1 |
| 0.3574 | 1 |
| 0.3593 | 1 |
| 0.3675 | 1 |
| 0.38 | 2 |
| 0.3894 | 1 |
| 0.4092 | 1 |
| 0.417 | 1 |
| 0.42 | 18 |
| 0.4256 | 1 |
| 0.4312 | 1 |
| 0.4412 | 1 |
| 0.4562 | 1 |
| 0.4572 | 1 |
| 0.46 | 1 |
| 0.4812 | 1 |
| 0.4834 | 2 |
| 0.4874 | 1 |
| 0.4896 | 1 |
| 0.4902 | 2 |
| 0.4913 | 3 |
| 0.5175 | 1 |
| 0.52 | 4 |
| 0.5226 | 1 |
| 0.5358 | 1 |
| 0.5376 | 1 |
| 0.5456 | 1 |
| 0.5566 | 6 |
| 0.5647 | 1 |
| 0.573 | 1 |
| 0.6123 | 1 |
| 0.6157 | 1 |
| 0.6184 | 1 |
| 0.6295 | 1 |
| 0.6304 | 1 |
| 0.6352 | 1 |
| 0.6358 | 1 |
| 0.6531 | 1 |
| 0.6552 | 1 |
| 0.657 | 1 |
| 0.6685 | 1 |
| 0.6686 | 1 |
| 0.6688 | 2 |
| 0.711 | 1 |
| 0.712 | 1 |
| 0.7258 | 1 |
| 0.73 | 2 |
| 0.7596 | 1 |
| 0.7763 | 1 |
| 0.7886 | 1 |
| 0.81 | 1 |
| 0.8798 | 1 |
| 0.8865 | 1 |
| 0.9014 | 1 |
| 0.9379 | 1 |
| 0.9404 | 1 |
| 0.9539 | 1 |
| 0.9856 | 1 |
| 0.9938 | 3 |
| 0.9962 | 1 |
| 1 | 353 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 815 power segments present, 455 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
