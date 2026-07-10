# S4 interrupt boundary

Status date: 2026-07-10.

Status: **S4 INTERRUPT PATH GUARDED / SWITCH CONTINUITY PENDING**

This generated report isolates the external interrupt receive path
around S4. It guards the current X1 -> D3 -> D10 IR6/IR7 evidence
while keeping the two S4 switch pins as explicit source-read or
continuity work.

## Command

```sh
python3 scripts/report_s4_interrupt_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| S4 is present as the scanned interrupt-path switch | PASS | S4 provenance block |
| INT7 raw expansion input reaches D3 | PASS | `INT7_RAW`: X1.113B -> D3.13 |
| D3 buffered IR7 reaches PIC IR7 | PASS | `IR7`: D3.12 -> D10.25 |
| INT6 raw expansion input reaches D3 | PASS | `INT6_RAW`: X1.113C -> D3.1 |
| D3 buffered IR6 reaches PIC IR6 | PASS | `IR6`: D3.2 -> D10.24 |
| D3 and D10 package roles match the interrupt path | PASS | D3 inverter sections feed D10 PIC inputs |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| S4 pins remain unnetted until source/continuity proof | PASS | S4.1/S4.2 are known switch pins, but their exact insertion into IR6/IR7 remains pending |
| Do not infer S4 wiring from MAME or behavior | PASS | current model preserves the note but does not replace continuity evidence |

## Current Interrupt Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `INT7_RAW` | `D3.13, X1.113B` | scan |
| `IR7` | `D10.25, D3.12` | scan |
| `INT6_RAW` | `D3.1, X1.113C` | scan |
| `IR6` | `D10.24, D3.2` | scan |

## Interpretation

- The modeled interrupt path carries expansion `INT7`/`INT6` through D3
  inverter sections to PIC inputs IR7/IR6.
- S4 is physically present and associated with that path, but its two
  switch pins are deliberately not promoted into the netlist yet.
- Closing this boundary requires a sheet read, macro photo, or continuity
  check of S4.1/S4.2 on a .009 processor board.
