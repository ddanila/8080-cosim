# Replica manufacturing readiness

Status: **READY TO UPLOAD**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Final upload ZIP SHA256: `0f52569a63601573c300ef099561f93bda1845cf51985a530b9e46863232a211`

This is the tracked top-level manufacturing packet for the replica main
board. It proves the generated fabrication package is internally coherent
and ready for vendor upload; it does not claim that a vendor order has
already been placed or accepted.

## Gate Summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2253 | PASS |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 4755 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2912 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2788 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 7972 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1629 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1905 | PASS |

## Toolchain Provenance

| Tool | Version / command |
| --- | --- |
| KiCad CLI | /usr/bin/kicad-cli-nightly |
| KiCad CLI version | 10.99.0 |
| Gerber job generator | KiCad Pcbnew 10.99.0-unknown-3a2065e8de~189~ubuntu26.04.1 |
| External viewer | @tracespace/cli |

## Locked Vendor Options

| Option | Value |
| --- | --- |
| Service | PCB fabrication only; no factory assembly package for the replica main board |
| Layers | 2 |
| Material/thickness | FR-4, 1.6 mm |
| Board outline | 310 mm x 266 mm Edge.Cuts coordinate box |
| Rendered job size | 310.15 mm x 266.15 mm profile-aperture envelope |
| Drill file | one mixed-plating Excellon drill file |
| Impedance/stackup | do not request impedance control or stackup changes |

## Required Pre-Payment Commands

```sh
python3 kicad/report_order_readiness.py
(cd fab/gerbers && sha256sum -c SHA256SUMS)
(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)
```

## Remaining External Evidence To Save With The Order

- Vendor preview screenshots.
- Quoted fabrication options and price.
- Vendor order number.
- The final upload ZIP checksum above.
