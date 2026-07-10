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
| Top copper | `juku_routed-F_Cu.gtl` | 375844 | `12785d59ec2c069dd2b3e7e8749e15464f6c6d3d9dfa2e93180587235da6dee0` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 321719 | `ab5e31b528642d1de797f41f5ca47a4fbfddaf76d687ffcaf35e5fa16b5decf6` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 67058 | `1454200a6c66e7658755268e27e0f2ae9efdd350a60a9c645e6f14aa10243eb7` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 67058 | `38b67e9aa85381133800ea1c06efb302ca9c541819db98026f07fe50f962b243` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2036860 | `334dfdfd789cb20cf0c5319032b5be8f42155ebcc7ea2f0e1a35b5ad694f8648` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `16801c362361f90fae23c522cf6bd65931307401e1c10d7029b29a3dc3009e41` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `e1e2f8d1c98324990ea02f1ee7d227bfbc080f08008b8e3b4343224b656bba21` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `8b6ad2e4233f5ad7072c7f20435eb931e6322a7bcce2e69a78806c33e2fb39ce` | PASS |
| Excellon drill | `juku_routed.drl` | 43328 | `a8a0ec4683340632d4572a793ade1070fddf822e7b2d49a7eb6a234b0c8b287c` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 787272 | `a1688aab1625a6c1d2a4ee4aa87540030d9b82b5d545b7bca9aa7e3ebc7da344` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 375844 | PASS | PASS |
| juku_routed-B_Cu.gbl | 321719 | PASS | PASS |
| juku_routed-F_Mask.gts | 67058 | PASS | PASS |
| juku_routed-B_Mask.gbs | 67058 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2036860 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 43328 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `a1688aab1625a6c1d2a4ee4aa87540030d9b82b5d545b7bca9aa7e3ebc7da344` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2822 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1875 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1628 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2874 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2598 | PASS |
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
