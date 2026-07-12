# Replica manufacturing readiness

Status: **PACKAGE INVALID**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Final upload ZIP SHA256: `341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4`

This is the tracked top-level manufacturing packet for the replica main
board. It separates reproducible package integrity from functional design
release. A verified package must not be uploaded while the status is
DESIGN HOLD.

## Gate Summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Main-board ERC/parity | `docs/main-board-erc-parity.md` | 1194 | PASS |
| Order readiness | `fab/gerbers/order-readiness.md` | 2879 | PASS |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5516 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3028 | FAIL |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2468 | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 73540 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8586 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 3165 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1747 | FAIL |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1772 | PASS |

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
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `0f0de6fafc8dea26732383e729a733c0ac8350ccb91b56439bacbc9264eeba4e` | PASS |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 790180 | `341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4` | PASS |

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

## Failures

- required report marker missing in docs/replica-order-upload-runbook.md: Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**
- required report marker missing in docs/replica-fab-drc-disposition.md: Status: **READY**
- required report marker missing in docs/replica-power-trace-readiness.md: Status: **READY**
- required report marker missing in fab/gerbers/review-waivers.md: Status: **ACCEPTED**
