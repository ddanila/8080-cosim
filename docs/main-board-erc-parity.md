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
| ERC error violations | 260 | BLOCK |
| PCB/schematic parity issues | 0 | PASS |
| Explicit board-JSON no-connects | 19 | FAIL |
| KiCad schematic no-connect markers | 17 | FAIL |
| Functional pins without net or explicit NC | 260 | BLOCK |
| Unknown/conflicting NC records | 0 | PASS |

## Unresolved endpoint priorities

| Priority | Count |
| --- | ---: |
| P0 | 168 |
| P1 | 92 |
| P2 | 0 |

The complete machine-readable backlog is
`docs/main-board-unresolved-endpoints.csv`.

## ERC types

- `pin_not_connected`: 260

## Most affected references

- `D93`: 21
- `D97`: 14
- `D102`: 14
- `D106`: 14
- `D95`: 14
- `D101`: 14
- `D99`: 12
- `D28`: 12
- `D98`: 12
- `D96`: 11
- `D41`: 10
- `D40`: 9
- `D34`: 8
- `D35`: 7
- `D13`: 7
- `D7`: 6
- `D52`: 6
- `D10`: 6
- `D56`: 5
- `D43`: 5

## Release interpretation

Parity currently passes, but unconnected functional pins and ERC errors remain
release blockers. They must be traced, redesigned, or individually recorded as
intentional no-connects. This gate deliberately does not exclude or waive them.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
