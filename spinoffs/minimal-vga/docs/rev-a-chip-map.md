# Revision A chip map

This is the working physical decomposition for the first manufacturable
spin-off board. It intentionally starts conservative: socketed DIP logic, +5V
parts, and enough test headers to debug DRAM timing.

## Core

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U1 | CPU | Z80 CPU CMOS/NMOS compatible | DIP-40 | +5V first prototype CPU. |
| U2 | ROM | 28C256 or 27C256-class ROM/EEPROM | DIP-28 | Start with adapter-friendly EEPROM if possible. |
| U3 | CPU bus/data buffer | 74HCT245 | DIP-20 | Optional if direct bus loading is acceptable; keep footprint in Rev A. |
| U4 | Address latch/buffer | 74HCT573 or 74HCT244 | DIP-20 | Exact need depends on final timing. |
| U5 | Decode glue | GAL16V8/GAL22V10 or 74HCT138/00/32 | DIP | Prefer GAL for Rev A iteration; replace with TTL later if desired. |

## DRAM And Arbitration

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U10-U17 | 64K x 1 DRAM bits D0-D7 | 4164-compatible | DIP-16 | Direct analogue for K565RU5-style testing. |
| U20-U21 | Row/column address mux | 74HCT157/257-class | DIP-16 | CPU/video/refresh address selection. |
| U22 | Refresh/video counter low | 74HCT393/4040/161-class | DIP | Exact topology still open. |
| U23 | Refresh/video counter high | 74HCT393/4040/161-class | DIP | Exact topology still open. |
| U24 | RAS/CAS/WE sequencer | GAL16V8/GAL22V10 or PROM+TTL | DIP | Functional replacement for first Rev A. |
| U25 | DRAM control gates | 74HCT00/02/08/32 as needed | DIP | Split once equations settle. |

## Keyboard

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U30 | PPI | 82C55 / 8255-compatible | DIP-40 | Column select and keyboard control. |
| U31 | Row priority encoder | 74HCT148 | DIP-16 | Mirrors Juku/MAME keyboard decode model. |
| J30 | Keyboard connector | TBD | TH | Pinout decision open. |
| R7-R14 | Keyboard row pullups | 10k | TH | Pull active-low row inputs high. |
| R15 | Keyboard encoder enable | 0 ohm link | TH | Ties 74148 enable active by default. |
| R16-R23 | Keyboard column conditioning | 220 ohm | TH | Series resistors between 8255 outputs and connector. |

## Video/VGA

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U40 | VGA timing block | TTL640x480-derived logic or header | Mixed | Start as header or redraw TTL640x480 block. |
| U41 | Pixel latch/serializer | 74HCT165/166/595-class | DIP | Exact byte-to-pixel path still open. |
| J40 | VGA connector | HD-15 or pin header | TH | Include resistor DAC network near connector. |

## Power, Clock, Reset, Debug

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| J1 | ATX power input | ATX 20/24-pin or adapter header | TH | Rev A uses +5V only unless otherwise needed. |
| F1 | +5V input fuse | resettable PTC fuse | TH | ATX +5V enters as VCC_RAW and feeds VCC through F1. |
| D1 | +5V clamp | TVS diode | TH | Fused VCC clamp near power entry. |
| J2 | ATX enable | 2-pin jumper/header | TH | Short PS_ON_N to GND to request supply on. |
| U50 | Clock oscillator | canned oscillator | DIP-14/half-can | CPU clock and/or divided timing source. |
| U51 | Reset supervisor | MCP130-class or RC+Schmitt | TO-92/SOT/DIP | Prefer deterministic reset. |
| J90-J93 | Logic analyzer/debug headers | 2.54 mm headers | TH | Address/data/RAS/CAS/WE/sync/power debug. |
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
- The physical schematic should replace logical blocks one group at a time while
  keeping LVS green at each step.
