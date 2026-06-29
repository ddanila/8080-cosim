# HDL side — structural model of the Juku E5104

This is the "digital schematic" we emulate **and** the reference the LVS checker
compares against the KiCad netlist. So it is written **structurally**: each module
instance is a real chip on the board, and the `wire`s are the board's nets
(address bus, data bus, control, chip-selects). Behavioral guts live inside the
device modules; the top is pure interconnect.

Derived from `../docs/hardware-map.md` (itself from MAME `ref/mame_juku.cpp`).

## Files
- `juku_top.v` — structural top: chip instances + bus wiring (the LVS target)
- `devices.v`  — device module *shells* (8255/8253/8251/1793/PIC/CPU/mem); to be
  filled with behavioral models for simulation. Ports/pin names are what matter
  for LVS; bodies are stubs for now.

## Chips (must 1:1 match KiCad refdes once the schematic exists)
| refdes (proposed) | chip | Verilog module |
|---|---|---|
| U_CPU | КР580ВМ80А (i8080A) | `cpu_8080` |
| U_ROM | 16 KB BIOS ROM | `rom_16k` |
| U_RAM0..19 | К565РУ5 (64K×1 DRAM) ×20 | `dram_64kx1` |
| U_PPI0/1 | КР580ВВ55А (8255) ×2 | `ppi_8255` |
| U_PIT0/1/2 | КР580ВИ53 (8253) ×3 | `pit_8253` |
| U_SIO0 | КР580ВВ51А (8251) | `usart_8251` |
| U_FDC | КР1818ВГ93 (WD1793) | `fdc_1793` |
| U_LATCH | КР580ИР82 (8282) | `latch_8282` |
| U_PIC | 8259 | `pic_8259` |

## I/O port decode (from the map)
4 ports per chip ⇒ A1:A0 = register select, A4:A2 = chip group select:
`0x00`→PIC, `0x04`→PPI0, `0x08`→SIO0, `0x0C`→PPI1, `0x10/14/18`→PIT0/1/2,
`0x1C`→FDC, `0x80`→mouse.

## Memory bank decode
4-mode ROM/RAM overlay selected by **PPI0 Port C[1:0]** (see hardware-map.md).
This is board glue logic — modelled here in `mem_decode`, to be matched against
the actual 74xx/PROM decode chips once they're in the schematic.

## Status
Skeleton: interconnect + module shells. Not yet simulable (device bodies are stubs;
no 8080 core vendored yet). Next: vendor an open Verilog 8080 core, fill RAM/ROM +
decode so a ROM image can at least be fetched and bus activity observed.
