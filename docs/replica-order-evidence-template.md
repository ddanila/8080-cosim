# Replica order evidence template

Copy this checklist into the private order record when the replica main-board
fabrication order is placed. Do not fill it in ahead of the vendor UI; live DFM,
price, and order-number evidence only exists after upload/quotation.

## Pre-Payment Gate

```sh
kicad/check_replica_manufacturing_ready.sh
```

Expected result: `replica manufacturing readiness: READY TO UPLOAD`.

## Upload Artifact

| Field | Value |
| --- | --- |
| Upload ZIP | `fab/gerbers/upload/juku-replica-gerbers-drill.zip` |
| Upload ZIP SHA256 | `0f52569a63601573c300ef099561f93bda1845cf51985a530b9e46863232a211` |
| Upload checksum command | `(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)` |

## Vendor Options To Record

| Field | Recorded value |
| --- | --- |
| Vendor |  |
| Order/project number |  |
| Quote timestamp and currency |  |
| Quantity |  |
| Layers | 2 |
| Material/thickness | FR-4, 1.6 mm |
| Board size shown by vendor |  |
| Drill files accepted |  |
| Soldermask color |  |
| Silkscreen color |  |
| Surface finish |  |
| Copper weight |  |
| Electrical test option |  |
| Impedance/stackup option | none / not requested |
| Notes sent to vendor |  |

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
- [ ] Vendor did not enable impedance control or change the 2-layer stackup.
- [ ] Final quoted options match the locked options in `docs/replica-manufacturing-readiness.md`.
- [ ] Upload ZIP SHA256 above is saved with the order.
