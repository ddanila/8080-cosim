# Revision A target

Revision A is a small, +5V-first proof board.

## Goal

Prove that a simplified Z80-based board can run through ROM/RAM/IO cycles while
the memory side is shaped to accept the original-style Juku DRAM refresh and
video arbitration work.

## Included

- Z80 CPU boundary, modeled by T80 `T80se`.
- Native Z80 bus adapter for the first prototype.
- ROM decode at `0x0000`.
- RAM decode at `0x8000` for the first synthetic test, expanding toward the Juku
  map later.
- IO write/read strobe path.
- Future block placeholders for:
  - 4164/K565RU5-compatible DRAM bank.
  - keyboard decode.
  - VGA timing bridge.

## Not Yet Included

- Real Juku ROM boot.
- Full original-style DRAM RAS/CAS cycle generator attached to the CPU bus.
- Full keyboard matrix scan.
- VGA pixel output sourced from Juku video memory.

Those are the next layers after the CPU/ROM/RAM/IO smoke test is stable.

## Current Simulator Milestone

The first runnable top now proves:

- T80 `T80se` fetches and executes synthetic ROM code.
- A write/read round trip goes through a bit-sliced 4164-style RAM bank.
- CPU RAM accesses go through a row/column DRAM sequencer with RAS/CAS phases.
- An independent refresh sequencer ticks without using Z80 `RFSH` as the refresh
  source.
- Periodic video reads arbitrate for the same DRAM path as CPU and refresh.
- A keyboard-style IO read path is visible.
- VGA timing completes at least one frame.
- The spin-off structural HDL and generated KiCad schematic pass LVS through the
  real `kicad-cli` netlist export path.
