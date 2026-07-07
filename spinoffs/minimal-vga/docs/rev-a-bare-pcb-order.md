# VJUGA Rev A bare-PCB order

Status: **READY FOR VENDOR PREVIEW**

Rev A's first physical sample is a PCB-only order. Do not enable factory
assembly for this order; components, sockets, headers, and manual rows remain
deferred until the bare board has been inspected and the concept is accepted.

## Upload File

Upload only:

```text
fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip
```

Current local package evidence:

- Gerber/drill ZIP SHA256:
  `6fbb59ff5afc1c82aad08dd874c4ef77a3cbb802212d1cc5920d2bc032c58966`
- Integrity command:

```sh
(cd fab/minimal-vga && sha256sum -c upload/SHA256SUMS.txt)
```

The generated `fab/minimal-vga/order-upload-runbook.md` is the order-time
runbook. It marks the retained BOM/CPL files as reference-only for a later
assembled-board path.

## Vendor UI Checks

- Select PCB fabrication only / no assembly.
- Confirm 4-layer stackup, board outline, drill hits, and top/bottom orientation
  in the vendor Gerber preview.
- Confirm the Rev A no-plane and 0.20 mm VCC/GND/VCC_RAW routing disposition is
  still intentional for this low-current prototype.
- Save vendor preview screenshots, stackup/settings, price, and order number
  with the order record.

## Deferred

- `upload/vjuga-rev-a-jlcpcb-bom.csv`
- `upload/vjuga-rev-a-jlcpcb-cpl.csv`
- Manual-install rows `D1/J30/R6/R15/U50/U51`
- Socketed IC insertion list

These are preserved as references for a later assembled-board order, not for the
bare-PCB first sample.
