# Replica order-upload runbook

Fabrication package: `fab/gerbers`
Upload archive: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Status: **PACKAGE INVALID**

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
| Top copper | `juku_routed-F_Cu.gtl` | 384651 | `55e5ba8dc44e30a82f3d77cf0648a31aa1906deb58dfd32ce1f2b745689064c3` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 327666 | `6ed94f4b9ea5d4a13a0c2a9ebfa14c6a0a69e20e4a79ff950941a60c2c8be2dd` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 67058 | `3f08b8720f87432b522ae56128581bbd9633559a1079910acd4bd4aded0cf7fd` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 67058 | `5caff2333072cacbbaf2b959b40f1f5abd3af7cf08d3f7c89cbe25bc8e6cf380` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2036860 | `84d9f11809672e3e3a1581336af8c9a7bce6f12ccf98143f99e6da9e792d8174` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `5adaf8054d32a9b7e8106ce225dafe21a9e53c6a880a41f5bbc25a3e7e0b6564` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `85910fb379b54e674528fd34c118fad6fe91ccf5062523badf3eff03f43e4943` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `c6e257ebe318f9ce59d988f5799ae199ac75c3b51b49a04d6bc4a745d794b0ff` | PASS |
| Excellon drill | `juku_routed.drl` | 44166 | `55c20e1ff44ad01fc9679a9e105e82b6d0766ffd791a0c8f3f81797c91ff724b` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 790221 | `7df2a6e2927c62313275f3f5713e2b4cf3622c3c782b795cf41b27c8f3bfff46` | FAIL |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 384651 | PASS | PASS |
| juku_routed-B_Cu.gbl | 327666 | PASS | PASS |
| juku_routed-F_Mask.gts | 67058 | PASS | PASS |
| juku_routed-B_Mask.gbs | 67058 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2036860 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 44166 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `7df2a6e2927c62313275f3f5713e2b4cf3622c3c782b795cf41b27c8f3bfff46` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2871 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1852 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1797 | FAIL |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3199 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2554 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 73517 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9240 | PASS |
| Checksum file | `fab/gerbers/SHA256SUMS` | 805 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 3165 | PASS |

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

## Failures

- review-waivers.md does not contain expected marker `Status: **ACCEPTED**`
- docs/replica-fab-drc-disposition.md does not contain expected marker `Status: **READY**`
