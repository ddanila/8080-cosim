# Package endpoint coverage

Status: **DECLARED NON-POWER ENDPOINTS VALIDATED**

This guard reads `kicad/juku.board.json`. For net endpoints whose references
exist in `chips`, it rejects undeclared pins unless the net is tagged `power`.
It also rejects explicit no-connects absent from the chip pin contract.

## Command

Run from the repository root with Python 3 (standard library only).
The generator overwrites this report after all checks pass; failure exits
nonzero before writing a new report.

```sh
python3 scripts/report_package_endpoint_coverage.py
```

## Summary

- Undeclared non-power endpoints: `0`
- Undeclared explicit no-connect pins: `0`
- Power endpoints outside board pin contracts: `119` across `58` refs

| Tagged power net | Endpoints outside board pin contracts |
| --- | ---: |
| `GND` | 59 |
| `M12V` | 2 |
| `P12V` | 2 |
| `P5V` | 56 |

## Checks

| Check | Result |
| --- | --- |
| Every known-chip non-power net endpoint is declared by its chip/package | PASS |
| Every explicit no-connect exists in its chip/package | PASS |
| S1 off-board SPDT contact 3 is explicitly declared | PASS |
| Remaining undeclared endpoints belong only to tagged PCB power nets | PASS |

## Scope

- Net endpoints with references absent from `chips` are skipped. Explicit
  no-connects with unknown references are rejected.
- This check does not find required pins omitted from both nets and
  no-connects, validate package pin functions, or inspect HDL pinmaps.
- Tagged power-net exceptions are counted; their voltage, routing and
  electrical suitability are not validated here.
- Spinoff boards, routed copper and physical continuity are outside this
  report. Use their own package, LVS and manufacturing checks.
