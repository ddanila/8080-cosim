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
| Top copper | `juku_routed-F_Cu.gtl` | 359912 | `9b28957fd3352c51c46694f4cea17ec72d88090b36475fb94c43a180deea9171` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 317534 | `59e1bc651eefa95fd95a30b274810d6cb30c20cfee40267777c243d940c2ece0` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 67083 | `e18c53cec7b2e93efaa0f89ab4117bf372eaddec345ad9d212d522bf32ef1196` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 67083 | `4dcb4ff6acb655f9bf4f783574f24f7d5f1eb6e1b659d5a08c243e6cf0ddd717` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035522 | `56e544f16164bc62438a4932db9b4ab1313d9fb8e4345e9003a7f8a2485c855d` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `8918b2455f2c8ecd01b2afce272e26e62dee8d1f1049ec28a119b64acfc57774` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `40d65b1f31a43e36d766d5653a2a3a097a4f18879d7e250921869e93ba7768e3` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `c81bc7059042b2054a0e26a21c55c7844c7698720ecb4a8892694338f317ed3b` | PASS |
| Excellon drill | `juku_routed.drl` | 42971 | `2511acd7c4e0d528879b19ea15babcd1f8c7d81e133dfb8c5fdf62b26ddbc3e1` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 785899 | `cf346cce590ea3d11c6f072face5161782f5cc4ab17a1e1cabe68e4d0b31f20e` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 359912 | PASS | PASS |
| juku_routed-B_Cu.gbl | 317534 | PASS | PASS |
| juku_routed-F_Mask.gts | 67083 | PASS | PASS |
| juku_routed-B_Mask.gbs | 67083 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2035522 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42971 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `cf346cce590ea3d11c6f072face5161782f5cc4ab17a1e1cabe68e4d0b31f20e` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2874 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2510 | PASS |
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
