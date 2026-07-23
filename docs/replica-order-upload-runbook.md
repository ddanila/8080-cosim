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
| Top copper | `juku_routed-F_Cu.gtl` | 994398 | `33c424cf5ad0d5915d2415a3a39b63289f379ff2e416f83f31f5a4744ec4c15c` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 867881 | `dcdfedb227e7a008487fe142e014459a0a5855e59aa2c8557aee81e186e36bb2` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71143 | `20d587c3df426ff8a93499921146f4907704692e01edce9261fc926b275798d4` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70436 | `fc00027a00dba853bfb223257f464846abe080bf6c4e0fcbf296ab267cc9102d` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2814327 | `13ba941bc6945b10b4850da159e1e8e398bc04cb5b1f9ed40d309b676a299de7` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `75f4bb05935d5ff9a8927ebe8241ed31f99490a06678b3404b4da6ff71856a11` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `35551d2dc533e13dfe50ddebdde09e4744e7723ccf2dd2c3395c28d0264dcba7` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `a4d736afa18c968487f5194d29a1e0e9f8e95ce0bf735c92e1d557d997a95054` | PASS |
| Excellon drill | `juku_routed.drl` | 82192 | `d8440687c346a022c72c936fbb056e4288fde330b2dbd3d31eed508bc4b3558f` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4905767 | `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 994398 | PASS | PASS |
| juku_routed-B_Cu.gbl | 867881 | PASS | PASS |
| juku_routed-F_Mask.gts | 71143 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70436 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2814327 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 82192 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46` | PASS |

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
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 9149 | PASS |
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
