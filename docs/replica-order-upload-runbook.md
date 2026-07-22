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
| Top copper | `juku_routed-F_Cu.gtl` | 976797 | `d503428327ebdf1c42f60114b02cce0e2c43405822215928fd7039e03a69605a` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 845600 | `3bd4d6a1009ed493637a61d07ff7699e22706b63329ddb07513f4df1ed70cf59` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 71079 | `ca99bde8910a19e13ec591d08c868a0a63770d48a7c3c27fc55bfcbeec680144` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 70372 | `416903d5ab7cbd984c8eaa8ab6105bf2fa55c497f88e39357ae43bfaf10ffe04` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2697367 | `0c8c7ae332260aea430de8193aef03026bdc3803ace8daecd189f6cae96ac215` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 469 | `0d40aee447cd3f97f47b9e950d5198d22daf960e167d4a2435906b0569d6b056` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1238 | `54520a6e7ddefb284b195d853eaee4bd984c47dbcbd3a1d93e0b45740b539443` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2413 | `0681d0240dff170a7676350343e1477bfe8c585095ef62d25a4e4459b2364fc6` | PASS |
| Excellon drill | `juku_routed.drl` | 80534 | `247c9c6c529b104eaa0b27eb1e651c1bb33dd6d41a7acafe156738697ff401ea` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 4746979 | `bc5a9b2d3f027d455a5bd4a0eafa9e602a3bdd9b1b6d72d9037c508b2da615da` | PASS |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, stored (uncompressed) members, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 976797 | PASS | PASS |
| juku_routed-B_Cu.gbl | 845600 | PASS | PASS |
| juku_routed-F_Mask.gts | 71079 | PASS | PASS |
| juku_routed-B_Mask.gbs | 70372 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2697367 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 469 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1238 | PASS | PASS |
| juku_routed-job.gbrjob | 2413 | PASS | PASS |
| juku_routed.drl | 80534 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `bc5a9b2d3f027d455a5bd4a0eafa9e602a3bdd9b1b6d72d9037c508b2da615da` | PASS |

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
