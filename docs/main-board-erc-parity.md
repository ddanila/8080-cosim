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
| ERC error violations | 53 | BLOCK |
| PCB/schematic parity issues | 0 | PASS |
| Explicit board-JSON no-connects | 70 | PASS |
| KiCad schematic no-connect markers | 70 | PASS |
| Functional pins without net or explicit NC | 0 | PASS |
| Duplicate board-JSON endpoint memberships | 0 | PASS |
| Unknown/conflicting NC records | 0 | PASS |

## Unresolved endpoint priorities

| Priority | Count |
| --- | ---: |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

The complete machine-readable backlog is
`docs/main-board-unresolved-endpoints.csv`.

## ERC types

- `label_dangling`: 53

## Most affected references

- None.

## Release interpretation

Parity currently passes, but unconnected functional pins and ERC errors remain
release blockers. They must be traced, redesigned, or individually recorded as
intentional no-connects. This gate deliberately does not exclude or waive them.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
