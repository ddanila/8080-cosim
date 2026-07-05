# Rev A ERC cleanup

Status: current blocker list after the physical schematic started emitting
`VCC`, `GND`, and `VCC_RAW` nets.

Run:

```sh
spinoffs/minimal-vga/kicad/report_rev_a_erc_readiness.sh
```

Current result:

- 93 KiCad ERC error-level findings.
- 88 `pin_not_connected` findings.
- 5 `label_dangling` findings.
- Previous power-net noise is gone; the remaining list is now useful for Rev A
  schematic cleanup.

## Must Resolve Before Ordering

These are likely real electrical issues, not paperwork:

- `U1` Z80 active-low inputs: `INT_N`, `NMI_N`, and `BUSRQ_N` must not float.
  Add pullups or explicit fixed ties if Rev A does not use interrupts or bus
  request.
- `U30` 8255 `RESET` should connect to the board `RESET_N` policy through the
  correct polarity path.
- `U41` pixel serializer inputs `SER` and `INH` need defined levels if the
  serializer stays in Rev A.
- Dangling video labels `PIXCLK`, `BLANK_N`, and `PIX_LOAD_N` need to connect
  to the selected TTL640x480/timing-header boundary or be removed from Rev A.
- `U24` DRAM sequencer pins that represent required timing signals
  (`RAM_CE_N`, `REFRESH_Q0`-`REFRESH_Q3`, `DRAM_OE_N`) must match the final GAL
  equations and board wiring.

## Intentional No-Connect Candidates

These can probably become explicit KiCad no-connect markers once the final
bring-up/debug policy is confirmed:

- `U1` Z80 outputs `HALT_N` and `BUSACK_N` if they are not routed to debug
  headers.
- `U10`-`U17` DRAM pin 1. Common 4164-class DRAM documentation marks pin 1 as
  no-connect for compatibility; confirm against the actual KM4164B lot before
  marking it NC.
- `U31` 74148 `EO_N` if the keyboard encoder is not cascaded.
- Unused `74HCT393` counter outputs on `U22`/`U23`; unused clear/clock inputs
  still need defined levels, not NC.

## Topology Still Too Open

These findings mean the schematic is still carrying Rev A placeholders or
unfrozen glue logic. Do not silence them blindly:

- `U3` `74HCT245`: the B-side bus pins are unconnected while the buffer policy
  is still optional.
- `U4` `74HCT573`: the entire latch/buffer body is unconnected; either wire the
  address/data latch role or remove the footprint from Rev A.
- `U25` `74HCT00`: all NAND gates are currently unused; split/replace it after
  the DRAM equations settle.
- `U30` 8255: unused `PB*` and upper `PC*` pins should be assigned to keyboard
  behavior, diagnostic expansion, or explicit NC policy.
- `U41` pixel serializer and the `PIX*` labels are still coupled to the
  unfinished video bridge decision.

## Gate

ERC should become a hard fabrication gate only after the list above is reduced
to zero or to explicitly documented, intentionally marked no-connects.

## Source Notes

- Samsung KM4164B datasheet index:
  <https://www.alldatasheet.com/datasheet-pdf/pdf/102233/SAMSUNG/KM4164B.html>
- NTE4164 / generic 4164 datasheet mirror describing pin 1 as no internal
  connection:
  <https://www.farnell.com/datasheets/1905614.pdf>
