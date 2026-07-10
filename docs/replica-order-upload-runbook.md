# Replica order-upload runbook

Fabrication package: `fab/gerbers`
Upload archive: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**

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
| Top copper | `juku_routed-F_Cu.gtl` | 359145 | `05ff91b4d17a2a68de18628a67fb67bdcef367d2514f89db2e3411e9bb272366` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 326640 | `1bb36048d082ff248dc9869d54360096c68260c58f5fcd227f8c89b1b2d2e027` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66929 | `a0c2678b93bf086c3e2bdcb27144280cb4966f37df87f2a3cca5983b162abfd5` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66929 | `e146ead3ec53a5db054c3c03833abfb84d3b229085db4cb3df78d19d7336fea8` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035507 | `080264d921211ae9d9175598a7f1b38644832aec089d4c78dbb8f26cf260a073` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `f41e2fcc92b372f9717a8b097fe2842d1c50237de3d5bf9254959e3bdf5be0c2` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `b9814a62c7e70b904e0c8619e2b024d8fce0b9ebb9d12670e111d4528ff69070` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `99855e022a0926e3fadfdc3da1f5f5c6b7e23795b67256068279b4fa2a070fdd` | PASS |
| Excellon drill | `juku_routed.drl` | 42618 | `40a97871ff15ea1ae74429756f4f5c49ecbf88cee67400c75ac26547d079aeff` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 786139 | `cf2ea833be2a0be7ceaa2147682a5cb4a6a86c4da963340b3b3d5aa2e8e35518` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 359145 | PASS | PASS |
| juku_routed-B_Cu.gbl | 326640 | PASS | PASS |
| juku_routed-F_Mask.gts | 66929 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66929 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2035507 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42618 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `cf2ea833be2a0be7ceaa2147682a5cb4a6a86c4da963340b3b3d5aa2e8e35518` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2873 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2351 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 13555 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8548 | PASS |
| Checksum file | `fab/gerbers/SHA256SUMS` | 805 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2957 | PASS |

## Order-Time Checks

- [ ] Confirm `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`; while it says `DESIGN HOLD`, do not upload anything.
- [ ] After release, upload only `upload/juku-replica-gerbers-drill.zip` for PCB fabrication.
- [ ] Confirm vendor preview matches `docs/replica-package-geometry-readiness.md`: 2-layer board, 310 mm x 266 mm Edge.Cuts box, and one mixed-plating Excellon drill file.
- [ ] Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.
- [ ] Select 1.6 mm FR-4 unless deliberately changed after DFM review.
- [ ] Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.
- [ ] Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.
- [ ] Review the 533 accepted courtyard/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
