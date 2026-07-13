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
| Top copper | `juku_routed-F_Cu.gtl` | 384621 | `fec2dce9e40162e95cc57dc2588b438f702377373331aaf87dc09537fb2e9456` | PASS |
| Bottom copper | `juku_routed-B_Cu.gbl` | 327687 | `e66878bc0a52edec37111ef4214ae189c49701763779ea8b3a38c4814820aff2` | PASS |
| Top soldermask | `juku_routed-F_Mask.gts` | 67058 | `48c24ba68013e7c0ab14aa055de3a531e6d4add3c90876294c8fb8794966e652` | PASS |
| Bottom soldermask | `juku_routed-B_Mask.gbs` | 67058 | `04dd2385027c40a1b53a0c8646243ff9b59e4b3c41ae7a0ec5532ac8d73efe6c` | PASS |
| Top silkscreen | `juku_routed-F_Silkscreen.gto` | 2036860 | `b1c4e7ac7336e7158e575ce9acd85c12afac9995ad82325c5240a86b92e4cbc6` | PASS |
| Bottom silkscreen | `juku_routed-B_Silkscreen.gbo` | 533 | `94c08342a9211131786e7f5b4c9bfe9d50baec17e029fbc9b773b74deca1401d` | PASS |
| Board outline | `juku_routed-Edge_Cuts.gm1` | 1302 | `3ee6d203a9068346bb493637680cd4afe335eb054c2560f75b0974d535b465b7` | PASS |
| Gerber job | `juku_routed-job.gbrjob` | 2445 | `1db732769e450d82ff5ed8b02f580ddbe592af660d1aa36b3dc1f662d426ec50` | PASS |
| Excellon drill | `juku_routed.drl` | 44122 | `805197e87b10a2e1090c0130f46da9f0a05c9d106b0c95acc1e46391c39aa76c` | PASS |

## Upload Archive

| File | Bytes | SHA256 | Contents |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/juku-replica-gerbers-drill.zip` | 790180 | `341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4` | FAIL |

## Upload ZIP Members

- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`

| Member | Bytes | Metadata | Source match |
| --- | ---: | --- | --- |
| juku_routed-F_Cu.gtl | 384621 | PASS | PASS |
| juku_routed-B_Cu.gbl | 327687 | PASS | PASS |
| juku_routed-F_Mask.gts | 67058 | PASS | PASS |
| juku_routed-B_Mask.gbs | 67058 | PASS | PASS |
| juku_routed-F_Silkscreen.gto | 2036860 | PASS | PASS |
| juku_routed-B_Silkscreen.gbo | 533 | PASS | PASS |
| juku_routed-Edge_Cuts.gm1 | 1302 | PASS | PASS |
| juku_routed-job.gbrjob | 2445 | PASS | PASS |
| juku_routed.drl | 44122 | PASS | PASS |

## Upload Checksum

| File | Bytes | SHA256SUMS entry | Status |
| --- | ---: | --- | --- |
| `fab/gerbers/upload/SHA256SUMS.txt` | 97 | `341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4` | PASS |

## Retained Evidence

| Purpose | File | Bytes | Status |
| --- | --- | ---: | --- |
| Order readiness | `fab/gerbers/order-readiness.md` | 2875 | PASS |
| Fabrication readiness | `fab/gerbers/fab-readiness.md` | 1772 | PASS |
| Review waiver | `fab/gerbers/review-waivers.md` | 1747 | FAIL |
| External Gerber review | `fab/gerbers/external-gerber-review.md` | 2125 | PASS |
| DRC visual disposition | `docs/replica-fab-drc-disposition.md` | 3028 | FAIL |
| Package geometry | `docs/replica-package-geometry-readiness.md` | 1415 | PASS |
| Power trace readiness | `docs/replica-power-trace-readiness.md` | 2546 | PASS |
| Bring-up verification points | `docs/replica-bringup-verification-points.md` | 83889 | PASS |
| Sourcing readiness | `docs/replica-sourcing-readiness.md` | 8440 | PASS |
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
