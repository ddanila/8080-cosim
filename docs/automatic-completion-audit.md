# Automatic completion audit

Status: **DESK REVIEW REOPENED / SHORTLIST EVIDENCE HOLD**

This report inventories recognized Markdown checkboxes and verifies their
manifest classifications and cited text markers. It scans tracked and
untracked non-ignored `.md` files, excluding `external/` and the four
operator templates. It does not inspect prose tasks, validate completed
checkboxes, rerun the cited guards, or establish that all desk work is done.

## Command

```sh
python3 scripts/report_automatic_completion_audit.py
```

## Active unchecked work

There are 8 unchecked items across 3 project-plan
documents. The manifest assigns these items to the boundaries below.
The shortlist reports an evidence hold; inspect its failed checks before handoff.

| Plan | Unchecked tasks |
| --- | ---: |
| `PLAN.md` | 6 |
| `docs/crt-cvbs-simulation-plan.md` | 1 |
| `docs/factory-drawing-exploitation-plan.md` | 1 |

| Plan item | Tasks | Remaining dependency | Required next input |
| --- | ---: | --- | --- |
| P0 physical connectivity and reroute | 1 | Remaining endpoints are hidden, contradictory under powered behavior, or continuity-only | owner continuity and powered captures from `docs/owner-measurement-shortlist.md` |
| Main-board release and order | 1 | The current routed board has open connections and needs copper repair plus a regenerated package; physical-connectivity and sourcing gates remain held | closed P0 evidence, regenerated and reviewed package, explicit release, vendor upload, and payment |
| Functional parts kit | 1 | No purchase is authorized and seller stock cannot establish fitted historical truth | procurement choice, purchase, receipt, and physical testing |
| Tier 1, 2, and 3 bring-up | 3 | These milestones require a fabricated and assembled physical replica | board, parts, instruments, staged power-up, and surviving-machine comparison |
| Physical framebuffer readout | 1 | D41/shared-DRAM slot timing, `SHIFT_G`, `TIMING_TAG17`, and `D34_SIG` are not evidence-complete | continuity/drawing closure and captured timing; no guessed serializer schedule |
| juku3000 community exchange | 1 | Publishing scope and venue are external-facing decisions | owner approval |

## Machine-checked classification

| Plan | Unchecked task | Class | Cited report markers |
| --- | --- | --- | --- |
| `PLAN.md` | P0 physical connectivity is complete and rerouted. | `connectivity` | `docs/owner-measurement-shortlist.md` (owner/bench packet on evidence hold); `docs/replica-bringup-verification-points.md` (source-risk net index unresolved); `docs/main-board-erc-parity.md` (release parity gate held) |
| `PLAN.md` | Main-board design release passes; board is ordered. | `release` | `docs/replica-manufacturing-readiness.md` (current package regeneration held) |
| `PLAN.md` | Functional parts kit is received and tested. | `parts` | `docs/replica-sourcing-readiness.md` (sourcing gate held) |
| `PLAN.md` | Replica completes Tier 1 bring-up. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `PLAN.md` | Replica completes Tier 2. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `PLAN.md` | Replica completes Tier 3. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `docs/crt-cvbs-simulation-plan.md` | Replace the simulation-only framebuffer read port only after the | `framebuffer` | `docs/video-slot-timing-audit.md` (physical video-slot schedule pending); `docs/crt-cvbs-simulation-plan.md` (implementation explicitly evidence-gated) |
| `docs/factory-drawing-exploitation-plan.md` | Decide what to share on juku3000 #25. | `community` | `docs/factory-drawing-exploitation-plan.md` (external publication is owner-gated) |

The 42 unchecked boxes in the order, order-evidence, parts-inventory,
and first-article documents are operator templates. They deliberately remain
blank until an authorized physical order/assembly record exists; they are not
repository implementation backlog.

## Guard

This writer found active unchecked tasks in 3 Markdown file(s).
Any new unchecked task outside the four operator templates must have an exact
classification. Classified milestones must remain present as checkboxes, and
cited evidence markers must exist. The owner/bench shortlist accepts either
`READY` or `EVIDENCE HOLD`; a hold is reported above, not treated as readiness.
Missing classifications or accepted markers fail generation.
`scripts/check_documentation_consistency.py` runs this writer in
`--check` mode, and `scripts/regen_all.sh` regenerates the committed report.

Use the [owner/bench shortlist](owner-measurement-shortlist.md) for the
listed physical evidence tasks. This inventory does not rule out further
repository review, documentation corrections, or implementation repairs.
