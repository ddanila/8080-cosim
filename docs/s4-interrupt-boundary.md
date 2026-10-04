# S4 interrupt boundary

Status: **S4 INTERRUPT SELECTOR GUARDED**

This generated report isolates the external interrupt receive path
around S4. It guards the current X1 -> D3 -> D10 IR6/IR7 evidence
and preserves the full three-terminal S4 changeover topology.

## Command

Run from the repository root with Python 3 (standard library only).
The command reads `kicad/juku.board.json` and overwrites this report.

```sh
python3 scripts/report_s4_interrupt_boundary.py
```

A completed check writes its PASS/FAIL results before exiting; failed
checks return status 1. Inspect the exit status as well as the report.

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| S4 is present as the scanned interrupt-path switch | PASS | S4 provenance block |
| INT7 raw expansion input reaches D3 | PASS | `INT7_RAW`: X1.113B -> D3.13 |
| D3 buffered IR7 reaches PIC IR7 | PASS | `IR7`: D3.12 -> D10.25 |
| INT6 raw expansion input reaches D3 | PASS | `INT6_RAW`: X1.113C -> D3.1 |
| D3 buffered INT6 reaches the upper S4 throw | PASS | `INT6_BUF`: D3.2 -> S4.3 |
| S4 common reaches PIC IR6 | PASS | `IR6`: S4.2 -> D10.24 |
| USART SYNDET reaches the lower S4 throw | PASS | `SYNDET_S4`: D11.16 -> S4.1 |
| D3 and D10 package roles match the interrupt path | PASS | D3 complete hex-inverter contract; traced sections feed D10 PIC inputs |

## Source Contract Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| S4 retains a complete three-terminal SPDT contract | PASS | sheet-1 S4.1/S4.2 changeover symbol; all three electrical terminals assigned |
| Do not infer S4 wiring from MAME or behavior | PASS | current model preserves the note but does not replace continuity evidence |

## Current Interrupt Nets

Per-net provenance is retained in [the board model](../kicad/juku.board.json).

| Net | Endpoints |
| --- | --- |
| `INT7_RAW` | `D3.13, R9.1, X1.113B` |
| `IR7` | `D10.25, D3.12` |
| `INT6_RAW` | `D3.1, R10.1, X1.113C` |
| `INT6_BUF` | `D3.2, S4.3` |
| `SYNDET_S4` | `D11.16, S4.1` |
| `IR6` | `D10.24, S4.2` |

## Interpretation

- Expansion `INT7` continues through D3 directly to PIC IR7.
- Expansion `INT6` passes through D3 to one S4 throw; USART SYNDET feeds
  the other throw, and the common drives PIC IR6.
- This generator checks source endpoints, package roles and provenance
  markers. It does not run LVS, inspect routed copper or verify a fitted
  switch position by measurement.
- S4 is an off-board mechanical assembly with three modeled terminals.
  The HDL `spdt_switch` fixes the common to the external INT6 throw;
  runtime throw selection and switching behavior are not modeled.
