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
| Top copper | `juku_routed-F_Cu.gtl` | 370885 | `d94e7105a899139158af106f3b1226f4089e1440453c78ce5793bab3feb24022` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 318961 | `cf6dacf36dbef8668aa40d492b62a59d6860f8425f72c858c7a2fb9eb261a220` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66929 | `ca52554cf6f1c27394c93e945b7a636d867642cb5a31d020f9e8bd4d20455109` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66929 | `f316926ec81a75e441386918a832faf187dfb0363d2372d187446ed4571aa840` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035487 | `ddac022907d09ef19917e0eff9e26c4d4982981696441efddec7bc0c21b9ea76` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `f894bcabf66d0be81192bc3c478cf154a21f2d5930c6a3d59120ffb1596c84a1` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `b3a7fef11165accd815ede227a45437e7c8db136b502b674fef6e270c3b05302` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `f09f132bb271943acd80aaafc29ac2c7fe6d336aa10789b9e44217e6c63bf9bd` | PASS |
| Excellon drill | `juku_routed.drl` | 42777 | `dbb3fde00ef6397f10a6640cf453c993b6a1b7c63bc6c33774840fd5d8d5c62f` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 785575 | `d81a7ffbc401dfb8fbc6af22f775d18a4dde04d0b8c481f9b9199a7044a2a62e` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 370885 | PASS | PASS |
| juku_routed-B_Cu.gbl | 318961 | PASS | PASS |
| juku_routed-F_Mask.gts | 66929 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66929 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2035487 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42777 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `d81a7ffbc401dfb8fbc6af22f775d18a4dde04d0b8c481f9b9199a7044a2a62e` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2824 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2873 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2513 | PASS |
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
