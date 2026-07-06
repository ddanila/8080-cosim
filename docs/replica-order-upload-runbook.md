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
| Top copper | `juku_routed-F_Cu.gtl` | 358515 | `3ae71434fbbb1532025cfdc8eb139e1f687ecc55075797acb3c65a622c342e45` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 319987 | `9156ea7baa0711e7b52551d975f78af906d5126fca38667606d623dcd1db7ead` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 66645 | `f0647fbead25809535f003ec185ad65f4e7085ab3f0d6dff454a011aa5f397ac` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 66645 | `ccf9edcbdaca982711f7871c31b63e16a6ba5b53722135cb5dffd469c83f6065` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2029476 | `a0fe021df0ab3d4814f807fa159831ce609c723c12d3e39f8ffaa2ede52aca47` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `0c7108d46f67f6ae0439fb96302f29128b6ff201df4f5a33b5c3ee046f97fd83` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `7158404960b6e72fb3adc13bb5902aa2731bf29e02be3faed5efff19a56d60af` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `6539002190380ce28f5ac2db0a5c799ed60ddbf5dc04f378732b5ba2f4c61406` | PASS |
| Excellon drill | `juku_routed.drl` | 42878 | `252a814b7cf4a2e55467fa6ff3430df644ca3e1b84c45298dfd11fabca94633c` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 786506 | `0f52569a63601573c300ef099561f93bda1845cf51985a530b9e46863232a211` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 358515 | PASS | PASS |
| juku_routed-B_Cu.gbl | 319987 | PASS | PASS |
| juku_routed-F_Mask.gts | 66645 | PASS | PASS |
| juku_routed-B_Mask.gbs | 66645 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2029476 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 42878 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `0f52569a63601573c300ef099561f93bda1845cf51985a530b9e46863232a211` | PASS |

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
| Checksum file | `fab/gerbers/SHA256SUMS` | 805 | PASS |
| Order evidence template | `docs/replica-order-evidence-template.md` | 2208 | PASS |

## Order-Time Checks

- [ ] Upload only `upload/juku-replica-gerbers-drill.zip` for PCB fabrication.
- [ ] Confirm vendor preview matches `docs/replica-package-geometry-readiness.md`: 2-layer board, 310 mm x 266 mm Edge.Cuts box, and one mixed-plating Excellon drill file.
- [ ] Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.
- [ ] Select 1.6 mm FR-4 unless deliberately changed after DFM review.
- [ ] Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.
- [ ] Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.
- [ ] Review the 599 accepted courtyard/PTH/silk/text findings against the vendor preview before payment.
- [ ] Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.

## Do Not Upload

- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.
- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.
- Review PNG/SVG outputs are retained as evidence only.
