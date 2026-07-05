# Revision A chip map

This is the working physical decomposition for the first manufacturable
spin-off board. It intentionally starts conservative: socketed DIP logic, +5V
western parts, and enough test headers to debug DRAM timing.

## Core

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U1 | CPU | Z0840004PSC | DIP-40 | Owner-ordered 4 MHz Z80; factory mounts socket only. |
| U2 | ROM | 27C256-class EPROM, 28C256-compatible where possible | DIP-28 | 32 KiB ROM target for recovered firmware. |
| U5 | Decode glue | GAL22V10-class programmable logic | DIP-24 | Use GAL/PAL-style logic for Rev A iteration. |

## DRAM And Arbitration

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U10-U17 | 64K x 1 DRAM bits D0-D7 | KM4164B-10 | DIP-16 | Owner-ordered Samsung 4164-compatible 100 ns DRAM; factory mounts sockets only. |
| U20-U21 | Row/column address mux | 74HCT157/257-class | DIP-16 | CPU/video/refresh address selection. |
| U22 | Refresh/video counter low | 74HCT393/4040/161-class | DIP | Exact topology still open. |
| U23 | Refresh/video counter high | 74HCT393/4040/161-class | DIP | Exact topology still open. |
| U24 | RAS/CAS/WE sequencer | GAL22V10-class programmable logic | DIP-24 | GAL/PAL-style timing logic for first Rev A. |

## Keyboard

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U30 | PPI | 82C55 / 8255-compatible | DIP-40 | Column select and keyboard control. |
| U31 | Row priority encoder | 74HCT148 | DIP-16 | Mirrors Juku/MAME keyboard decode model. |
| J30 | Keyboard connector | 1x15 2.54 mm inline header | TH | Bring-up wiring point for original keyboard: 8 columns plus 7 rows, no keyboard power pins. |
| R7-R14 | Keyboard row pullups | 10k | TH | Pull active-low row inputs high. |
| R15 | Keyboard encoder enable | 0 ohm link | TH | Ties 74148 enable active by default. |
| R16-R23 | Keyboard column conditioning | 220 ohm | TH | Series resistors between 8255 outputs and connector. |

## Video/VGA

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U40 | VGA timing block | TTL640x480 bring-up timing header | 2x6 2.54 mm header | Rev A proves CPU/DRAM/refresh/video handoff first; exports PIXCLK, sync, blanking, video request/ack, and pixel-load timing. Full onboard TTL VGA expansion is deferred. |
| U41 | Pixel latch/serializer | 74HCT165/166/595-class | DIP | Byte-to-pixel path driven by U40 timing signals for Rev A bring-up. |
| J40 | VGA output/debug | 1x7 2.54 mm header | TH | RGB after series resistors plus HSYNC/VSYNC/GND and BLANK_N; HD-15 adapter is external for Rev A. |

## Power, Clock, Reset, Debug

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| J1 | +5V input | 2-pin 5.00 mm terminal/header | TH | Feeds VCC_RAW before F1; alternate input to USB-C. |
| J3 | USB-C +5V input | HRO TYPE-C-31-M-17-compatible receptacle | SMD/THT shell | Power-only USB-C input in parallel with J1 before F1. |
| R30-R31 | USB-C CC pulldowns | 5.1k | TH | Rd pulldowns from CC1/CC2 to GND for 5V sink behavior. |
| F1 | +5V input fuse | resettable PTC fuse | TH | VCC_RAW from J1/J3 feeds fused VCC through F1. |
| D1 | +5V clamp | TVS diode | TH | Fused VCC clamp near power entry. |
| U50 | Clock oscillator | canned oscillator | DIP-14/half-can | CPU clock and/or divided timing source. |
| U51 | Reset supervisor | MCP130-class or RC+Schmitt | TO-92/SOT/DIP | Prefer deterministic reset. |
| J90-J93 | Logic analyzer/debug headers | 2.54 mm headers | TH | Address/data/RAS/CAS/WE/sync/power debug; J93 exposes VCC/GND/PWR_OK/VCC_RAW. |
| D2-D7 | Diagnostic LEDs | 3 mm LEDs | TH | +5V, PWR_OK, CLK, RESET_N, M1_N, and RFSH_N bring-up indicators. |
| R24-R29 | Diagnostic LED resistors | 2.2k | TH | Conservative current limit to reduce logic loading. |
| C* | Decoupling | 100 nF ceramic | TH/SMD | One per IC, close to socket power pins. |

## Current Modeling Status

- `minimal_vga_lvs.v` still uses logical blocks for adapter, DRAM bank,
  refresh, keyboard, VGA timing, and video fetch.
- `../kicad/rev-a-physical.board.json` is the first generated physical
  schematic target using this decomposition.
- `../kicad/rev-a-physical.kicad_sch` is generated from that target.
- The Rev A physical spec now uses real DIP pin numbers for Z80, 28C256, 4164,
  8255, and the selected 74xx support sockets. GAL and header pins are still
  design-assigned until equations and connector pinouts are frozen.
- The optional CPU bus buffer, address latch/buffer, and extra DRAM control
  gates are not populated in the Rev A baseline. The current board routes the
  direct Z80 data bus and GAL-based decode/timing contract; add those sockets
  back only if simulator or hardware bring-up proves they are needed.
- Rev A should use western parts only; Soviet-part footprints are not preserved
  as a constraint for this spin-off.
- Factory assembly is the intended manufacturing target, with sockets/passives
  mounted by the assembler where practical and vintage ICs inserted after
  assembly.
- The physical schematic should replace logical blocks one group at a time while
  keeping LVS green at each step.
