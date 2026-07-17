# Shared commons — generic Juku ↔ spin-offs

Contract for what is shared between the main Juku reconstruction (root) and the
spin-offs (`spinoffs/minimal-vga/` rev A, rev B boards, and anything later), so
that knowledge and findings flow **automatically**, not by copy-paste.

## Principle
**Root is the single source of truth; spin-offs consume, never fork.** A finding
made anywhere (bench, owner measurement, PROM dump, twin calibration) lands in
the root artifact first; spin-offs pick it up through derivation or a guard —
a spin-off must never carry a hand-maintained copy of a root fact.

## The commons inventory (what is shared, where truth lives)

| Commons | Truth location | Spin-offs consume via |
|---|---|---|
| Behavioral oracle | `cosim/` (C emulator) + golden `vram*.bin` | boot/framebuffer comparison — already the rev A/B gate |
| Firmware images | `roms/` (ekta37 etc.) | derived images only (e.g. `make_z80_rom.c` builds `ekta37_z80.bin`); derived files are build products, never edited |
| PROM/silicon truth | `proms/` dumps, `ref/reconstructed-proms/`, D6/D8 tables | GAL equations and decode models are *derived from* these tables |
| Machine facts (map, ports, timing) | **`ref/juku-machine-facts.json`** (to create — see below) | testbenches, docs, and card specs read the same file |
| Owner/bench measurements | `docs/owner-measured-facts.md` and per-topic docs | referenced, never restated with different numbers |
| Shared HDL device models | root `hdl/` (FDC, PIC/intr, devices) | spin-off twins instantiate root models where the device is the same silicon |
| Bring-up method | rev A docs (NOP plug, J95 observability, FB-readback oracle) | rev B inherits by reference (`rev-b-build-plan.md` S9) |

## The new artifact: `ref/juku-machine-facts.json`
One machine-readable file holding the facts every consumer currently repeats in
prose: memory map (ROM/RAM/overlay modes, framebuffer `0xD800`+9640, 40×241
geometry), I/O port map (PIC `0x00/0x01`, 8255 `0x04–0x07`, UART, FDC), PIC
wiring (ir0..ir7 assignments), calibrated constants (frame-IRQ period 200,000
cycles, FDC 2 MHz-equivalent timings), and clock assumptions. Populated **from
cosim/twin sources**, with provenance notes per entry.

Consumers: rev B's B0 bus-contract doc (generated sections), HDL testbench
parameters, cosim guards, future spin-offs.

## The automatic part: a commons guard
Extend the existing consistency-guard pattern
(`scripts/check_documentation_consistency.py` precedent) with a **commons check**:
it verifies that constants appearing in spin-off HDL/testbenches/docs match
`juku-machine-facts.json`, and that derived artifacts (Z80 ROM image, GAL
equations, reconstructed PROM exports) are up to date with their root sources.
Run with the other guards; a root finding that changes a fact then *fails* every
stale consumer instead of silently diverging.

## Findings flow (the rule of motion)
1. New finding → update the root truth artifact (dump, facts file, measured-facts doc).
2. Re-run derivations (exports, ROM builds, GAL terms).
3. Commons guard flags every consumer that must react — that list *is* the work item.
4. Spin-off docs cite root docs; they don't restate numbers.

The inverse also holds: a spin-off bench discovery (e.g. rev A resolving the D6
polarity, rev B backplane timing reality) is a **root finding made on spin-off
hardware** — it lands in root first, then flows back out.
