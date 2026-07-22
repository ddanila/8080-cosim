# Automatic completion audit

Status: **AUTOMATIC CHECKLIST EXHAUSTED / EXTERNAL ACTION REQUIRED**

This audit answers a narrow question: whether the repository's owned plans
still contain an unchecked implementation task that can be completed from the
evidence and tools already present. It does not declare the replica complete or
release the PCB. The package remains verified under design hold.

## Active unchecked work

There are nine unchecked items in the active project plans: seven in
`PLAN.md`, one in the CRT/CVBS subordinate plan, and one external community
coordination decision. Every one now requires evidence, hardware, purchasing,
fabrication, or owner authorization.

| Plan item | Why automation must stop | Required next input |
| --- | --- | --- |
| P0 physical connectivity and reroute | Remaining endpoints are hidden, contradictory under powered behavior, or continuity-only | owner continuity and powered captures from `docs/owner-measurement-shortlist.md` |
| Independent PROM/EPROM corroboration | Repository search, history audit, physical small-PROM reads, and deterministic D15/D16 functional images are exhausted | programming-disk files, independent PROM reads, and repeat physical D15/D16 dumps |
| Main-board release and order | The verified zero-open package is intentionally held by the physical-connectivity and sourcing gates | closed P0 evidence, explicit release, vendor upload, and payment |
| Functional parts kit | No purchase is authorized and seller stock cannot establish fitted historical truth | procurement choice, purchase, receipt, and physical testing |
| Tier 1, 2, and 3 bring-up | These milestones require a fabricated and assembled physical replica | board, parts, instruments, staged power-up, and surviving-machine comparison |
| Physical framebuffer readout | D41/shared-DRAM slot timing, `SHIFT_G`, `TIMING_TAG17`, and `D34_SIG` are not evidence-complete | continuity/drawing closure and captured timing; no guessed serializer schedule |
| juku3000 community exchange | Publishing scope and venue are external-facing decisions | owner approval |

The 28 unchecked boxes in the order, order-evidence, and parts-inventory
documents are operator templates. They deliberately remain blank until an
authorized physical order/assembly record exists; they are not repository
implementation backlog.

## Automatically closed scope

- The source and routed PCBs have exact pad parity, zero opens, zero electrical
  blockers, and zero dangling copper; fabrication outputs and checksums pass.
- Every populated PROM/EPROM has a hash-guarded Tier-1/2 burnable image. The
  runnable twin executes all four validated physical small-PROM tables.
- Firmware reconstruction has consumed every defensible repository donor: the
  D15/D16 archive pair is uniquely EktaSoft 3.7, one Monitor 2.2 byte is proven,
  and unresolved ROM blocks/pages remain unpatched rather than guessed.
- The C and HDL FDC backends now support explicit 1,600-byte companion metadata
  for cross-run normal/deleted marks while keeping raw `.juk`/`.CPM` payloads
  unchanged. Arbitrary flux, damaged headers, and noncanonical ID geometry are
  still honestly outside the flat-image representation.
- Shared-DRAM framebuffer replacement, X7 voltage fidelity, and later receiver
  work are correctly dependency-blocked by missing physical timing/driver
  evidence rather than incomplete code scaffolding.

## Guard

`python3 scripts/check_documentation_consistency.py` checks the exact nine-item
active set, the 28 template boxes, this status marker, and the external-boundary
markers. A newly introduced unchecked active task makes the consistency check
fail until it is either implemented or explicitly classified with evidence.

The practical next action is therefore the owner/bench shortlist—not another
inference pass over the same files.
