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
| Top copper | `juku_routed-F_Cu.gtl` | 369825 | `5039a710810b228f8264e8870b46c01677335218613b4bf7066bc6ed9f694724` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 316764 | `8a3f6d08834e5c7d3e9f95a1341a4e8ae54eeabebfc8d7475cb05044bb5d9d8f` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66914 | `168fe237fc08d6a689e37f0cc83c2fdeffb8d5c8ffbd7631200188c3a52ec098` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66914 | `083e7f6aea3b4dde54ec7fb799b9fc8f13f8d91ebf388adbec825f2ad738684e` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035502 | `b6492be708b0b0fcc8442c1d1607f8540a6e234c38d38b50e73879b18ef84a0f` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `2a2fa02e46720fe4bb7fc91c776b7e5722efe284dbd25c5854d1e0b54d3ba604` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `6cd93f82a5987ea0f3a00a79a1c5ace1f1f8698d8113847eb01d4f2f08a5bb12` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `8d9aae8c16e9e53aff4d7f69cd9de12be630eeec929dcbe5c05915df58890e0f` | PASS |
| Excellon drill | `juku_routed.drl` | 42788 | `d8e905c5f0c1bfff6e3a47d2360421344d6339b5999a3d6dcb9b3f0c21e02b0a` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 787459 | `dec4424f17b16c36f3ccb09c1697b4cf2d665ff456ddbf36619025a3898409fd` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 369825 | PASS | PASS |
| juku_routed-B_Cu.gbl | 316764 | PASS | PASS |
| juku_routed-F_Mask.gts | 66914 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66914 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2035502 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42788 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `dec4424f17b16c36f3ccb09c1697b4cf2d665ff456ddbf36619025a3898409fd` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2873 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2638 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 13845 | PASS |
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
