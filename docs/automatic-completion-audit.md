# Automatic completion audit

Status: **AUTOMATIC CHECKLIST EXHAUSTED / EXTERNAL ACTION REQUIRED**

This generated audit answers a narrow question: whether any tracked project
Markdown outside vendored `external/` material and operator templates contains
an unchecked implementation task that can be completed from repository evidence
and tools. It does not declare the replica complete or release the PCB.

## Command

```sh
python3 scripts/report_automatic_completion_audit.py
```

## Active unchecked work

There are 9 unchecked items across 3 tracked project-plan
documents. Every one now requires evidence, hardware, purchasing, fabrication,
or owner authorization.

| Plan | Unchecked tasks |
| --- | ---: |
| `PLAN.md` | 7 |
| `docs/crt-cvbs-simulation-plan.md` | 1 |
| `docs/factory-drawing-exploitation-plan.md` | 1 |

| Plan item | Tasks | Why automation must stop | Required next input |
| --- | ---: | --- | --- |
| P0 physical connectivity and reroute | 1 | Remaining endpoints are hidden, contradictory under powered behavior, or continuity-only | owner continuity and powered captures from `docs/owner-measurement-shortlist.md` |
| Independent PROM/EPROM corroboration | 1 | Repository donor search, history audit, physical small-PROM reads, and deterministic D15/D16 functional images are exhausted | programming-disk files, independent PROM reads, and repeat physical D15/D16 dumps |
| Main-board release and order | 1 | The verified zero-open package is intentionally held by physical-connectivity and sourcing gates | closed P0 evidence, explicit release, vendor upload, and payment |
| Functional parts kit | 1 | No purchase is authorized and seller stock cannot establish fitted historical truth | procurement choice, purchase, receipt, and physical testing |
| Tier 1, 2, and 3 bring-up | 3 | These milestones require a fabricated and assembled physical replica | board, parts, instruments, staged power-up, and surviving-machine comparison |
| Physical framebuffer readout | 1 | D41/shared-DRAM slot timing, `SHIFT_G`, `TIMING_TAG17`, and `D34_SIG` are not evidence-complete | continuity/drawing closure and captured timing; no guessed serializer schedule |
| juku3000 community exchange | 1 | Publishing scope and venue are external-facing decisions | owner approval |

## Machine-checked classification

| Plan | Unchecked task | Class | External-boundary evidence |
| --- | --- | --- | --- |
| `PLAN.md` | P0 physical connectivity is complete and rerouted. | `connectivity` | `docs/owner-measurement-shortlist.md` (owner/bench packet ready); `docs/replica-bringup-verification-points.md` (source-risk net index unresolved); `docs/main-board-erc-parity.md` (release parity gate held) |
| `PLAN.md` | Independent programming files/reads corroborate the four factory PROMs | `firmware` | `docs/firmware-gap-ledger.md` (Tier-1/2 burnable set guarded; Tier-3 truth absent); `docs/cartridge-basic-boundary.md` (remaining cartridge artifact boundary explicit) |
| `PLAN.md` | Main-board design release passes; board is ordered. | `release` | `docs/replica-manufacturing-readiness.md` (package verified under design hold) |
| `PLAN.md` | Functional parts kit is received and tested. | `parts` | `docs/replica-sourcing-readiness.md` (sourcing gate held) |
| `PLAN.md` | Replica completes Tier 1 bring-up. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `PLAN.md` | Replica completes Tier 2. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `PLAN.md` | Replica completes Tier 3. | `bringup` | `docs/replica-manufacturing-readiness.md` (no released fabrication package) |
| `docs/crt-cvbs-simulation-plan.md` | Replace the simulation-only framebuffer read port only after the | `framebuffer` | `docs/video-slot-timing-audit.md` (physical video-slot schedule pending); `docs/crt-cvbs-simulation-plan.md` (implementation explicitly evidence-gated) |
| `docs/factory-drawing-exploitation-plan.md` | After Stage 1.2, decide what to share on juku3000 #25 (the MAME | `community` | `docs/factory-drawing-exploitation-plan.md` (external publication is owner-gated) |

The 28 unchecked boxes in the order, order-evidence, and parts-inventory
documents are operator templates. They deliberately remain blank until an
authorized physical order/assembly record exists; they are not repository
implementation backlog.

## Automatically closed scope

- Source/routed PCB identity, zero-open copper, fabrication-package integrity,
  burnable Tier-1/2 firmware, and runnable HDL/cosim behavior have dedicated
  generated reports and CI guards.
- Firmware reconstruction has consumed every defensible repository donor;
  unresolved physical ROM truth remains unpatched rather than guessed.
- Physical shared-DRAM video timing and analog-output fidelity remain explicitly
  evidence-gated rather than replaced with a simulation convenience path.

## Guard

This writer found active unchecked tasks in 3 tracked Markdown file(s).
Any new unchecked task outside the three operator templates must have an exact
classification and all cited evidence markers must exist, otherwise generation
fails closed. `scripts/check_documentation_consistency.py` runs this writer in
`--check` mode, and `scripts/regen_all.sh` regenerates the committed report.

The practical next action is therefore the owner/bench shortlist—not another
inference pass over the same files.
