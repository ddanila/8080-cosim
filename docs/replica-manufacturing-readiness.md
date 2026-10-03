# Replica manufacturing readiness

Status: **DESIGN HOLD / PACKAGE REGENERATION REQUIRED**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Historical upload ZIP SHA256: `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`

## Current release boundary

The current routed board is
`f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a`.
The ignored `fab/gerbers` tree is incomplete and its upload ZIP is absent in
this checkout. No package is authorized for upload or order.

Current evidence and remaining holds belong to these reports:

- [Source/routed comparison](routed-refresh-audit.md): pad identity, net and
  placement differences that must be reconciled before routing release.
- [Factory wire fidelity](factory-wire-route-fidelity.md): explicit insulated
  links, landing evidence and fresh routed-board DRC. Its current audit records
  59 unconnected items; the older package DRC below is a separate snapshot.
- [PPI orientation](ppi-orientation-audit.md) and
  [physical pin mapping](ppi-physical-pin-mapping.json): D26/D27 footprint
  orientation and physical pin-to-net mapping remain held.
- [X8 electrolytic footprints](x8-electrolytic-footprint-audit.md): C31–C33
  axial lead geometry must replace the present radial footprints.
- [Photo registration](photo-registration.md): timer-cluster placement and the
  missing lower-right mounting hole need dimensioned physical fits.
- [Release evidence](replica-release-evidence-package.md): consolidated electrical,
  sourcing, fabrication and as-built acceptance gates.

After design corrections, regenerate and review the package. Its
`fab/gerbers/source-board.sha256` must match the exact routed PCB. Package
geometry checks cover outline, layers and drill export; they do not prove
physical IC orientation, pin mapping or functional design readiness.

## Historical package scope

The tables below preserve the previously verified package for routed-board
SHA256 `3a1f83c8277624f2c04633761de5703550420443839fb3d5e49eea2c8a99e266`.
Its canonical identity and audit counts are in
[the historical package record](../ref/routing/zero-open-fabrication-package.json).
Every PASS, byte count and tool version below describes that package snapshot,
not current files or upload approval. The former ZIP must not be uploaded while
the design is held or its board identity differs from the released board.

## Historical gate summary

| Gate | Evidence | Bytes | Status |
| --- | --- | ---: | --- |
| Main-board ERC/parity | `docs/main-board-erc-parity.md` | 2172 | HOLD |
| PPI orientation | `docs/ppi-orientation-audit.md` | 6899 | HOLD |
| X8 electrolytic footprints | `docs/x8-electrolytic-footprint-audit.md` | 2921 | HOLD |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | HOLD |
| Upload runbook | `docs/replica-order-upload-runbook.md` | 5364 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1385 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2959 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2147 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 15741 | HOLD |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9149 | HOLD |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | 12334 | HOLD |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2957 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2126 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1901 | PASS |

## Historical toolchain provenance

| Tool | Version / command |
| --- | --- |
| KiCad CLI | /usr/bin/kicad-cli-nightly |
| KiCad CLI version | 10.99.0 |
| Gerber job generator | KiCad Pcbnew 10.99.0-unknown-3a2065e8de~189~ubuntu26.04.1 |
| External viewer | @tracespace/cli |
| Upload ZIP format | timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644` |

## Historical upload directory

| File | Bytes | SHA256 | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `d29095f3749caf764ec9cc93a0df1f01d2bf695b242eca0f62293cf5bcc1bfd8` | PASS |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4905767 | `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46` | PASS |

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
- The checksum of the newly released upload ZIP, not the historical checksum above.
- Confirmation that `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`.
- Confirmation that the package matches the final released board and all
  electrical, physical-layout and construction holds are closed.
