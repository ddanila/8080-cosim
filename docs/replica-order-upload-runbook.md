# Replica order-upload runbook

Fabrication package: `fab/gerbers`
Upload archive: `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
Status: **READY**

This is the exact upload/runbook layer for the main replica board PCB order.
It does not claim live vendor DFM acceptance; those checks happen in the
vendor UI immediately before payment.

## Pre-Upload Integrity

Run from the repository root:

```sh
kicad/check_replica_manufacturing_ready.sh
```

## Files In Upload ZIP

| Purpose | File | Bytes | SHA256 | Status |
| --- | --- | ---: | --- | --- |
| Top copper | `juku_routed-F_Cu.gtl` | 358515 | `627c9c00689e0c8b58a4f45dd0a8734b7f7aa441f4a03d52a65381658fd31874` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 319987 | `631f584cc568cff3ba1115aac26eac2ef5692c608611532532ccd40381d49609` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66645 | `25ac8c0116bc23af66ac5a00b4a65599f09cca0f8c9abe02c5858fc555e15db4` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66645 | `89025f600a1153555eeaf1a4110be97e5a37c75b729fa23d2d3d9a29bf671d54` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2031026 | `1a7e27bdf3df61927ca192a8ecd4a123bf19d46a065e07914a1e80cfb5a90d6f` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `09bf67e1db70fb48f9b4694213523f37e3b44c40bc1cef397abc271df759c070` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `255ab4a85caa7935d4d7bd93126634b63007d4d109f26a6c455c762bc9ceb5ea` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `af40cece4309111b957823242223a71ab8d7dd8fa1005958f39c3506a0e94962` | PASS |
| Excellon drill | `juku_routed.drl` | 42878 | `7bef7bed9516f490ad225676b35baba2328d9fcc4a18e065426d1e34c357044f` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 787065 | `93de3fc0a16b4bb31a4f613af69833ed24353d403d8870a774e365d534a7c815` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 358515 | PASS | PASS |
| juku_routed-B_Cu.gbl | 319987 | PASS | PASS |
| juku_routed-F_Mask.gts | 66645 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66645 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2031026 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42878 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `93de3fc0a16b4bb31a4f613af69833ed24353d403d8870a774e365d534a7c815` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2253 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1905 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1629 | PASS |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 2912 | PASS |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2788 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 12793 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8360 | PASS |
| Checksum file | `fab/gerbers/SHA256SUMS` | 805 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2795 | PASS |

## Order-Time Checks

- [ ] Upload only `upload/juku-replica-gerbers-drill.zip` for PCB fabrication.
- [ ] Confirm vendor preview matches `docs/replica-package-geometry-readiness.md`: 2-layer board, 310 mm x 266 mm Edge.Cuts box, and one mixed-plating Excellon drill file.
- [ ] Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.
- [ ] Select 1.6 mm FR-4 unless deliberately changed after DFM review.
- [ ] Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.
- [ ] Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.
- [ ] Review the 599 accepted courtyard/PTH/silk/text findings against the vendor preview before payment.
- [ ] Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
