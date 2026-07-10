# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 779
- Widened power segments (`>0.20 mm`): 439
- Total routed power length: 4886.442 mm
- Widened routed power length: 2195.789 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 311 | 177 | 0.200 | 1.000 | 1910.530 | 934.220 | B.Cu, F.Cu |
| P5V | 348 | 216 | 0.200 | 1.000 | 1974.670 | 1020.218 | B.Cu, F.Cu |
| P12V | 49 | 25 | 0.200 | 1.000 | 454.378 | 162.965 | B.Cu, F.Cu |
| M12V | 52 | 12 | 0.200 | 1.000 | 460.987 | 53.329 | B.Cu, F.Cu |
| M5V_DERIVED | 19 | 9 | 0.200 | 1.000 | 85.877 | 25.057 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 340 |
| 0.3038 | 1 |
| 0.3142 | 1 |
| 0.3224 | 1 |
| 0.3265 | 3 |
| 0.3359 | 1 |
| 0.3549 | 1 |
| 0.366 | 2 |
| 0.38 | 1 |
| 0.382 | 1 |
| 0.3924 | 1 |
| 0.417 | 1 |
| 0.4172 | 1 |
| 0.42 | 14 |
| 0.4301 | 1 |
| 0.431 | 1 |
| 0.441 | 1 |
| 0.4436 | 1 |
| 0.46 | 1 |
| 0.4832 | 3 |
| 0.4834 | 4 |
| 0.4848 | 1 |
| 0.488 | 2 |
| 0.4925 | 1 |
| 0.5174 | 1 |
| 0.5175 | 1 |
| 0.5184 | 1 |
| 0.5198 | 1 |
| 0.52 | 2 |
| 0.534 | 1 |
| 0.542 | 1 |
| 0.5434 | 1 |
| 0.5566 | 6 |
| 0.5572 | 1 |
| 0.57 | 1 |
| 0.5757 | 2 |
| 0.5833 | 1 |
| 0.6102 | 3 |
| 0.612 | 2 |
| 0.6157 | 1 |
| 0.6173 | 1 |
| 0.6328 | 1 |
| 0.6334 | 1 |
| 0.6386 | 1 |
| 0.6478 | 1 |
| 0.648 | 2 |
| 0.6515 | 1 |
| 0.6543 | 1 |
| 0.6608 | 1 |
| 0.6637 | 1 |
| 0.6686 | 1 |
| 0.6688 | 3 |
| 0.68 | 1 |
| 0.6906 | 1 |
| 0.6996 | 1 |
| 0.7596 | 3 |
| 0.7734 | 1 |
| 0.775 | 1 |
| 0.7763 | 1 |
| 0.7862 | 1 |
| 0.8389 | 1 |
| 0.84 | 1 |
| 0.8478 | 1 |
| 0.86 | 1 |
| 0.8714 | 2 |
| 0.8866 | 1 |
| 0.8876 | 1 |
| 0.9024 | 2 |
| 0.9338 | 2 |
| 0.9352 | 1 |
| 0.942 | 1 |
| 0.9716 | 1 |
| 0.977 | 1 |
| 0.9816 | 1 |
| 0.9943 | 1 |
| 0.996 | 1 |
| 0.9962 | 2 |
| 1 | 322 |

## Disposition

The routed power nets match the reviewed current-route widening envelope: 779 power segments present, 439 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
