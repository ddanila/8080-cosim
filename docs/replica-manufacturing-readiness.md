# Replica manufacturing readiness

Status: **DESIGN HOLD / PACKAGE VERIFIED**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Final upload ZIP SHA256: `dec4424f17b16c36f3ccb09c1697b4cf2d665ff456ddbf36619025a3898409fd`

This is the tracked top-level manufacturing packet for the replica main
board. It separates reproducible package integrity from functional design
release. A verified package must not be uploaded while the status is
DESIGN HOLD.

## Gate Summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5269 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2873 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2638 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 13845 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8548 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2957 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |

## Toolchain Provenance

| Tool | Version / command |
| --- | --- |
| KiCad CLI | /usr/bin/kicad-cli-nightly |
| KiCad CLI version | 10.99.0 |
| Gerber job generator | KiCad Pcbnew 10.99.0-unknown-3a2065e8de~189~ubuntu26.04.1 |
| External viewer | @tracespace/cli |

## Final Upload Directory

| File | Bytes | SHA256 | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `31cdbda6f277b181dc3466d9516da8a6913bf63df9548fd6590816c650dec407` | PASS |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 787459 | `dec4424f17b16c36f3ccb09c1697b4cf2d665ff456ddbf36619025a3898409fd` | PASS |

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

## Required release/pre-payment command

```sh
kicad/check_replica_manufacturing_ready.sh
```

## External evidence to save after design release

Use `docs/replica-order-evidence-template.md` for the private order record.

- Vendor preview screenshots.
- Quoted fabrication options and price.
- Vendor order number.
- The final upload ZIP checksum above.
- Confirmation that `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`.
- Confirmation that the package was regenerated after the final D2/D94
  changes, placement-only functional IC dispositions, and source-risk
  net corrections.
