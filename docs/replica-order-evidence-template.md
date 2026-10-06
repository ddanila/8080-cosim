# Replica order evidence template

Status: **TEMPLATE INVALID**

The [superseded package record](../ref/routing/zero-open-fabrication-package.json)
preserves the historical ZIP identity. Record the newly verified upload hash below.

This is a future private order-record template. Do not upload the current
package or start an order until the manufacturing gate says RELEASED FOR UPLOAD.
Live DFM, price, and order-number evidence only exists after a released
design is uploaded and quoted.
Refresh from the repository root with Python 3 (standard library only):
`python3 kicad/report_replica_order_evidence_template.py`.
The generator overwrites this template and returns exit status 3 when
its artifact or evidence checks fail. Copy it to a private order record
before filling in vendor details; regeneration does not preserve entries.

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

| Purpose | File | Status |
| --- | --- | --- |
| Upload runbook | `docs/replica-order-upload-runbook.md` | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | FAIL |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | PASS |

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
- [ ] Confirmed the release criteria in `PLAN.md` are satisfied and the design-release report explicitly authorizes fabrication.
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
