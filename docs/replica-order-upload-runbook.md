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
| Top copper | `juku_routed-F_Cu.gtl` | 361790 | `0682add47739c5fd881ef5f69a249343dab00a72ab7ab875d1e09c6f50eb7548` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 318377 | `074436a557301fa597e6393bc1c70ad37a1965593c21b0fddb0cfe2a6d0687c9` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66904 | `058b84dd401f1eb0716c9f539a9e88bfb589cacfbbf95d29a41609c9895fe37c` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66904 | `90d65f348178de512d6cb6f848653accba4d99d012a9dfddd1fb6b17e24c0a7c` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035333 | `b5a9fff489faeba31712513651ae006de3c740bf7ad5131ee0edf8a2d3ee85d6` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `e7d9bf19364df50e9f3d8c9b5ff8d9b7e4b950a216e4eb2efb5f172543f3aa37` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `1a71268a16d53758c33c3afeb04c622f46d794dcf647a7d0ab912eba6cad866e` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `957f9bc509cc13e2303c3efaa0f82425823d8f242055d3a8bcfd5965d71d6d57` | PASS |
| Excellon drill | `juku_routed.drl` | 42991 | `1a23d255e02fcedf9fee94003227033b2c9efd25019ee6a8212b7fd61ca518c9` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 782002 | `261db032c3301d5604feca84ee3cd581aaa5dc924d8a183a921c4b0d180de0a1` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 361790 | PASS | PASS |
| juku_routed-B_Cu.gbl | 318377 | PASS | PASS |
| juku_routed-F_Mask.gts | 66904 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66904 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2035333 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42991 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `261db032c3301d5604feca84ee3cd581aaa5dc924d8a183a921c4b0d180de0a1` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2873 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2647 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 13060 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8548 | PASS |
| Checksum file | `fab/gerbers/SHA256SUMS` | 805 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 3085 | PASS |

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
