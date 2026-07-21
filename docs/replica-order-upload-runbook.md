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
| Top copper | `juku_routed-F_Cu.gtl` | 963266 | `e856bcddb13fc5dbe57d40127ba1b81fedd58d2b94f33ecbccb964a1cd4f702f` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 834874 | `e91cf7c6e24d642a380e5388039388925530451925285ed26fbae7424e94b106` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 70984 | `655d28983562d835bc5fa5178b830f46728c248b38ebe0ff69b52f4c308807b8` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70292 | `cfdcb83525826bc86cb98a9aebf644b218776112d4490eec8edcf83ad54c94bf` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2689173 | `72d7aedef3b88c28dca1231c6b4d13e2eec9c6493554f70faba1661c792d667f` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 469 | `9323d10acc00169ee5dedb2a4efca6f091c1108bf3f54b168bda867421cdff38` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1238 | `2fe1bfbda8db6434a5aa313ba24d86412c0e1b2dcca7cbdf6d40e84248326e33` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2413 | `ae31cee521226bee6fa24e4fc63e3b34d632f59a6de6463be2ef91ec0b9045d2` | PASS |
| Excellon drill | `juku_routed.drl` | 79661 | `fc3a5d21964382d83f7ddf691546d0f5670bd99f3d655253307a76a6768a5aed` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 1197416 | `d950a5e55a7627b731e40373c822dffaa9640354fcc50e4bcf927712cc31304c` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 963266 | PASS | PASS |
| juku_routed-B_Cu.gbl | 834874 | PASS | PASS |
| juku_routed-F_Mask.gts | 70984 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70292 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2689173 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 469 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1238 | PASS | PASS |
| juku_routed-job.gbrjob | 2413 | PASS | PASS |
| juku_routed.drl | 79661 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `d950a5e55a7627b731e40373c822dffaa9640354fcc50e4bcf927712cc31304c` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2934 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1891 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1630 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2127 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2965 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1385 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2147 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 16663 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9109 | PASS |
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
- [ ] Review the 701 accepted courtyard/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
