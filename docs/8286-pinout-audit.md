# 8286 transceiver pinout audit

Status: **PHYSICAL PINOUT GUARDED**

The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns
A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.
Sheet 1 routes D107 and D23-D25 straight, permutes D4's high-address
channels, and permutes D29's eight command channels. Board pad endpoints
and per-instance LVS maps preserve those routes while HDL keeps ordered
logical buses. Factory sheets 1 and 3 prove that D100 instead buffers eight
floppy-drive outputs; its paired pads and shared pins 9/11 control
continuation are guarded here independently of the data-bus devices.

Primary pinout source:
`https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf`

## Checks

| Check | Result |
| --- | --- |
| D4 uses the Intel DIP-20 logical pin names | PASS |
| D4 address-channel pad assignments match sheet 1 | PASS |
| D107 uses the Intel DIP-20 logical pin names | PASS |
| D107 address-channel pad assignments match sheet 1 | PASS |
| D23 uses the Intel DIP-20 logical pin names | PASS |
| D23 address-channel pad assignments match sheet 1 | PASS |
| D24 uses the Intel DIP-20 logical pin names | PASS |
| D24 address-channel pad assignments match sheet 1 | PASS |
| D25 uses the Intel DIP-20 logical pin names | PASS |
| D25 address-channel pad assignments match sheet 1 | PASS |
| D29 uses the Intel DIP-20 logical pin names | PASS |
| D29 command-channel pads preserve owner-corrected IORD, IOWR, and D30.8 routes | PASS |
| D100 uses the Intel 8287 DIP-20 pin names | PASS |
| D100 drive-interface pad assignments follow factory sheet 3 | PASS |
| LVS type pinmap follows A0-A7 pins 1-8 and B0-B7 pins 19-12 | PASS |
| 8287 LVS type pinmap follows the same physical channel pairs | PASS |
| D100 LVS pinmap follows the complete 8287 contract | PASS |
| D4 LVS override preserves its routed high-address permutation | PASS |
| D29 LVS override preserves its routed command permutation | PASS |
| D7 pin 5 and D29 physical A2 pin 3 share the traced -INHIB source boundary | PASS |
| D7 pin 4 and D29 physical pin 1 share the traced MEMW conductor | PASS |
| D29 physical A1 pin 2 remains isolated from the qualified D105 pin 3 write rail | PASS |
