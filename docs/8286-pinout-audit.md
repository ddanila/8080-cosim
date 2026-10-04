# 8286 transceiver pinout audit

Status: **PHYSICAL PINOUT GUARDED**

The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns
A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.
Sheet 1 routes D107 and D23-D25 straight, permutes D4's high-address
channels, and permutes D29's eight command channels. The exact .009
D29 row transcription is in `ref/schematics/d29-exact-009-pinmap-review.json`;
the command rows match the exact .009 source map. Other checked
pad endpoints and per-instance LVS maps use ordered logical buses.
Factory sheets 1 and 3 prove that D100 instead buffers eight
floppy-drive outputs. Its paired channels and separate pin-9 OE_N and
pin-11 T nets are guarded independently of the data-bus devices.

Primary pinout source:
`https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf`

## Command

```sh
python3 scripts/report_8286_pinout_audit.py
```

## Checks

| Check | Result |
| --- | --- |
| D4 uses the Intel DIP-20 logical pin names | PASS |
| D4 channel pad assignments match sheet 1 | PASS |
| D107 uses the Intel DIP-20 logical pin names | PASS |
| D107 channel pad assignments match sheet 1 | PASS |
| D23 uses the Intel DIP-20 logical pin names | PASS |
| D23 channel pad assignments match sheet 1 | PASS |
| D24 uses the Intel DIP-20 logical pin names | PASS |
| D24 channel pad assignments match sheet 1 | PASS |
| D25 uses the Intel DIP-20 logical pin names | PASS |
| D25 channel pad assignments match sheet 1 | PASS |
| D29 uses the Intel DIP-20 logical pin names | PASS |
| D29 physical input/output pads match all eight exact .009 sheet-1 rows | PASS |
| D100 uses the Intel 8287 DIP-20 pin names | PASS |
| D100 drive-interface pad assignments follow factory sheet 3 | PASS |
| LVS type pinmap follows A0-A7 pins 1-8 and B0-B7 pins 19-12 | PASS |
| 8287 LVS type pinmap follows the same physical channel pairs | PASS |
| D100 LVS pinmap follows the complete 8287 contract | PASS |
| D4 LVS override preserves its source high-address permutation | PASS |
| D29 LVS override preserves its source command permutation | PASS |
| D7 pin 5 and D29 physical A2 pin 3 share the traced -INHIB source boundary | PASS |
| D7 pin 4 and D29 physical pin 8 share the exact -MWR conductor | PASS |
| D7 pin 3 joins D29 physical pin 2 but remains separate from qualified /WR | PASS |

## Scope

This guard compares the listed main-board source contracts, net endpoints
and LVS mapping data with fixed pinout/channel expectations. It does not
run LVS, inspect routed copper, simulate turnaround timing or measure
physical continuity. D100 control and remote-source boundaries remain
subject to the [FDC handoff](fdc-hardware-handoff.md).
