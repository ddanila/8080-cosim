# Main-board ERC and schematic/PCB parity

Status: **READY**

ERC uses a generated include-power schematic under `fab/audit`; the normal
LVS schematic deliberately omits power nets. Parity uses `juku.kicad_sch`
and the same-basename source `juku.kicad_pcb`. The routed PCB is a derived
artifact; KiCad cannot run
schematic parity against it without a matching routed schematic/project.

## Summary

| Check | Count | Result |
| --- | ---: | --- |
| ERC error violations | 0 | PASS |
| PCB/schematic parity issues | 0 | PASS |
| Explicit board-JSON no-connects | 65 | PASS |
| KiCad schematic no-connect markers | 65 | PASS |
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

- None.

## Most affected references

- None.

## Release interpretation

ERC, parity, endpoint ownership, and explicit no-connect accounting all pass.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
