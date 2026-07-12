# S4 interrupt boundary

Status date: 2026-07-10.

Status: **S4 INTERRUPT SELECTOR GUARDED**

This generated report isolates the external interrupt receive path
around S4. It guards the current X1 -> D3 -> D10 IR6/IR7 evidence
and preserves the full three-terminal S4 changeover topology.

## Command

```sh
python3 scripts/report_s4_interrupt_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| S4 is present as the scanned interrupt-path switch and remains schematic/off-board | PASS | S4 provenance block; `.009` PCB assembly sheet has no S4 footprint |
| INT7 raw expansion input reaches D3 | PASS | `INT7_RAW`: X1.113B -> D3.13 |
| D3 buffered IR7 reaches PIC IR7 | PASS | `IR7`: D3.12 -> D10.25 |
| INT6 raw expansion input reaches D3 | PASS | `INT6_RAW`: X1.113C -> D3.1 |
| D3 buffered INT6 reaches the upper S4 throw | PASS | `INT6_BUF`: D3.2 -> S4.3 |
| S4 common reaches PIC IR6 | PASS | `IR6`: S4.2 -> D10.24 |
| USART SYNDET reaches the lower S4 throw | PASS | `SYNDET_S4`: D11.16 -> S4.1 |
| D3 and D10 package roles match the interrupt path | PASS | D3 complete hex-inverter contract; traced sections feed D10 PIC inputs |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| S4 retains a complete three-terminal SPDT contract | PASS | sheet-1 S4.1/S4.2 changeover symbol; all three electrical terminals assigned |
| Do not infer S4 wiring from MAME or behavior | PASS | current model preserves the note but does not replace continuity evidence |

## Current Interrupt Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `INT7_RAW` | `D3.13, X1.113B` | scan |
| `IR7` | `D10.25, D3.12` | scan |
| `INT6_RAW` | `D3.1, X1.113C` | scan |
| `INT6_BUF` | `D3.2, S4.3` | scan sheet-1: D3.2 buffered -INT6 reaches the upper S4.2 throw |
| `SYNDET_S4` | `D11.16, S4.1` | scan sheet-1: D11 SYNDET pin 16 reaches the lower S4.1 throw |
| `IR6` | `D10.24, S4.2` | scan sheet-1: S4 changeover common drives D10 IR6 |

## Interpretation

- Expansion `INT7` continues through D3 directly to PIC IR7.
- Expansion `INT6` passes through D3 to one S4 throw; USART SYNDET feeds
  the other throw, and the common drives PIC IR6.
- The exact fitted switch position affects behavior but no longer leaves
  any copper endpoint or switch terminal omitted from the source PCB.
