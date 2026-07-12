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
| ERC error violations | 52 | BLOCK |
| PCB/schematic parity issues | 0 | PASS |
| Explicit board-JSON no-connects | 67 | PASS |
| KiCad schematic no-connect markers | 67 | PASS |
| Functional pins without net or explicit NC | 52 | BLOCK |
| Unknown/conflicting NC records | 0 | PASS |

## Unresolved endpoint priorities

| Priority | Count |
| --- | ---: |
| P0 | 37 |
| P1 | 15 |
| P2 | 0 |

The complete machine-readable backlog is
`docs/main-board-unresolved-endpoints.csv`.

## ERC types

- `pin_not_connected`: 52

## Most affected references

- `D93`: 21
- `D99`: 12
- `D29`: 4
- `D26`: 4
- `D14`: 2
- `D39`: 2
- `D30`: 2
- `D11`: 2
- `R94`: 1
- `D13`: 1
- `S1`: 1

## Release interpretation

Parity currently passes, but unconnected functional pins and ERC errors remain
release blockers. They must be traced, redesigned, or individually recorded as
intentional no-connects. This gate deliberately does not exclude or waive them.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
