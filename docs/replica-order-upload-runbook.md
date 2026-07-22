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
| Top copper | `juku_routed-F_Cu.gtl` | 981046 | `63126a8cc6066a8c21e0b5fe4ad0a91b331d6cdf85b6fdee71d1660e4a1b27f8` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 852500 | `b3dad4d8157af3b1ec1323da65e70ecb85a34c56fbb7262dd1aaaf9b2c37fa7c` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71143 | `bdfdebc6796b8d4008076ed16ad5cd34566944c79caf51e6b76ffb93ce30ec51` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70436 | `cc0bc694a44a00810424809ff187eac68834cee596f254f93d4470beab94d1c9` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2814327 | `020543c717bada7cf39552e876d3c8b0802987a7879f159b5286916f050ce312` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `d7c89dfea4053fdd70cab2efffe67d5d0fc29c2305cee05741603d69c566c513` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `5fbda94db39fa31108bcf2213ce737ca3ad42bf2e386f7e40329226139e2f2b9` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `3190faa7a174581bae6b95aee8c94122c245b9cac50cabbaca410dce7c94d11c` | PASS |
| Excellon drill | `juku_routed.drl` | 81107 | `1b8ddc98c502b66f44d4026f6be5b500f218a4980ac83cb79b41eae06123aa9a` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4875949 | `136f0b701a1442eda40e72590822233f278851f516a5404bcf1ad19c4a3b6b28` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 981046 | PASS | PASS |
| juku_routed-B_Cu.gbl | 852500 | PASS | PASS |
| juku_routed-F_Mask.gts | 71143 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70436 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2814327 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 81107 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `136f0b701a1442eda40e72590822233f278851f516a5404bcf1ad19c4a3b6b28` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1901 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2126 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2959 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1385 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2147 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 15976 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9109 | PASS |
| Factory wire construction | `docs/factory-wire-route-fidelity.md` | 12334 | PASS |
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
- [ ] Review the 704 accepted courtyard/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
