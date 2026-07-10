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
| Top copper | `juku_routed-F_Cu.gtl` | 361553 | `869064e9f163f7e0c7622eccc9c20176e0e76dc75f192f7b88aa260a74f836b9` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 318311 | `d5b19d17dab8da3ba110ed3d802ba337a16b289401c601163ab1fa90bedfa785` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66904 | `8849b874ff71403b1efe27b050d22b85ec4ab78c21375f7b07a6d6250095208b` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66904 | `a2c0473d8aa6c5f554c68064948d7d46838bf67bba2b494a24695f84fd1f9d6d` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2035333 | `7a1b82c4d6025acec554ac90dfe858076a8287472ee44b9440ed0d6a00c8d8b2` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `20eedafe4bcddc21102f8805e9c172d211aeeeedc8ce2d8882ed9d59d644ac5a` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `6c4c9e4890c50d7d7ac4d87cd734411f2dc159035cd4b2f6c48ff7fb19098dd1` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `9af7f5a14ac031c53eac3d6559dccf61ae31b73e84780adab1ed36b2242ac571` | PASS |
| Excellon drill | `juku_routed.drl` | 42991 | `069c279ea4b29a4c58646043a0c1ff0ad8fb146fdefbc25236f5b3dc4b365634` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 781950 | `7001c1245d4bb92d552800eec35e33de399768d4c7cb2ec871eeef69c3dfb07e` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 361553 | PASS | PASS |
| juku_routed-B_Cu.gbl | 318311 | PASS | PASS |
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
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `7001c1245d4bb92d552800eec35e33de399768d4c7cb2ec871eeef69c3dfb07e` | PASS |

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
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 12587 | PASS |
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
