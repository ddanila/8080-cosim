# VJUGA minimal-VGA experiment

Status date: 2026-07-10.

Status: **EXPERIMENTAL / DESIGN HOLD**.

VJUGA explores a smaller +5 V, Z80-based board with socketed ROM, one 64 KiB
4164-style DRAM bank, keyboard I/O, and a VGA-oriented display path. It is an
independent experiment, not the main Juku replica and not a released hardware
product.

## What works

- **The VJUGA top boots the real Juku firmware on a Z80.** `sim/boot_check.sh`
  runs the T80 core in **Z80 mode** against a 3-byte-patched ROM
  (`roms/ekta37_z80.bin`) with the Juku memory map, and draws a framebuffer
  byte-for-byte identical to the recreation's `cosim` oracle after 6000 video
  writes (the same map and oracle the main `sync/boot_check.sh` uses). No FDC
  and no interrupts are needed — the banner draws exactly as cosim runs it. See
  `hdl/juku_boot_top.vhd`.
- **A Verilog twin boots the same ROM on `tv80` through the real Juku chips.**
  `sim/vjuga_boot_check.sh` runs `hdl/vjuga_juku_top.v` (tv80 Z80 core + the real
  `dram_64kx1` РУ5 DRAM, the real `decode_prom` D6 К556РТ4, and the real
  `re3_prom` D8 К155РЕ3 — all reused verbatim from `hdl/devices.v` with the
  validated dumps) and matches the cosim framebuffer byte-for-byte at 6000 video
  writes. Booting exercises the DRAM and both PROMs in the functional path
  (workbench goals 2 and 3): a bad socketed chip diverges the boot. The D6 `~D0`
  correction is provisional (pending the main-twin level probe).
- The pinned T80 core also executes a built-in synthetic ROM (smoke test).
- The synthetic test exercises CPU ROM/RAM/I/O cycles, a bit-sliced DRAM
  model, independent refresh, video arbitration, keyboard-style input, and one
  VGA timing frame.
- An eight-instance logical HDL/KiCad model passes structural comparison.
- The Rev A physical source has 95 refs and 116 modeled nets.
- The committed four-layer routed PCB passes the repository's KiCad DRC and
  unconnected-item checks.
- The ignored `fab/minimal-vga/` package can be regenerated and its current
  Gerber/drill ZIP is internally checksummed.

### CPU choice: real Z80 + a 3-byte-patched ROM

VJUGA uses a **Z80** so the board runs from a single +5 V rail — the original
Juku CPU (КР580ВМ80 = 8080) needs +5 / +12 / −5 V, and dropping it removes two
supplies, which is the whole point of this minimal board.

The Juku firmware is 8080 code, and three of its bytes are 8080 undocumented
NOPs (`0x08/0x10/0x20` at `0x0021/0x0024/0x0026`) that a Z80 decodes as real
instructions (`EX AF,AF'`/`DJNZ`/`JR NZ`), so a stock Z80 diverges within the
first 40 fetches. The fix is a tiny ROM patch: those three opcodes are rewritten
to `NOP` (`0x00`) and the block-1 self-test checksum at `0x000A` is recomputed —
four bytes total, length-preserving, and provably 8080-behavior-identical (cosim
draws the same framebuffer to 200M cycles). See `roms/README.md` and
`tools/make_z80_rom.c`. The T80 core therefore runs in native **Z80 mode**
(`Mode => 0`).

(The core can also run the *unpatched* ROM in 8080 mode, `Mode => 2` — a useful
cross-check, but not the board's configuration.)

## What does not work yet

- The Rev A *physical* ROM map (in `z80_minimal_top.vhd` / the KiCad model) is
  still a coarse synthetic lower-ROM/upper-RAM map. The verified Juku overlay
  behavior currently lives in the functional `juku_boot_top.vhd` boot model;
  folding it into the Rev A physical top + GAL decode is the next step.
- The GAL equations are draft bring-up logic; DRAM timing and wait-state
  behavior have not been validated against selected parts or hardware.
- The VGA test proves timing activity, not a Juku banner or prompt sourced from
  shared DRAM.
- No independent end-to-end schematic/design review has released the copper.

Therefore the fabrication outputs are useful engineering artifacts, but the
board is **not authorized for vendor upload, order, or assembly**.

## Current scope

Included in the experiment:

- socketed DIP Z80, ROM, 8255, programmable logic, and eight 4164-compatible
  DRAM devices;
- +5 V input protection, clock/reset, debug headers, and diagnostics;
- keyboard matrix interface;
- shared CPU/refresh/video DRAM scaffold;
- VGA timing/debug header and pixel-serializer path.

Excluded from Rev A: FDC, external bus, tape/serial/network/mouse interfaces,
historical placement, and the original composite/RF chain.

## Evidence map

- `docs/workbench-plan.md`: the bench-fixture direction (test the real Juku
  РУ5/РТ4/РЕ3 parts) and the phased build plan.
- `hdl/README.md`: exactly what the synthetic simulation proves.
- `docs/rev-a-chip-map.md`: current physical decomposition.
- `docs/rev-a-gal-equations.md`: unvalidated programmable-logic draft.
- `docs/rev-a-placement-rules.md`: placement policy.
- `docs/rev-a-power-budget.md`: conservative planning estimate.
- `docs/rev-a-sourcing-plan.md`: future sourcing/assembly policy; stock must be
  rechecked at order time.
- `kicad/fab-notes.md`: routed/package facts and release blockers.
- `docs/rev-a-manufacturing-readiness.md`: top-level package/design status.
- `external/`: pinned-core and third-party design notes.

Generated reports under `fab/minimal-vga/` are ignored build artifacts. Their
individual `READY` labels mean the named mechanical/package check passed; they
do not override the top-level design hold.

## Checks

Run the current simulation and structural/physical checks:

```sh
spinoffs/minimal-vga/sim/check.sh
```

Run only the logical schematic/HDL comparison:

```sh
spinoffs/minimal-vga/sync/check.sh
```

Regenerate fabrication review artifacts only after accepting that they remain
non-release outputs:

```sh
spinoffs/minimal-vga/kicad/export_fab.sh
```

## Release gate

Before this experiment can become an order candidate it must, at minimum:

1. ~~boot the intended real Juku ROM on the VJUGA T80 top~~ **done**
   (`sim/boot_check.sh`, framebuffer-identical to cosim at 6000 video writes);
2. ~~match the intended memory and I/O behavior with an explicit oracle~~
   **done for the functional boot model** (cosim is the oracle); still to fold
   into the Rev A *physical* top + GAL decode;
3. render a deterministic real-ROM display result through the VGA path;
4. replace draft GAL timing with simulated, programmed, reviewed equations;
5. validate DRAM, reset, clock, power, connector, and socket pinouts against
   selected parts;
6. receive an independent schematic, copper, Gerber, drill, and power-return
   review; and
7. regenerate all package artifacts after the design is frozen.

Until then, work on VJUGA must not distract from the main replica's P0 closure
items in the repository-root `PLAN.md`.
