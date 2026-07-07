# VJUGA Rev A bare-PCB order evidence template

Status: **READY**

Copy this checklist into the private order record when the VJUGA Rev A
bare-PCB fabrication order is placed. Do not fill it in ahead of the vendor UI;
live DFM, preview, price, and order-number evidence only exists after upload.

## Pre-Payment Gate

```sh
spinoffs/minimal-vga/sim/check.sh
(cd fab/minimal-vga && sha256sum -c upload/SHA256SUMS.txt)
```

Expected results:

- `BOOT-CHECK: PASS (merge intact)`
- `Rev A PCB scaffold check: PASS`
- `Status: **READY**` in `fab/minimal-vga/fab-readiness.md`
- All upload checksums report `OK`

## Upload Artifact

| Field | Value |
| --- | --- |
| Upload ZIP | `fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip` |
| Upload ZIP SHA256 | `6fbb59ff5afc1c82aad08dd874c4ef77a3cbb802212d1cc5920d2bc032c58966` |
| Upload checksum command | `(cd fab/minimal-vga && sha256sum -c upload/SHA256SUMS.txt)` |
| Order mode | PCB fabrication only / no assembly |

## Source Evidence

| Purpose | File | Required status |
| --- | --- | --- |
| Bare-PCB order note | `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md` | `READY FOR VENDOR PREVIEW` |
| Generated order readiness | `fab/minimal-vga/order-readiness.md` | `BARE PCB READY - VENDOR PREVIEW REQUIRED` |
| Generated upload runbook | `fab/minimal-vga/order-upload-runbook.md` | `READY` |
| Fabrication readiness | `fab/minimal-vga/fab-readiness.md` | `READY` |
| External Gerber review | `fab/minimal-vga/external-gerber-review.md` | `READY` |

## Vendor Options To Record

| Field | Recorded value |
| --- | --- |
| Vendor | - |
| Order/project number | - |
| Quote timestamp and currency | - |
| Quantity | - |
| Layers | 4 |
| Material/thickness | FR-4, vendor default unless changed deliberately |
| Board size shown by vendor | - |
| Drill files accepted | - |
| Soldermask color | - |
| Silkscreen color | - |
| Surface finish | - |
| Copper weight | - |
| Electrical test option | - |
| Impedance/stackup option | none / not requested |
| Assembly enabled | no |
| BOM/CPL uploaded | no |
| Notes sent to vendor | - |

## Screenshot Evidence To Save

- Upload file list showing only `vjuga-rev-a-gerbers-drill.zip` for the order.
- Vendor top copper preview.
- Vendor bottom copper preview.
- Vendor inner layer previews.
- Vendor top soldermask/silkscreen preview.
- Vendor bottom soldermask/silkscreen preview.
- Vendor board-outline/drill preview.
- Quoted fabrication options and price.
- Final order confirmation page with order number.

## Review Before Payment

- [ ] Re-ran the pre-payment gate above after regenerating/selecting the upload ZIP.
- [ ] Vendor UI is set to PCB fabrication only / no assembly.
- [ ] No BOM or CPL file is uploaded for this first sample.
- [ ] Vendor preview agrees with the Tracespace review under `fab/minimal-vga/review/tracespace/`.
- [ ] Vendor preview shows the expected 4-layer stackup.
- [ ] Board outline and drill hits look correct in the vendor preview.
- [ ] Top/bottom orientation is correct.
- [ ] The Rev A no-plane and 0.20 mm VCC/GND/VCC_RAW routing disposition remains intentional.
- [ ] Upload ZIP SHA256 above is saved with the order.
