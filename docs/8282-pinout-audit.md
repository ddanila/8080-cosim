# D58 8282 latch pinout audit

Status: **PHYSICAL PINOUT GUARDED**

The Intel 8282 contract places DI0-DI7 on pins 1-8, OE on pin 9,
GND on pin 10, STB on pin 11, DO7-DO0 on pins 12-19, and +5 V on
pin 20. Sheet 2 uses D58 as the DRAM read-data latch from `RDO0-7`
to `DB0-7`. OE follows the source-closed D37.6 read gate; the remote
strobe source at `D58_STB_TAG5` remains unresolved. Runnable HDL ties
that strobe low through a simulation boundary.

Intel datasheet scan: `https://datasheet4u.com/datasheet-pdf/Intel/M8282/pdf.php?id=727746`

## Command

Run from the repository root with Python 3 (standard library only).
The command overwrites this report after its checks pass.

```sh
python3 scripts/report_8282_pinout_audit.py
```

## Checks

| Check | Result |
| --- | --- |
| D58 declares the complete Intel 8282 DIP-20 pinout | PASS |
| D58 RDO/DB/control/power pad assignments match sheet 2 | PASS |
| LVS IR82 pinmap includes the complete package contract | PASS |

## Scope

This guard compares D58's source-model pin contract, net assignments and
the LVS type map with fixed expected values. It does not run LVS, inspect
PCB copper, exercise latch behavior or establish the missing strobe source.
