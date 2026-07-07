# VJUGA Rev A manufacturing readiness

Status: **READY TO UPLOAD**
Fabrication package: `fab/minimal-vga`
Final upload ZIP: `fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`
Final upload ZIP SHA256: `6fbb59ff5afc1c82aad08dd874c4ef77a3cbb802212d1cc5920d2bc032c58966`

This is the tracked top-level manufacturing packet for the VJUGA Rev A first
sample. It proves the generated fabrication package is internally coherent and
ready for vendor upload as a **bare PCB only** order. It does not claim that a
vendor order has already been placed or accepted.

## Gate Summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Bare-PCB order readiness | `fab/minimal-vga/order-readiness.md` | 6715 | PASS |
| Bare-PCB upload runbook | `fab/minimal-vga/order-upload-runbook.md` | 3817 | PASS |
| Fabrication readiness | `fab/minimal-vga/fab-readiness.md` | 385 | PASS |
| Fabrication package integrity | `fab/minimal-vga/fab-package-integrity.md` | 2425 | PASS |
| External Gerber review | `fab/minimal-vga/external-gerber-review.md` | 2291 | PASS |
| Routing/plane disposition | `fab/minimal-vga/routing-disposition-readiness.md` | 1342 | PASS |
| Bare-PCB order note | `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md` | 1624 | PASS |
| Order evidence template | `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order-evidence-template.md` | 3160 | PASS |

## Final Upload Directory

| File | Bytes | SHA256 | Status |
| --- | ---: | --- | --- |
| `fab/minimal-vga/upload/SHA256SUMS.txt` | 714 | `9cda63e83af2eeadd99373ffce6db88eebbc019df8cc4e84b34ed2d73c401b4e` | PASS |
| `fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip` | 134872 | `6fbb59ff5afc1c82aad08dd874c4ef77a3cbb802212d1cc5920d2bc032c58966` | PASS |

## Locked Vendor Options

| Option | Value |
| --- | --- |
| Service | PCB fabrication only; no factory assembly and no components |
| Layers | 4 |
| Material/thickness | FR-4, vendor default unless changed deliberately |
| Drill file | one mixed-plating Excellon drill file |
| Assembly | disabled |
| BOM/CPL upload | do not upload for this first sample |
| Impedance/stackup | do not request impedance control or stackup changes |
| Routing disposition | Rev A no-plane layout with 0.20 mm VCC/GND/VCC_RAW routing accepted for this low-current prototype |

## Required Pre-Payment Commands

```sh
spinoffs/minimal-vga/sim/check.sh
(cd fab/minimal-vga && sha256sum -c upload/SHA256SUMS.txt)
```

## Remaining External Evidence To Save With The Order

Use `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order-evidence-template.md` for
the private order record.

- Vendor preview screenshots.
- Quoted fabrication options and price.
- Vendor order number.
- The final upload ZIP checksum above.
- Confirmation that assembly was disabled and no BOM/CPL was uploaded.
