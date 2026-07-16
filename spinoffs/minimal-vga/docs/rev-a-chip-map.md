# Revision A chip map

This is the working physical decomposition for the experimental Rev A board.
It uses socketed DIP logic, +5 V parts, and test headers for DRAM-timing debug;
it is not a released manufacturing BOM.

## Core

| Ref | Function | Candidate part | Package | Notes |
|---|---|---|---|---|
| U1 | CPU | Z0840004PSC | DIP-40 | Owner-ordered 4 MHz Z80; factory mounts socket only. |
| U2 | ROM | 27C256-class EPROM, 28C256-compatible where possible | DIP-28 | 32 KiB ROM target for recovered firmware. |
| U5 | Decode glue | GAL22V10-class programmable logic | DIP-24 | Dual-mode decode; see the Decode PROMs section and `rev-a-gal-equations.md`. |

## Decode PROMs (Phase 3 — the workbench purpose)

These sockets exist to **test the scarce original Juku bipolar PROMs** in their
real functional roles; booting the firmware is the self-test.

| Ref | Juku role | Part | Package | Notes |
|---|---|---|---|---|
| U3 | D6 memory-map decode (`.038`) | К556РТ4 / 82S126-class 256×4 OC PROM | DIP-16 | Address `{A7=0,/PC1,/PC0,A11..A15}`; outputs O1..O4 = rom_n/ram_n/rev/roe_n. |
| U4 | D8 ROM-select pager (`.039`) | К155РЕ3 / SN74188-class 32×8 OC PROM | DIP-16 | Address `A[15:11]`; `/CE`=ROM_CE_N; outputs to J95 readback. |
| U6 | Port C mode-bit inverter | 74HC04 hex inverter | DIP-14 | 8255 PC0/PC1 → `/PC0,/PC1` for the РТ4 (two gates; rest tied off). |
| J94 | Decode-mode jumper | 1×3 header + shunt | TH | Mode A (GAL-internal decode, PROM sockets empty) vs Mode B (real РТ4 drives decode). |
| J95 | Decode-observability header | 1×14 header | TH | РТ4 outputs, РЕ3 byte, REV_OUT for the analyzer (Phase 4 readback). |
| R32-R35 | РТ4 output pull-ups | 4.7k | TH | Open-collector outputs need pull-ups (datasheet: fuse=1 reads high). |
| R36-R43 | РЕ3 output pull-ups | 4.7k | TH | Open-collector 8-bit output. |
| R44 | MODE_B default pull-down | 10k | TH | Floating/no-shunt defaults to Mode A (safe bring-up). |

**Buffered through the GAL, not into the enables directly.** The РТ4 (U3)
outputs route into U5, which applies the provisional `~D0`/`~D3` polarity
correction (root `PLAN.md` item 1) as a **reprogrammable GAL term** — when the
main-twin level probe resolves the polarity, the fix is a GAL reprogram, not a
board respin. The РЕ3 (U4) is enabled by ROM select and its output byte is only
**observed** (via J95): VJUGA's single 27C256 does not need the pager to gate
data, and the verified twin (`hdl/vjuga_juku_top.v`) likewise only *asserts* on
D8 rather than routing it into the data path.

**8255 Port C reconciliation.** The firmware writes the memory-map mode to Port C
bits 0-1 (I/O port `0x06`), so those bits (U30 pins 14/15 = PC0/PC1) are the mode
**output** feeding U6→U3. The keyboard-encoder readback therefore moves from Port C
lower (PC0-3) to Port C upper (PC4-7) — an 8255 mode-0 split (lower nibble output,
upper nibble input). PC2/PC3 are freed.

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
- Rev A uses western parts for the baseline (Mode A), and adds DIP sockets for
  the scarce original Juku bipolar PROMs (U3 РТ4, U4 РЕ3) that Mode B exercises;
  the DRAM sockets (U10-U17) take either KM4164B or К565РУ5. Soviet-part
  footprints are otherwise not preserved as a constraint for this spin-off.
- **The routed PCB (`rev-a-physical.kicad_pcb`) now matches the Phase 3 source.**
  It places/routes U3/U4/U6/J94-J98 and their passives and passes zero-violation,
  zero-unconnected KiCad DRC. The generated fab package still must be refreshed
  and independently reviewed before any order.
- A future assembly path may mount sockets/passives at the factory and insert
  vintage or programmed ICs later, but that path is blocked on functional
  proof and design review.
- The physical schematic should replace logical blocks one group at a time while
  keeping LVS green at each step.
