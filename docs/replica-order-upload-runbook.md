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
| Top copper | `juku_routed-F_Cu.gtl` | 981046 | `91f1ebee4f7e6bba959288dafa0e31ea75c0fb74badcae80c938958c739394d2` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 852500 | `cb96cd268ad589e41281a7107f7cb315c0e372e3da564ea6ec9ed47d6400934f` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71143 | `17f3daa2a75353eaecdedfa4425d179206f20d46261ca055ca50fb53a7da7425` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70436 | `34584c1d3e24222ea99f817d129960cf518010e61cf1bd0294227a380ba047ee` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 3129059 | `d159c51a69618b53afed6b126e9af53029b126f025bebe4901cbbbdbcfc1cf81` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `4e7ae71b8ecaa44f2a49cffc5e9d59d0c7c82d445c10fe5a671000166640c783` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `92214e79e3ab5892c8a651d43ed06d06f7cb3c461dfc3eb9d0ca8331a136ef04` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `5df73a030854525ec17625976f78d14e7a341bc7f737c02032e983dfcd452d2a` | PASS |
| Excellon drill | `juku_routed.drl` | 81107 | `2ab4e1779a0f0136cbab4eaed4343a1c181c82db60e955b0b73719f3675667c8` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 5190681 | `09253384d703c8a200d49ee360661825a6b0c057364d5308115c9f0b6e116ca9` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 981046 | PASS | PASS |
| juku_routed-B_Cu.gbl | 852500 | PASS | PASS |
| juku_routed-F_Mask.gts | 71143 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70436 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 3129059 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 81107 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `09253384d703c8a200d49ee360661825a6b0c057364d5308115c9f0b6e116ca9` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1901 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2126 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2962 | PASS |
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
