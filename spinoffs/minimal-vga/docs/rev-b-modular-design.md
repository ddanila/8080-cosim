# VJUGA rev B modular design

Rev B is a modular Z80/SRAM/VGA machine using the accepted Juku firmware
interfaces. It is independent of the monolithic Rev A and the faithful original
PCB reconstruction. The [five-board plan](rev-b-five-board-order-plan.md) controls
the first article; [status](rev-b-status.md) records its qualification boundary.

## Cards and backplane

| Design | Role | First-article PCB |
| --- | --- | --- |
| CPU | Z80, socketed 2.000 MHz clock, diagnostic header; unbuffered bus interface | 100×70 mm, two layers |
| Memory | 27C256 ROM, SRAM and ATF22V10 overlay decode | 100×60 mm, two layers |
| I/O | Sole 8251 UART, 8255 keyboard/mode control, PIC, D57-compatible PIT and independent POST display | 100×100 mm, two layers |
| Video | Local framebuffer SRAM, autonomous VGA timing, pixel shift, RGB drivers and CPU-access arbitration | 100×100 mm, four layers |
| Backplane | Five bus slots, protected 5 V input, reset authority and data-only TTL console boundary | 100×100 mm, two layers |

A future FDC card is outside this order. Minimal CPU/Memory/I/O population is a
staged diagnostic configuration; the complete first article includes Video.
Current mechanical qualification places Video in slot 5 with slot 4 empty.
Fitting a future FDC requires renewed mechanical qualification; the empty slot
is part of the first-article clearance arrangement.

## Bus and ownership

[The bus contract](rev-b-bus-contract.md) owns the exact pin tables, memory/I/O
maps, defaults and interrupt connections. The RC2014-compatible base uses 39
pins plus a separate ten-pin extension carrying `/WAIT`, `/NMI`, `/BUSRQ`,
`/BUSAK`, `/RFSH`, `/HALT`, two peripheral IRQ lines, power and ground.
All slots share the extension. This is not the vanilla 40-pin connector layout.

- CPU owns address/control and write data. Only the selected card drives read
  data; bus-conflict assertions check decode overlap and refresh behavior.
- Video owns RAM accesses at `0xD800–0xFFFF` in modes 0 and 3, with a
  9640-byte visible image (40×241) within the 10,240-byte CPU window.
  Memory serves the upper ROM overlay in modes 1 and 2; Video does not answer CPU accesses then. Scanout stays on Video-local
  SRAM in every mode.
- Video asserts open-drain `/WAIT` for CPU accesses that collide with scanout
  fetches. Phase sweeps and integrated CPU checks verify access completion.
- Video supplies `FRAME_TICK`; I/O supplies overlay MODE0/1. Backplane defaults
  the mode lines for boot when I/O is absent and owns shared-line pull-ups.
- Reset comes from the backplane. Peripheral interrupt requests terminate at
  the I/O PIC; serial-ready lines remain on-card.
- Protected barrel power is the sole input. USB-TTL supplies data, not board
  power. Parts, rail-drop and decoupling contracts are checked per card/system.

## Verification and physical boundary

Each first-article card has an HDL interface and bus-functional checks; the
assembled twin uses firmware byte-stream/framebuffer oracles. Independent pin/LVS checks,
programmable-logic rebuilds, DRC, exact-part guards, mechanics and package review
cover the implementation beyond the behavioral model. Use the
[execution guide](rev-b-execution-guide.md) for commands.

The assembled twin does not implement PIC interrupt service or keyboard
scanning; its scope is detailed in the [bus contract](rev-b-bus-contract.md#pic-interrupt-assignments).

Digital simulation does not prove physical bus timing, signal integrity or
assembled operation. Those require the staged first-article bench procedure.
The desk-qualified five-board candidate remains **ORDER HOLD** until explicit
owner upload authorization; ordering and payment have separate gates.

The [build contract](rev-b-build-plan.md) records durable decisions, and the
[Video adoption note](rev-b-video-adoption.md) records external timing concepts,
source identity and attribution. Generator-owned boards and qualification
contracts define the actual implementation.
