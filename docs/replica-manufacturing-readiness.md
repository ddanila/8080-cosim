# Replica manufacturing readiness

Status: **DESIGN HOLD / PACKAGE REGENERATION REQUIRED**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Final upload ZIP SHA256: `-`
Routed PCB SHA256: `f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a`
Fabrication source stamp: `-`

This packet checks package integrity and reads design-release report markers.
Only RELEASED FOR UPLOAD authorizes the next upload step. Report markers
do not substitute for current physical and functional evidence.

The current routed board is
`f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a`.
The upload ZIP is absent in this checkout.
This command reruns order/package checks and refreshes the order template;
it does not export Gerbers or correct the board. Refresh with
`python3 kicad/report_replica_manufacturing_readiness.py`.

## Physical release evidence

- [Source/routed comparison](routed-refresh-audit.md): pad, net, and placement differences.
- [PPI orientation](ppi-orientation-audit.md) and [pin mapping](ppi-physical-pin-mapping.json): D26/D27 physical mapping.
- [X8 footprints](x8-electrolytic-footprint-audit.md): C31–C33 axial lead geometry.
- [Photo registration](photo-registration.md): timer placement and mounting-hole geometry.
- [Factory wire fidelity](factory-wire-route-fidelity.md): insulated links and landing evidence.

## Historical package provenance

The superseded package used routed-board SHA256
`3a1f83c8277624f2c04633761de5703550420443839fb3d5e49eea2c8a99e266`.
Historical upload ZIP SHA256: `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`.
Its identity, toolchain, and audit counts are preserved in
[the historical package record](../ref/routing/zero-open-fabrication-package.json).
Those results do not authorize the current board or package.

## Gate Summary

Rows check report presence and configured markers; PASS does not mean
this generator reran every underlying design check.

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Main-board ERC/parity | `docs/main-board-erc-parity.md` | 3504 | HOLD |
| PPI orientation | `docs/ppi-orientation-audit.md` | 3863 | HOLD |
| X8 electrolytic footprints | `docs/x8-electrolytic-footprint-audit.md` | 2709 | HOLD |
| Order readiness | `fab/gerbers/order-readiness.md` | 3406 | HOLD |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5829 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 583 | FAIL |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3564 | FAIL |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 1396 | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 20412 | HOLD |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 13453 | HOLD |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | 16311 | HOLD |
| Order evidence template | `docs/replica-order-evidence-template.md` | 4549 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 3259 | FAIL |
| Review waiver | `fab/gerbers/review-waivers.md` | 1967 | FAIL |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 2255 | FAIL |

## Toolchain Provenance

| Tool | Version / command |
| --- | --- |
| KiCad CLI | /usr/bin/kicad-cli |
| KiCad CLI version | 10.0.6 |
| Gerber job generator | - |
| External viewer | @tracespace/cli |
| Upload ZIP format | timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644` |

## Final Upload Directory

| File | Bytes | SHA256 | Status |
| --- | ---: | --- | --- |

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
Use `docs/replica-first-article-record.md` for each received and assembled
physical unit; package verification and vendor evidence do not substitute for
as-built identity or acceptance testing.

- Vendor preview screenshots.
- Quoted fabrication options and price.
- Vendor order number.
- The final upload ZIP checksum above.
- Confirmation that `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`.
- Confirmation that the package was regenerated after the final D2/D94
  changes, FDC-support functional pin dispositions, and source-risk
  net corrections.

## Failures

- fabrication source-board.sha256 is absent or differs from the current routed PCB
- required report marker missing in docs/replica-order-upload-runbook.md: Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**
- required report marker missing in docs/replica-package-geometry-readiness.md: Status: **READY**
- required report marker missing in docs/replica-fab-drc-disposition.md: Status: **READY**
- required report marker missing in docs/replica-power-trace-readiness.md: Status: **READY**
- required report marker missing in fab/gerbers/external-gerber-review.md: Status: **READY**
- required report marker missing in fab/gerbers/review-waivers.md: Status: **ACCEPTED**
- required report marker missing in fab/gerbers/fab-readiness.md: Fabrication-file inventory gate: **PASS**
- upload directory contains unexpected file set: (empty)
- upload SHA256SUMS.txt does not match the final upload ZIP
- root SHA256SUMS missing upload member(s): juku_routed-F_Cu.gtl, juku_routed-B_Cu.gbl, juku_routed-F_Mask.gts, juku_routed-B_Mask.gbs, juku_routed-F_Silkscreen.gto, juku_routed-B_Silkscreen.gbo, juku_routed-Edge_Cuts.gm1, juku_routed-job.gbrjob, juku_routed.drl
- missing toolchain provenance: Gerber job generator
