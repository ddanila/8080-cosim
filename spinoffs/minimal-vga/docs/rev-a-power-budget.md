# Rev A Power Budget

This is a first-pass +5 V current budget for choosing the input fuse and supply
path. It is intentionally conservative until the exact socketed IC vendors are
frozen.

## Assumptions

- Supply rail: +5 V only after F1.
- CPU: real DIP Z80, budgeted as an NMOS Z0840004-class part.
- DRAM: eight 4164-compatible 64K x 1 DIP parts.
- ROM: 27C256-class EPROM/EEPROM.
- PPI: 82C55/8255-compatible DIP.
- GALs: two GAL22V10-class DIP devices.
- VGA output: worst case assumes RGB outputs can source current through the
  series resistors into a 75 ohm monitor load.
- LEDs: six diagnostics through 2.2k class resistors, so LED current is small.

## Estimated +5 V Current

| Block | Qty | Budget each | Budget total |
| --- | ---: | ---: | ---: |
| Z80 CPU | 1 | 200 mA | 200 mA |
| 4164 DRAM | 8 | 75 mA | 600 mA |
| 27C256 ROM | 1 | 50 mA | 50 mA |
| 82C55/8255 PPI | 1 | 100 mA | 100 mA |
| GAL22V10 | 2 | 90 mA | 180 mA |
| 74HCT glue logic | 9 | 10 mA | 90 mA |
| Oscillator | 1 | 25 mA | 25 mA |
| Reset supervisor and pullups | 1 | 5 mA | 5 mA |
| Diagnostic LEDs | 6 | 2 mA | 12 mA |
| VGA RGB load | 3 | 10 mA | 30 mA |
| Margin / sourcing variation | - | - | 250 mA |
| **Total planning budget** |  |  | **1.54 A** |

## Fuse Choice

Rev A currently uses `F1` as a resettable PTC fuse between `VCC_RAW` and `VCC`.
The assigned candidate is Littelfuse `RXEF300` / JLCPCB `C14397`.

- Hold current: 3 A at 20 C.
- Trip current: 6 A at 20 C.
- Role on Rev A: gross short / wiring fault protection, not precise load
  limiting.

This is comfortably above the 1.54 A planning budget and should avoid nuisance
trips during bring-up. It is still low enough to be useful for gross faults, but
trace width, connector rating, ambient temperature derating, and final IC choices
must be checked before ordering.

USB-C is kept as a convenience 5 V input. Without PD/current negotiation, do not
assume it can supply the full planning budget from every host/charger. The screw
terminal / bench supply path remains the safer primary bring-up input.
