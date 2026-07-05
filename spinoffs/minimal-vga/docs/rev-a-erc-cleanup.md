# Rev A ERC cleanup

Status: current blocker list after the physical schematic started emitting
`VCC`, `GND`, and `VCC_RAW` nets.

Run:

```sh
spinoffs/minimal-vga/kicad/report_rev_a_erc_readiness.sh
```

Current result:

- 14 KiCad ERC error-level findings.
- 12 `pin_not_connected` findings.
- 2 `label_dangling` findings.
- Previous power-net noise is gone; the remaining list is now useful for Rev A
  schematic cleanup.

## Must Resolve Before Ordering

These are likely real electrical issues, not paperwork:

- `U41` pixel serializer `PIX_LOAD_N` needs to connect to the selected
  TTL640x480/timing-header boundary or be removed from Rev A.
- Dangling video label `BLANK_N` needs to connect to the selected
  TTL640x480/timing-header boundary or be removed from Rev A.

## Intentional No-Connect Candidates

These can probably become explicit KiCad no-connect markers once the final
bring-up/debug policy is confirmed:

- `U1` Z80 outputs `HALT_N` and `BUSACK_N` if they are not routed to debug
  headers.
- `U10`-`U17` DRAM pin 1. Common 4164-class DRAM documentation marks pin 1 as
  no-connect for compatibility; confirm against the actual KM4164B lot before
  marking it NC.
- `U31` 74148 `EO_N` is explicitly marked NC because the keyboard encoder is
  not cascaded in Rev A.
- Unused `74HCT393` counter outputs on `U22`; unused clear/clock inputs are
  now tied inactive where they are not part of the current topology.
- `U5` bus-buffer control outputs are explicitly marked NC because the optional
  data-bus buffer is deferred from the Rev A baseline.

## Topology Still Too Open

These findings mean the schematic is still carrying Rev A placeholders or
unfrozen glue logic. Do not silence them blindly:

- `U30` 8255: unused `PB*` and upper `PC*` pins should be assigned to keyboard
  behavior, diagnostic expansion, or explicit NC policy.
- `U41` pixel serializer and the `PIX*` labels are still coupled to the
  unfinished video bridge decision.

## Resolved In Source Model

- `U1` Z80 `INT_N`, `NMI_N`, and `BUSRQ_N` are tied inactive through the `VCC`
  net for Rev A.
- `U30` 8255 `RESET` is connected to the board reset net.
- `U41` pixel serializer `SER` and `INH` are tied inactive through `GND`.
- `U41` pixel clock now comes from the `PIXCLK` net instead of the board `CLK`
  net.
- Unused `U22`/`U23` counter clock/clear inputs are tied inactive through
  `GND`.
- `U5.RAM_CE_N` is connected to `U24.RAM_CE_N`.
- `U24.REFRESH_Q0`-`U24.REFRESH_Q3` are connected to the low refresh counter
  outputs.
- Intentional no-connect markers are generated for Z80 `HALT_N`/`BUSACK_N`,
  DRAM pin 1, GAL spare outputs, and non-cascaded `U31.EO_N`.
- `U23` high refresh/video counter outputs are explicitly marked NC because
  they are not consumed by the current Rev A timing model.
- `U24.DRAM_OE_N` is explicitly marked NC for Rev A. The selected 4164-class
  DRAM devices do not have an OE input; read output control is handled by the
  DRAM timing path, and this GAL output remains a reserved timing/debug signal.
- Optional placeholder sockets `U3` data-bus buffer, `U4` latch/buffer, and
  `U25` DRAM glue gates are removed from the Rev A physical source model and
  factory assembly rows. Rev A now routes the direct data bus and GAL-only
  decode/timing contract unless later verification proves extra glue is needed.

## Gate

ERC should become a hard fabrication gate only after the list above is reduced
to zero or to explicitly documented, intentionally marked no-connects.

## Source Notes

- Samsung KM4164B datasheet index:
  <https://www.alldatasheet.com/datasheet-pdf/pdf/102233/SAMSUNG/KM4164B.html>
- NTE4164 / generic 4164 datasheet mirror describing pin 1 as no internal
  connection:
  <https://www.farnell.com/datasheets/1905614.pdf>
