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

The upload ZIP is absent in this checkout.
This command reruns order/package checks and rewrites their reports,
the upload runbook, and the order template. It does not export Gerbers
or correct the board. Refresh with
`python3 kicad/report_replica_manufacturing_readiness.py` from the repository root.
The generator exits 3 for package failures and 0 for a valid package,
including a valid package still on DESIGN HOLD. Use the release command
below to enforce design release.

## Physical release evidence

- [Source/routed comparison](routed-refresh-audit.md): pad, net, and placement differences.
- [PPI orientation](ppi-orientation-audit.md) and [pin mapping](ppi-physical-pin-mapping.json): D26/D27 physical mapping.
- [X8 footprints](x8-electrolytic-footprint-audit.md): C31–C33 axial lead geometry.
- [Photo registration](photo-registration.md): timer placement and mounting-hole geometry.
- [Factory wire fidelity](factory-wire-route-fidelity.md): insulated links and landing evidence.

## Historical package provenance

The superseded package’s identity, toolchain, and audit counts are retained in
[the historical package record](../ref/routing/zero-open-fabrication-package.json).
Those results do not authorize the current board or package.

## Gate Summary

Rows check report presence and configured markers; PASS does not mean
this generator reran every underlying design check.

| Gate | Evidence | Status |
| --- | --- | --- |
| Main-board ERC/parity | `docs/main-board-erc-parity.md` | HOLD |
| PPI orientation | `docs/ppi-orientation-audit.md` | HOLD |
| X8 electrolytic footprints | `docs/x8-electrolytic-footprint-audit.md` | HOLD |
| Order readiness | `fab/gerbers/order-readiness.md` | HOLD |
| Upload runbook | `docs/replica-order-upload-runbook.md` | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | FAIL |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | FAIL |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | HOLD |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | HOLD |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | HOLD |
| Order evidence template | `docs/replica-order-evidence-template.md` | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | FAIL |
| Review waiver | `fab/gerbers/review-waivers.md` | FAIL |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | FAIL |

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

This command exits 3 immediately when the upload ZIP or current-board stamp
is absent. With those inputs present it refreshes selected checks and reports,
verifies package checksums, and returns 0 only for RELEASED FOR UPLOAD.

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
- Confirmation that the package was exported from the final released PCB
  and `fab/gerbers/source-board.sha256` matches that board's SHA256.

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
