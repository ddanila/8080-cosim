# Main-board ERC and schematic/PCB parity

Status: **DESIGN HOLD**

ERC uses a generated include-power schematic under `fab/audit`; the normal
LVS schematic deliberately omits power nets. Parity uses `juku.kicad_sch`
and the same-basename source `juku.kicad_pcb`. The routed PCB is a derived
artifact; KiCad cannot run schematic parity against it without a matching
routed schematic/project. Direct board-JSON pad-net checks cover each
modeled endpoint whose reference has a footprint on the source PCB or
either routed variant. A separate check catches modeled source-PCB pads
missing from a routed variant; off-board connectors are outside both checks.

## Summary

| Check | Count | Result |
| --- | ---: | --- |
| Raw ERC error violations | 0 | GUARDED |
| Unexpected ERC/mapping findings | 0 | PASS |
| Singleton-label ERC mode | suppressed (0 / 34) | PASS |
| Source-risk singleton nets | 23 | BLOCK |
| Other source-risk nets | 24 | BLOCK |
| PCB/schematic parity issues | 0 | PASS |
| Board-JSON/source-PCB pad-net mismatches | 0 | PASS |
| Board-JSON/juku_routed.kicad_pcb pad-net mismatches | 0 | PASS |
| Board-JSON/juku_routed_candidate.kicad_pcb pad-net mismatches | 0 | PASS |
| Source-PCB modeled endpoints missing from juku_routed.kicad_pcb | 4 | BLOCK |
| Source-PCB modeled endpoints missing from juku_routed_candidate.kicad_pcb | 4 | BLOCK |
| Explicit board-JSON no-connects | 63 | PASS |
| KiCad schematic no-connect markers | 63 | PASS |
| Functional pins without net or explicit NC | 0 | PASS |
| Duplicate board-JSON endpoint memberships | 0 | PASS |
| Unknown/conflicting NC records | 0 | PASS |

KiCad versions either report one `label_dangling` error for every
one-endpoint local-label net or suppress that complete warning class. The
gate accepts only those two exact modes; partial reporting fails. The
board-JSON singleton census remains the authoritative modeled boundary
surface in either mode.
Of those `34` singleton nets, `23` remain source-risk
boundaries and `11` have closed or intentional dispositions.

## Unresolved endpoint priorities

| Priority | Count |
| --- | ---: |
| P0 | 1 |
| P1 | 21 |
| P2 | 1 |

The complete machine-readable singleton-endpoint backlog is
`docs/main-board-unresolved-endpoints.csv`.

## ERC types

- None.

## Most affected references

- None.

## Release interpretation

Source-PCB modeled endpoints missing from juku_routed.kicad_pcb:

- `R10.1`
- `R10.2`
- `R9.1`
- `R9.2`

Source-PCB modeled endpoints missing from juku_routed_candidate.kicad_pcb:

- `R10.1`
- `R10.2`
- `R9.1`
- `R9.2`

Singleton-label ERC reporting is in the exact `suppressed` mode, and
source-PCB parity and endpoint ownership pass. Routed pad-net mismatches,
missing routed endpoints, and source-risk nets remain release blockers.
They must be traced, redesigned, or individually given an evidence-backed
disposition. This gate does not suppress the singleton labels or convert them
to no-connects merely to obtain a zero-error ERC count.

Raw machine-readable reports:

- `fab/audit/main-board-erc.json`
- `fab/audit/main-board-parity-drc.json`
