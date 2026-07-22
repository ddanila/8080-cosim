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
| Top copper | `juku_routed-F_Cu.gtl` | 984439 | `1a5034d60c0a61181cfe3a97744107f627e63cccffa41886f9134d921037967f` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 856664 | `ebeb5e617d1c283a178a818b0fedb2b6ae4721b60c9f4e13125cc647e5f04bd2` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71143 | `1f809710284e0316a67cb66dd3cba6093ebec1978ac049fe35f2108d0cde5aa6` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70436 | `9a16d3baeac03728f2464359aace9487b83618d8c97753456ee8bf556106fabe` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2814327 | `0a701561dbca9fe6ecd6c11e0b6fc2d85c79a19d12d2d27a7cf8c9c5f67c00f6` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `037bf0cee291ff29cdf8a10431d0131a14d91dd03b4c3984f02a94f79e14bf33` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `089bbdf58bbab87873690ad09c9e92c3199eac97ddb94c68b0c7498487ab48d6` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `338f70242cec0b2ff2b645277d8c0504c5084928e55f6057449065605eae82d9` | PASS |
| Excellon drill | `juku_routed.drl` | 81405 | `168d155b012d68be978483d23abca8246c0cfe9cc73cce4d5e43ef1a466d4ddb` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4883804 | `cef15e3abd93398fa40030662db62feaca805ba7c86c7bf61c54bd982f39e16a` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 984439 | PASS | PASS |
| juku_routed-B_Cu.gbl | 856664 | PASS | PASS |
| juku_routed-F_Mask.gts | 71143 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70436 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2814327 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 81405 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `cef15e3abd93398fa40030662db62feaca805ba7c86c7bf61c54bd982f39e16a` | PASS |

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
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 15741 | PASS |
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
