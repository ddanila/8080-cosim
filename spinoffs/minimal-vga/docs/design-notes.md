# Design notes

## Board philosophy

This is not a smaller clone layout. It is a smaller behavioral-compatible board.

Constraints we keep:

- Firmware-visible memory map and I/O behavior should match the original enough
  to run the Juku ROMs.
- CPU, ROM, DRAM, refresh/timing, and keyboard decode should stay close to the
  original schematic where known.
- The design must remain simulatable and LVS-checkable.

Constraints we drop:

- Original 2-layer routing.
- Original physical placement.
- Full peripheral population.
- RF/composite monitor output.

## Minimal functional blocks

Core:

- CPU: Z80 first, with a future adapter path toward Juku/8080-style control
  cycles.
- CPU bus support:
  - option 1: native Z80 `MREQ`/`IORQ`/`RD`/`WR` adapter;
  - option 2: adapter that translates Z80 cycles into the original-style Juku
    memory/IO strobes.
- ROM: use `../../roms/ekta37.bin` first; allow multi-ROM mapping later.
- RAM: one 64K x 8 DRAM bank from eight western 4164-compatible 64K x 1
  chips.
- Decode: memory decode PROM behavior from the main project.

Keyboard:

- 8255 PPI0-compatible column select.
- 74148-compatible row priority encoder.
- Matrix mapping from the main project/MAME transcription.

Video:

- Preserve Juku DRAM/video arbitration where needed for firmware compatibility.
- Use onboard TTL640x480-derived logic for VGA sync/blanking.
- Define a small interface between Juku video data and the VGA timing block:
  `pixel_on`, `hsync`, `vsync`, `blank`, and optional RGB resistor DAC lines.

Power:

- Simple +5V input via 2-pin terminal/header and optional power-only USB-C.
- Rev A active logic is +5V-only with a real DIP Z80 CPU.
- Multi-layer power/ground planes allowed.

## Simulation plan

Use three levels:

1. Existing oracle: `../../sync/boot_check.sh`.
2. Z80-native minimal-top boot: compile the spin-off HDL top once created and
   prove ROM/RAM/keyboard progress.
3. VGA-visible test: assert that the VGA-side output renders expected prompt or
   banner pixels/characters after boot.
4. Juku-adapter test: swap only the CPU bus adapter and compare DRAM/video
   externally visible behavior against the Z80-native top.

The first HDL top may keep behavioral RAM while we remove unused peripherals.
After that, the K565RU5 row/column model from `../../hdl/sim/dram_unit_tb.v`
should be wired into the minimal top.

## Adapter boundary

Keep the first Z80 version simple, but put all CPU-specific behavior behind one
boundary:

```text
Z80 core
  -> cpu_bus_adapter
  -> mem_io_request bus
  -> ROM / DRAM controller / keyboard PPI / VGA bridge
```

The `mem_io_request` side should describe intent, not Z80 pins:

- address
- data out
- data in
- memory read
- memory write
- IO read
- IO write
- interrupt acknowledge, if needed
- wait/ready

That makes option 2 a replacement of `cpu_bus_adapter`, not a rewrite of the
DRAM or video subsystem.

## Remaining Decisions

- Whether T80 `T80se` bus timing is close enough for the first boot target
  before the adapter is hardened.
- Whether to keep the original 8253/PIC frame interrupt path if the chosen ROM
  command path needs it for keyboard scanning.
- Whether VGA should read directly from shared DRAM or from a shadow/latch stage
  populated by original-style video reads.
- Exact USB-C/terminal input part selection and current budget.
- How much of the original timing PROM behavior must be physically reproduced
  versus collapsed into equivalent TTL/PROM logic.

Resolved Rev A policy:

- Use western parts only for the spin-off.
- Use a real socketed DIP Z80, 27C256-class ROM, western 4164-compatible DRAM,
  and GAL/PAL-style programmable logic for the first physical decode/timing
  iteration.
- Target factory assembly of passives, sockets, connectors, and protection
  parts where practical.
