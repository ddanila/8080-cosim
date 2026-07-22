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
| Top copper | `juku_routed-F_Cu.gtl` | 980982 | `319ae5453e9b09709073b1a8d7761001ee52d458e8e838c979cdc6f284a44943` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 852436 | `b6b02c1ad477d73178f44badaac11475bea1e4f4248a38281ccbc729676a71e0` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71079 | `e7185626a89f5dfa25693a1938e92c83641f1364343dea2458aca66bbc8f02ff` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70372 | `5dc2937ac02b6e17e2842eae39e58e51d88633ac5ee476caea1ad321b3008d62` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2697367 | `562367e433d7d0e8df2cacc47550be47b50570086a0ef63d9f725b99ebd7527c` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 469 | `94f51694a32716c8e9215dc85951099e83f131f92164ad3ca82d29156e748d1a` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1238 | `1c12329a3d38f1034644e5984c341b712d71b4160759ad06a317f9e48c2ca164` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2413 | `bb0922fffdb07a57e12383f3eeb5a8422f4b66d3891c53f4c6b920e846273293` | PASS |
| Excellon drill | `juku_routed.drl` | 81050 | `2c3adb5cab041d59550d0a7a7bb604bf215b3240838546db1969263027e04ef3` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4758516 | `dd074e982cea6d9d4945817506e5a1c6a894b675124f30260b06b9562a87310a` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 980982 | PASS | PASS |
| juku_routed-B_Cu.gbl | 852436 | PASS | PASS |
| juku_routed-F_Mask.gts | 71079 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70372 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2697367 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 469 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1238 | PASS | PASS |
| juku_routed-job.gbrjob | 2413 | PASS | PASS |
| juku_routed.drl | 81050 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `dd074e982cea6d9d4945817506e5a1c6a894b675124f30260b06b9562a87310a` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 3030 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1891 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2127 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2965 | PASS |
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
- [ ] Review the 703 accepted courtyard/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
