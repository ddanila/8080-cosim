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
| Top copper | `juku_routed-F_Cu.gtl` | 358644 | `26ffdc274fea956df9a4091090611558f137cc8c94cf74e1a9f924cf9e0d8ab6` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 320419 | `0461ff6dd10e13213d92bea59b6385217123f3e26e80ad1ff99460bf3ef705b2` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66717 | `9c09fe069ed710c7a4e1589007b33014f878e36b60c5935108e3d4af94e74613` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66717 | `2654284ff905a1abf840bc413464b759214dfa31f6c93c866d5adcfa079abba2` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2031026 | `5650fe2f231c43531cfbb6dd96e4674915d4e7b8ce6a2bdb328338853ce52fe7` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `0d05403430bab432a817f15e1ea2b60722eae49e4b9349f5e1d626dab5eea5e6` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `329906a846726e6d828809362b3776e98e38f8bae97af49514634bab4d835efd` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `af8702ead2515fff04682b57bb03e955febaee0b5207222a0a15e900cc3734c7` | PASS |
| Excellon drill | `juku_routed.drl` | 42914 | `d26bf004073dc2e7759bc4a7d8e125d8341578e6d6833aeb957314f3bbb58d05` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 787196 | `77f71719133c19470d853b4769e3584df2a2854320a68febb934ea7c25f74424` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 358644 | PASS | PASS |
| juku_routed-B_Cu.gbl | 320419 | PASS | PASS |
| juku_routed-F_Mask.gts | 66717 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66717 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2031026 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42914 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `77f71719133c19470d853b4769e3584df2a2854320a68febb934ea7c25f74424` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2854 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1905 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1629 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2912 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2788 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 12587 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8547 | PASS |
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
- [ ] Review the 599 accepted courtyard/PTH/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
