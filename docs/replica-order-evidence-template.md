# Replica order evidence template

Status: **TEMPLATE INVALID**

Historical superseded fabrication ZIP SHA256: `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`.
This is provenance for the older package; current release requires fresh package verification.

This is a future private order-record template. Do not upload the current
package or start an order until the manufacturing gate says RELEASED FOR UPLOAD.
Live DFM, price, and order-number evidence only exists after a released
design is uploaded and quoted.
Refresh with `python3 kicad/report_replica_order_evidence_template.py`.

## Pre-Payment Gate

```sh
kicad/check_replica_manufacturing_ready.sh
```

Required release result: `replica manufacturing readiness: RELEASED FOR UPLOAD`.

## Upload Artifact

| Field | Value |
| --- | --- |
| Upload ZIP | `fab/gerbers/upload/juku-replica-gerbers-drill.zip` |
| Upload ZIP SHA256 | - |
| Upload checksum command | `(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)` |

## Required Source Evidence

PASS means a nonempty report contains an accepted status marker; it does
not mean this generator reran its checks or closed its design risks.

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5829 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 583 | FAIL |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3564 | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 20762 | FAIL |

## Vendor Options To Record

| Field | Recorded value |
| --- | --- |
| Vendor | - |
| Order/project number | - |
| Quote timestamp and currency | - |
| Quantity | - |
| Layers | 2 |
| Material/thickness | FR-4, 1.6 mm |
| Board size shown by vendor | - |
| Drill files accepted | - |
| Soldermask color | - |
| Silkscreen color | - |
| Surface finish | - |
| Copper weight | - |
| Electrical test option | - |
| Impedance/stackup option | none / not requested |
| Notes sent to vendor | - |

## Screenshot Evidence To Save

- Upload file list showing `juku-replica-gerbers-drill.zip`.
- Vendor top copper preview.
- Vendor bottom copper preview.
- Vendor top soldermask/silkscreen preview.
- Vendor bottom soldermask/silkscreen preview.
- Vendor board-outline/drill preview showing the 310 mm x 266 mm class outline.
- Quoted fabrication options and price.
- Final order confirmation page with order number.

## Review Before Payment

- [ ] Re-ran the pre-payment gate above after the vendor ZIP upload was selected.
- [ ] Vendor preview agrees with `docs/replica-package-geometry-readiness.md`.
- [ ] Top/bottom orientation agrees with `fab/gerbers/review/tracespace/`.
- [ ] Accepted DRC classes in `docs/replica-fab-drc-disposition.md` remain acceptable in the vendor preview.
- [ ] Confirmed every P0 item in `PLAN.md` is closed and the design-release report explicitly authorizes fabrication.
- [ ] Reviewed and dispositioned every relevant source-risk row in `docs/replica-bringup-verification-points.md`.
- [ ] Vendor did not enable impedance control or change the 2-layer stackup.
- [ ] Final quoted options match the locked options in `docs/replica-manufacturing-readiness.md`.
- [ ] Upload ZIP SHA256 above is saved with the order.

## Receipt and first-article handoff

- [ ] Record received quantity, lot/order identity, visible damage, finish, outline, drill, and connector-orientation inspection.
- [ ] Assign a unit serial/label before assembly or rework.
- [ ] Start a per-unit `docs/replica-first-article-record.md` copy and enter the released commit, PCB/package/BOM hashes, programmed-image hashes, jumper settings, and every approved deviation.
- [ ] Do not copy the first unit's acceptance result to later units; each unit receives its own manufacturing/workmanship acceptance record.

## Failures

- missing or empty upload ZIP: fab/gerbers/upload/juku-replica-gerbers-drill.zip
- missing or empty upload checksum file: fab/gerbers/upload/SHA256SUMS.txt
- evidence marker missing in docs/replica-order-upload-runbook.md: Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**
- evidence marker missing in docs/replica-package-geometry-readiness.md: Status: **READY**
- evidence marker missing in docs/replica-fab-drc-disposition.md: Status: **READY**
- evidence marker missing in docs/replica-bringup-verification-points.md: Status: **ENDPOINT COVERAGE FAILED** or Status: **EVIDENCE INDEX READY / RISKS UNRESOLVED** or Status: **DESIGN RELEASE RISKS CLOSED**
