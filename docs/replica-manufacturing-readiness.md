# Replica manufacturing readiness

Status: **DESIGN HOLD / PACKAGE VERIFIED**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Final upload ZIP SHA256: `09253384d703c8a200d49ee360661825a6b0c057364d5308115c9f0b6e116ca9`

This is the tracked top-level manufacturing packet for the replica main
board. It separates reproducible package integrity from functional design
release. A verified package must not be uploaded while the status is
DESIGN HOLD.

## Gate Summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Main-board ERC/parity | `docs/main-board-erc-parity.md` | 2172 | HOLD |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | HOLD |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5364 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1385 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2962 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2147 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 15976 | HOLD |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9109 | HOLD |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | 12334 | HOLD |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2957 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2126 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1901 | PASS |

## Toolchain Provenance

| Tool | Version / command |
| --- | --- |
| KiCad CLI | /usr/bin/kicad-cli-nightly |
| KiCad CLI version | 10.99.0 |
| Gerber job generator | KiCad Pcbnew 10.99.0-unknown-3a2065e8de~189~ubuntu26.04.1 |
| External viewer | @tracespace/cli |
| Upload ZIP format | timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644` |

## Final Upload Directory

| File | Bytes | SHA256 | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `fb3fb12e207f06ef246902cbf678ded57e52b4395ea703a8f55b150b17ec81ad` | PASS |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 5190681 | `09253384d703c8a200d49ee360661825a6b0c057364d5308115c9f0b6e116ca9` | PASS |

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
  changes, FDC-support functional pin dispositions, and source-risk
  net corrections.
