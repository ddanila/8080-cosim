# 8286 address-buffer pinout audit

Status: **PHYSICAL PINOUT GUARDED**

The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns
A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.
Sheet 1 routes D107 straight and deliberately permutes D4's high-address
channels. The board pad endpoints and per-instance LVS map preserve that
routing while HDL exposes ordered `A[15:0]`/`BA[15:0]` buses.

Primary pinout source:
`https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf`

## Checks

| Check | Result |
| --- | --- |
| D4 uses the Intel DIP-20 logical pin names | PASS |
| D4 address-channel pad assignments match sheet 1 | PASS |
| D107 uses the Intel DIP-20 logical pin names | PASS |
| D107 address-channel pad assignments match sheet 1 | PASS |
| LVS type pinmap follows A0-A7 pins 1-8 and B0-B7 pins 19-12 | PASS |
| D4 LVS override preserves its routed high-address permutation | PASS |
