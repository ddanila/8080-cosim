# Replica order evidence template

Status: **TEMPLATE INVALID**

This is a future private order-record template. Do not upload the current
package or start an order while the design-release report says DESIGN HOLD.
Live DFM, price, and order-number evidence only exists after a released
design is uploaded and quoted.

## Pre-Payment Gate

```sh
kicad/check_replica_manufacturing_ready.sh
```

Required release result: `replica manufacturing readiness: RELEASED FOR UPLOAD`.

## Upload Artifact

| Field | Value |
| --- | --- |
| Upload ZIP | `fab/gerbers/upload/juku-replica-gerbers-drill.zip` |
| Upload ZIP SHA256 | `7df2a6e2927c62313275f3f5713e2b4cf3622c3c782b795cf41b27c8f3bfff46` |
| Upload checksum command | `(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)` |

## Required Source Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5423 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3199 | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 30221 | PASS |

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

## Failures

- evidence marker missing in docs/replica-order-upload-runbook.md: Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**
- evidence marker missing in docs/replica-fab-drc-disposition.md: Status: **READY**
