# Main-board ERC and schematic/PCB parity

Status: **DESIGN HOLD**

ERC uses a generated include-power schematic under `fab/audit`; the normal
LVS schematic deliberately omits power nets. Parity uses `juku.kicad_sch`
and the same-basename source `juku.kicad_pcb`. The routed PCB is a derived
artifact; KiCad cannot run
schematic parity against it without a matching routed schematic/project.

## Summary

| Check | Count | Result |
| --- | ---: | --- |
| Raw ERC error violations | 54 | GUARDED |
| Unexpected ERC/mapping findings | 0 | PASS |
| Exact singleton-label findings | 54 / 54 | PASS |
| Source-risk singleton nets | 37 | BLOCK |
| Other source-risk nets | 7 | BLOCK |
| PCB/schematic parity issues | 0 | PASS |
| Explicit board-JSON no-connects | 68 | PASS |
| KiCad schematic no-connect markers | 68 | PASS |
| Functional pins without net or explicit NC | 0 | PASS |
| Duplicate board-JSON endpoint memberships | 0 | PASS |
| Unknown/conflicting NC records | 0 | PASS |

Stable KiCad reports one `label_dangling` error for every one-endpoint
local-label net. The exact label-name/count guard above proves these are
the modeled singleton boundary surface, not geometrically detached labels.
Of those `54` singleton nets, `37` remain source-risk
boundaries and `17` have closed or intentional dispositions.

## Unresolved endpoint priorities

| Priority | Count |
| --- | ---: |
| P0 | 11 |
| P1 | 25 |
| P2 | 1 |

The complete machine-readable singleton-endpoint backlog is
`docs/main-board-unresolved-endpoints.csv`.

## ERC types

- `label_dangling`: 54

## Most affected references

- None.

## Release interpretation

The raw ERC findings are exactly accounted for by modeled singleton nets, and
parity plus endpoint ownership pass. Source-risk nets remain release blockers.
They must be traced, redesigned, or individually given an evidence-backed
disposition. This gate does not suppress the singleton labels or convert them
to no-connects merely to obtain a zero-error ERC count.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
