# Replica manufacturing readiness

Status: **DESIGN HOLD / PACKAGE REGENERATION REQUIRED**
Fabrication package: `fab/gerbers`
Final upload ZIP: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Historical upload ZIP SHA256: `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`

The tables below record a verified package for routed-board SHA256
`3a1f83c8277624f2c04633761de5703550420443839fb3d5e49eea2c8a99e266`.
The current routed board is
`40ecf0550c44bb205ebb8cfb547d34613b698dc6ba14323a5560348ccfc42c3c`
after the unsupported physical X7 footprint and route removal, the accepted D57.18 correction, the D104.7/R30 source-ground assignment, and the subsequent exact-sheet C99.2
ground-net, CS7/D9.7, D96.13/D99.10, D99.11/MOTOR EN, and selected
E12/D99.2 HLD, D100.9/D99.12 OE_N, D99 Q2 motor-pulse, D26.38/D101.1 IMDRG, D101 section-A input-junction, D96.9-to-D101 input, and D96.11-to-D94.2 clock corrections, followed by the photographed D34.4/D38.4 timing-tag-2 net merge.
Before the X6 A:3 correction, the routed PCB had thirteen unconnected items: C99.2 to GND, D9.7
to the D94.15/D93.3 `FDC_CS_N` copper, D96.13 to D99.10, D26.16 to
D99.11 `FDC_MOTOR_EN`, D99.2 to D93.28/D100.3 HLD copper, D99.5 to
D100.7 A7, D99.12 to D100.9 OE_N, D26.38 to D101.1 IMDRG, and D101
pins 3, 5, and 6 plus D96.9 to the D101.4/R92/R99 copper, and D96.11 to
the D94.2/D99.9/R89.1 copper. The later X6 A:3/VD3 retraction and surface-pad relocation left 16 unconnected items. The subsequent exact sheet-2 R38/D35 correction removed 108 wrong-net copper items and reassigned seven pads, leaving the routed PCB with 23 unconnected items. The later D104.7→R30 lower photo join and source-ground assignment changes that pad net without routing it, yielding 24 unconnected items and zero shorts, clearances, or track crossings. The later D29 exact-source pad migration removed 32 stale local copper items, leaving 35 unconnected items and still zero shorts, clearances, or track crossings. The subsequent exact R101/R104 refdes correction and D12/X1 pad assignments left 38 unconnected items. The later two-face owner-photo review moved the misplaced R18 footprint, placed R104 separately, and removed 20 obsolete copper segments. That 49-item count is historical. KiCad 10 error-only DRC on both current routed variants reports 176 violations and 54 unconnected items (2026-09-27). These branches must be routed and checked before any new package. The ignored
`fab/gerbers` tree is incomplete and its upload ZIP is absent in this checkout.
Every PASS below is historical package evidence,
not a current upload approval. Regenerate the exact package, review it, and
rerun the release gate after the remaining design changes. The export step now
stamps `fab/gerbers/source-board.sha256`; the release gate requires that stamp
to match the current routed PCB.

This is the tracked top-level manufacturing packet for the replica main
board. It separates historical package integrity from current functional
design release. The old ZIP must not be uploaded while the status is DESIGN
HOLD or its board hash differs from the current routed PCB.

Archive review has identified an additional physical-layout hold:
`docs/ppi-orientation-audit.md` records D26 and D27 PPI package orientations
in the owner photos that disagree with their current 90° routed footprints.
D26 and D27 are horizontal with right-edge notches in both factory and
owner evidence. The current 90° KiCad footprints are left-notched. The
package-geometry PASS below checks board outline,
layers, and drill export only; it does not validate IC orientation or
physical pin-to-net mapping. Release requires a local pin-center fit,
corrected PPI footprints and routing, and renewed electrical/visual review.
The current routed PCB has 40/40 net mismatches at the photographed physical
pin positions on each PPI; see `docs/ppi-physical-pin-mapping.json`.
The X8 power corner has a separate footprint hold: C31–C33 use 2 mm radial
footprints in all PCB variants, while the .009 assembly and owner photos show
axial cans with about 25–26 mm lead spacing. See
`docs/x8-electrolytic-footprint-audit.md`; register the six original joints
and replace/reroute the footprints before fabrication.
The timer cluster has a separate placement hold: owner component and solder
photos place D54's lower pin row about 23 mm above the physical bottom edge,
while the routed row is only 7.38 mm above Edge.Cuts. See
`docs/photo-registration.md`; D54/D55/D57 and adjacent D26 need a mechanical
fit before fabrication, regardless of the package-geometry PASS below.
The lower-right mounting hole seen on both July board faces and the earlier
May component photo is also absent from the routed Edge.Cuts; its approximate
photo coordinate needs a dimensioned fit before adding the drill.
The two lower holes have nearly equal visible apertures in the July
component photo (about 88 and 90 pixels), so the existing 3.5 mm drill
is a candidate for the missing hole, pending a physical diameter check.

## Gate Summary

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
- The final upload ZIP checksum above.
- Confirmation that `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`.
- Confirmation that the package was regenerated after the final D2/D94
  changes, FDC-support functional pin dispositions, and source-risk
  net corrections.
