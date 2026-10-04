# Main board order readiness

Board: `kicad/juku_routed.kicad_pcb`
Fabrication package: `fab/gerbers`
Status: **NOT READY**

This gate separates machine-checkable fabrication blockers from dense
placement and silkscreen findings that require human visual review or
explicit waiver before placing an order.
Run `python3 kicad/report_order_readiness.py` to refresh this report.
The command reruns DRC and the package checks; it does not export the PCB.

## Machine Blockers

| Type | Count |
| --- | ---: |
| clearance | 0 |
| copper_edge_clearance | 0 |
| lib_footprint_issues | 0 |
| shorting_items | 0 |
| unconnected_items | 59 |

## Unknown DRC Types

- `track_dangling`: 24
- `via_dangling`: 1

## Review-Only DRC Types

| Type | Count |
| --- | ---: |
| courtyards_overlap | 108 |
| pth_inside_courtyard | 68 |
| silk_over_copper | 199 |
| silk_overlap | 199 |
| text_thickness | 199 |

## Waiver Gate

- Review-only waiver status: **NOT ACCEPTED**
- Waiver report: `fab/gerbers/review-waivers.md`

## External Gerber Review Gate

- Independent render status: **NOT READY**
- Report: `fab/gerbers/external-gerber-review.md`

## Parts / Sourcing Gate

- Dual-config BOM status: **GENERATED**
- Report: `docs/replica-dual-config-bom.md`
- CSV: `docs/replica-dual-config-bom.csv`
- Sourcing readiness status: **NOT READY**
- Sourcing report: `docs/replica-sourcing-readiness.md`
- BOM lines: 122
- Board component positions: 377
- Current .009 populated parts: 273
- Empty expansion/authentic-completeness sockets: 104
- Action classes: circuit-review, leave-empty, mechanical-review, program/dump, source-now

## Design Release Gate

Package integrity and DRC are necessary but do not authorize fabrication.
The following evidence files must contain their configured release-status
markers. This command reads those reports; it does not rerun their
functional or physical verification. Confirm their evidence is current
before relying on a passing marker.

| Check | Evidence | Result |
| --- | --- | --- |
| Main-board ERC, parity, and endpoint ownership | `docs/main-board-erc-parity.md` | HOLD |
| D2 bus/wait PROM wiring and contents | `docs/d2-reconstruction-constraints.md` | HOLD |
| D94 FDC-control PROM wiring, strobe feasibility, and contents | `docs/d94-reconstruction-constraints.md` | HOLD |
| All FDC-support functional pin dispositions | `docs/unmodeled-footprint-inventory.md` | HOLD |
| Residual source-risk net dispositions | `docs/replica-bringup-verification-points.md` | HOLD |
| Complete functional sourcing/programming decision | `docs/replica-sourcing-readiness.md` | HOLD |
| Factory insulated-wire construction fidelity | `docs/factory-wire-route-fidelity.md` | HOLD |

## Power Trace Gate

- Power trace status: **NOT READY**
- Report: `docs/replica-power-trace-readiness.md`

## DRC Visual Disposition Gate

- DRC disposition status: **NOT READY**
- Report: `docs/replica-fab-drc-disposition.md`

## Package Geometry Gate

- Package geometry status: **NOT READY**
- Report: `docs/replica-package-geometry-readiness.md`

## Order Upload Runbook Gate

- Upload runbook status: **NOT READY**
- Report: `docs/replica-order-upload-runbook.md`
- Upload archive: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`

## Disposition

Do not order. Resolve or deliberately reclassify the machine blockers and unknown DRC classes, then pass every package and design-release gate above.
