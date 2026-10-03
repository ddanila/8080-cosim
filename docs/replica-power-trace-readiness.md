# Replica power-trace readiness

Board: `kicad/juku_routed.kicad_pcb`
Status: **NOT READY**

This report counts straight track segments on the five named power nets
and checks their widths against the configured inventory and width limits.
It excludes vias, arcs, pads, and zones; it does not check connectivity,
clearance, voltage drop, or current capacity. Run the separate
`kicad/report_order_readiness.py` gate for fabrication checks.

Refresh with `python3 kicad/report_replica_power_trace_readiness.py`.

## Summary

- Routed power segments: 2744
- Widened power segments (`>0.20 mm`): 284
- Total routed power length: 7219.757 mm
- Widened routed power length: 1208.486 mm
- Accepted width range: 0.20 mm to 1.00 mm

## Nets

| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GND | 1333 | 108 | 0.200 | 1.000 | 3041.178 | 493.041 | B.Cu, F.Cu |
| P5V | 940 | 150 | 0.200 | 1.000 | 2480.041 | 596.215 | B.Cu, F.Cu |
| P12V | 388 | 10 | 0.200 | 1.000 | 1050.510 | 29.959 | B.Cu, F.Cu |
| M12V | 62 | 10 | 0.200 | 1.000 | 560.442 | 68.298 | B.Cu, F.Cu |
| M5V_DERIVED | 21 | 6 | 0.200 | 1.000 | 87.586 | 20.973 | B.Cu, F.Cu |

## Disposition

Do not use this routed package until the failures below are resolved.

## Failures

- Expected 2738 routed power segments, found 2744.
