# D58 8282 latch pinout audit

Status: **PHYSICAL PINOUT GUARDED**

The Intel 8282 contract places DI0-DI7 on pins 1-8, OE on pin 9,
GND on pin 10, STB on pin 11, DO7-DO0 on pins 12-19, and +5 V on
pin 20. Sheet 2 uses D58 as the DRAM read-data latch from `RDO0-7`
to `DB0-7`; its OE and strobe remain separately traced boundaries.

Intel datasheet scan: `https://datasheet4u.com/datasheet-pdf/Intel/M8282/pdf.php?id=727746`

## Checks

| Check | Result |
| --- | --- |
| D58 declares the complete Intel 8282 DIP-20 pinout | PASS |
| D58 RDO/DB/control/power pad assignments match sheet 2 | PASS |
| LVS IR82 pinmap includes the complete package contract | PASS |
