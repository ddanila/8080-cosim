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

The superseded package used routed-board SHA256
`3a1f83c8277624f2c04633761de5703550420443839fb3d5e49eea2c8a99e266`.
Its package identity, toolchain, drill inventory, and DRC counts are preserved in
[the historical package record](../ref/routing/zero-open-fabrication-package.json).
Those results describe that snapshot and do not authorize upload of the current
board. Use the current release-evidence index above for present gate statuses.

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
