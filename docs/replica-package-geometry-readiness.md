# Replica package geometry readiness

Fabrication package: `fab/gerbers`
Status: **READY**

This report checks the vendor-visible geometry exported in the Gerber job,
Edge.Cuts Gerber, and Excellon drill file. It turns the order-time
preview dimensions and drill-file expectations into a reproducible local gate.

## Board Geometry

| Source | Measurement | Expected | Status |
| --- | --- | --- | --- |
| Gerber job size | 310.150 x 266.150 mm | 310.150 x 266.150 mm | PASS |
| Edge.Cuts coordinate box | 310.000 x 266.000 mm | 310.000 x 266.000 mm | PASS |
| Edge.Cuts min/max | (0.000, -266.000) .. (310.000, 0.000) | (0.000, -266.000) .. (310.000, 0.000) | PASS |
| Layer count | 2 | 2 | PASS |
| Board thickness | 1.600 mm | 1.600 mm | PASS |
| Copper files | 2 | 2 | PASS |
| Profile files | 1 | 1 | PASS |

## Drill File

| Tool | Diameter mm | Hits | Expected hits | Status |
| --- | ---: | ---: | ---: | --- |
| T1 | 0.300 | 331 | 331 | PASS |
| T2 | 0.750 | 12 | 12 | PASS |
| T3 | 0.800 | 2311 | 2311 | PASS |
| T4 | 1.000 | 30 | 30 | PASS |
| T5 | 1.300 | 5 | 5 | PASS |

## Upload Implications

- Vendor preview should show a 2-layer board.
- Vendor preview should show the 310 mm x 266 mm Edge.Cuts coordinate box; a 310.15 mm x 266.15 mm rendered job size is the 0.15 mm profile aperture envelope.
- Vendor preview should ingest one mixed-plating Excellon drill file with the five tool groups above.
