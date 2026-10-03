# Replica order-upload runbook

Fabrication package: `fab/gerbers`
Upload archive: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Status: **PACKAGE INVALID**

Historical superseded fabrication ZIP SHA256: `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`.
This is provenance for the older package; current release requires fresh package verification.

This report verifies the mechanics of the saved upload package. It is not
an order authorization. The current design-release state is owned by
`fab/gerbers/order-readiness.md` and the top-level command below.

## Pre-Upload Integrity

Run from the repository root:

```sh
kicad/check_replica_manufacturing_ready.sh
```

## Files In Upload ZIP

| Purpose | File | Bytes | SHA256 | Status |
| --- | --- | ---: | --- | --- |
| Top copper | `juku_routed-F_Cu.gtl` | 0 | - | FAIL |
| Bottom copper | `juku_routed-B_Cu.gbl` | 0 | - | FAIL |
| Top soldermask | `juku_routed-F_Mask.gts` | 0 | - | FAIL |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 0 | - | FAIL |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 0 | - | FAIL |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 0 | - | FAIL |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 0 | - | FAIL |
| Gerber job | `juku_routed-job.gbrjob` | 0 | - | FAIL |
| Excellon drill | `juku_routed.drl` | 0 | - | FAIL |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 0 | - | FAIL |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 0 | - | FAIL |

## Retained Evidence

Here `PASS` means a nonempty file contains its configured text marker
(or exists when no marker is configured). Some markers are only titles:
this table does not establish that every report is ready or its contents
were freshly verified. Run the manufacturing gate for release checks.

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1798 | FAIL |
| Review waiver | `fab/gerbers/review-waivers.md` | 1967 | FAIL |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2632 | FAIL |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3564 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1385 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2005 | FAIL |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 20412 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 13453 | PASS |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | 16311 | PASS |
| Checksum file | `fab/gerbers/SHA256SUMS` | 0 | FAIL |
| Order evidence template | `docs/replica-order-evidence-template.md` | 4239 | PASS |

## Order-Time Checks

- [ ] Confirm `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`; do not upload while it reports any unreleased status.
- [ ] After release, upload only `upload/juku-replica-gerbers-drill.zip` for PCB fabrication.
- [ ] Confirm vendor preview matches `docs/replica-package-geometry-readiness.md`: 2-layer board, 310 mm x 266 mm Edge.Cuts box, and one mixed-plating Excellon drill file.
- [ ] Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.
- [ ] Select 1.6 mm FR-4 unless deliberately changed after DFM review.
- [ ] Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.
- [ ] Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.
- [ ] Review the current findings and acceptance status in `docs/replica-fab-drc-disposition.md` against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.

## Failures

- missing or empty upload file: juku_routed-F_Cu.gtl
- missing or empty upload file: juku_routed-B_Cu.gbl
- missing or empty upload file: juku_routed-F_Mask.gts
- missing or empty upload file: juku_routed-B_Mask.gbs
- missing or empty upload file: juku_routed-F_Silkscreen.gto
- missing or empty upload file: juku_routed-B_Silkscreen.gbo
- missing or empty upload file: juku_routed-Edge_Cuts.gm1
- missing or empty upload file: juku_routed-job.gbrjob
- missing or empty upload file: juku_routed.drl
- fab-readiness.md does not contain expected marker `Fabrication-file inventory gate: **PASS**`
- review-waivers.md does not contain expected marker `Status: **ACCEPTED**`
- external-gerber-review.md does not contain expected marker `Status: **READY**`
- docs/replica-fab-drc-disposition.md does not contain expected marker `Status: **READY**`
- docs/replica-power-trace-readiness.md does not contain expected marker `Status: **READY**`
- missing or empty evidence file: SHA256SUMS
- upload ZIP was not created
- upload SHA256SUMS.txt was not created
