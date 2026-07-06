# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **READY**

This report records the routed main-board power traces after
`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the
authentic 2-layer board: the freerouted 0.20 mm baseline remains where
clearance constrained widening, while all geometry is still checked by
the KiCad DRC gate in `kicad/report_order_readiness.py`.

## Summary

- Routed power segments: 704
- Widened power segments (`>0.20 mm`): 377
- Total routed power length: 4842.582 mm
- Widened routed power length: 1876.340 mm
- Width clamp: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 323 | 158 | 0.200 | 1.000 | 1840.165 | 718.966 | B.Cu, F.Cu |
| P5V | 282 | 185 | 0.200 | 1.000 | 1947.702 | 941.388 | B.Cu, F.Cu |
| P12V | 54 | 19 | 0.200 | 1.000 | 466.127 | 144.254 | B.Cu, F.Cu |
| M12V | 33 | 10 | 0.200 | 1.000 | 507.136 | 45.610 | B.Cu, F.Cu |
| M5V_DERIVED | 12 | 5 | 0.200 | 1.000 | 81.452 | 26.122 | B.Cu, F.Cu |

## Width Histogram

| Width mm | Segments |
| ---: | ---: |
| 0.2 | 327 |
| 0.3099 | 1 |
| 0.3311 | 3 |
| 0.3335 | 1 |
| 0.3502 | 1 |
| 0.3584 | 1 |
| 0.3768 | 1 |
| 0.3984 | 2 |
| 0.4013 | 1 |
| 0.4142 | 1 |
| 0.4382 | 1 |
| 0.4447 | 1 |
| 0.4513 | 1 |
| 0.473 | 2 |
| 0.4832 | 1 |
| 0.4966 | 1 |
| 0.5034 | 2 |
| 0.508 | 1 |
| 0.5142 | 1 |
| 0.5865 | 1 |
| 0.5942 | 1 |
| 0.6111 | 1 |
| 0.6207 | 1 |
| 0.6212 | 1 |
| 0.6214 | 1 |
| 0.6234 | 2 |
| 0.6256 | 1 |
| 0.6402 | 1 |
| 0.6417 | 1 |
| 0.6464 | 1 |
| 0.6679 | 1 |
| 0.6688 | 1 |
| 0.6834 | 1 |
| 0.6848 | 1 |
| 0.6854 | 2 |
| 0.686 | 3 |
| 0.6878 | 2 |
| 0.693 | 1 |
| 0.7074 | 1 |
| 0.7082 | 2 |
| 0.7249 | 1 |
| 0.7358 | 1 |
| 0.7396 | 2 |
| 0.7528 | 4 |
| 0.7597 | 2 |
| 0.7598 | 1 |
| 0.7627 | 1 |
| 0.7749 | 1 |
| 0.7828 | 1 |
| 0.7916 | 1 |
| 0.8094 | 30 |
| 0.8139 | 1 |
| 0.8146 | 1 |
| 0.8165 | 1 |
| 0.8167 | 1 |
| 0.8174 | 1 |
| 0.8194 | 1 |
| 0.8211 | 3 |
| 0.8225 | 1 |
| 0.8238 | 1 |
| 0.8249 | 1 |
| 0.8264 | 1 |
| 0.8271 | 1 |
| 0.8273 | 2 |
| 0.8287 | 1 |
| 0.8316 | 1 |
| 0.8318 | 1 |
| 0.8319 | 1 |
| 0.8326 | 1 |
| 0.8343 | 1 |
| 0.8357 | 2 |
| 0.8364 | 1 |
| 0.8365 | 1 |
| 0.8373 | 1 |
| 0.8393 | 2 |
| 0.8396 | 2 |
| 0.8405 | 1 |
| 0.8713 | 1 |
| 0.8752 | 1 |
| 0.8806 | 1 |
| 0.8832 | 1 |
| 0.8834 | 1 |
| 0.8868 | 2 |
| 0.9375 | 1 |
| 0.9678 | 2 |
| 0.9856 | 1 |
| 1 | 239 |

## Disposition

The routed power nets match the reviewed v76 widening envelope: 704 power segments present, 377 widened where local clearance allowed, no power segment below the routed baseline, and no widened segment above the 1.00 mm clamp. KiCad DRC remains the clearance authority.
