# VJUGA minimal-VGA experiment

Status date: 2026-07-23.

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
  (workbench goals 2 and 3): a bad socketed chip diverges the boot. Corrected
  reader-3 packing proves D6 D0/pin12 is active-low `ROM_N`; Mode B now consumes
  that polarity directly.
- **Both decode modes boot byte-identical.** `sim/vjuga_boot_check.sh` builds and
  boots the twin in Mode B (the real D6 РТ4 drives the decode) *and* Mode A (the
  U5 GAL's internal A15/A14 baseline, РТ4 socket empty), and requires each to
  match the cosim framebuffer — so every physical `MODE_B` jumper setting (J94)
  has a proven simulated counterpart.
- The pinned T80 core also executes a built-in synthetic ROM (smoke test).
- The synthetic test exercises CPU ROM/RAM/I/O cycles, a bit-sliced DRAM
  model, independent refresh, video arbitration, keyboard-style input, and one
  VGA timing frame.
- An eight-instance logical HDL/KiCad model passes structural comparison.
- Six independently authored physical-board LVS stages pass. Stage 1 covers
  all POWER and CLOCK_RESET placement refs, J93, and the U1 clock/reset/power
  boundary (17 refs / 9 partitions). Stage 2 closes all 22 decode
  socket/glue parts plus six exact boundary projections (28 refs / 37
  partitions / 5 NC pads). Stage 3 closes every U1 Z80 and U2 ROM pin plus
  C1/C2, with every endpoint on 36 non-power core nets included (35 mapped
  refs / 38 partitions / 2 NC pads). Stage 4 closes U10-U17 and C6-C13, with
  every endpoint on 19 non-power DRAM-bank nets included (25 mapped refs / 21
  partitions / 8 NC pads). Stage 5 closes U20/U21 and C14/C15, including both
  grounded active-low enables and every endpoint on 25 non-power address-mux
  nets (19 mapped refs / 27 partitions). Stage 6 closes every U22/C16 pin,
  including both grounded active-high resets and the low-to-high-half cascade,
  plus every endpoint on CLK and all eight refresh-row nets (11 mapped refs /
  11 partitions). All stages include mutation controls. Whole-board coverage
  remains incomplete; see `docs/rev-a-lvs-coverage.md`.
- U23 is retained only as an empty DNP spare socket. Its eight outputs have no
  consumers and the verified video timing/request handoff is U40/U41; generated
  assembly artifacts therefore omit U23 from owner IC insertion while still
  mounting its routed socket.
- The Rev A physical source has 119 refs and 133 modeled nets, and now sockets
  the real Juku decode PROMs (U3 К556РТ4, U4 К155РЕ3) with a Mode-A/Mode-B
  jumper plus the Phase 4 observability headers (J96 clock-control, J97 high
  address + write strobe, J98 control bus); `check_rev_a_physical` enforces
  decode-socket and observability contracts that match the verified twin.
- **The framebuffer-readback boot oracle is built and validated.**
  `sim/vjuga_readback_check.sh` boots the twin with `+capture`, reassembles the
  write stream (`tools/vjuga_fb_readback/reassemble.py`), and confirms it equals
  both the twin's own dump and cosim's `vram.bin` — so the banner is verifiable
  on the bench from analyzer captures with zero display electronics. A twin
  reference trace (`tools/vjuga_single_step/`) backs the UNO single-step rig.
- The committed four-layer routed PCB includes the Phase 3 decode sockets and
  observability headers and passes the repository's KiCad DRC and
  unconnected-item checks. Independent schematic/copper and power-return review
  still holds release.
- The last ignored `fab/minimal-vga/` package predates both the U20/U21
  address-mux enable correction and the U22 refresh-counter cascade correction,
  and is **stale; do not upload or order it**. Its superseded
  Gerber/drill ZIP SHA-256 was
  `19d7e1fe1b8b80720f16dc4b8d096fa43af59f956f687e7a3e7f60799422d478`.
  A fresh guarded stable-KiCad export and checksum are required.

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

- The current Rev A copper includes the Phase 3 decode sockets and observability
  headers and passes zero-violation/zero-unconnected KiCad DRC. Its two inner
  layers are reserved for filled GND/VCC planes; independent review remains.
- The U5 decode is simulated in both jumper modes, and U24's Gray-coded DRAM
  timing/wait-state reference passes the slower vendored MK4564-12 limits at
  4 MHz. Neither GAL has been compiled/programmed or validated in hardware.
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
- `docs/phase4-bench-bringup.md`: the detailed Phase 4 plan — pre-fab
  observability design-ins, analyzer channel maps, the framebuffer-readback
  boot oracle, the UNO single-step rig, and the assembly/chip-test ladder.
- `hdl/README.md`: exactly what the synthetic simulation proves.
- `docs/rev-a-chip-map.md`: current physical decomposition.
- `docs/rev-a-gal-equations.md`: unvalidated programmable-logic draft.
- `docs/rev-a-placement-rules.md`: placement policy.
- `docs/rev-a-power-budget.md`: conservative planning estimate.
- `docs/rev-a-sourcing-plan.md`: future sourcing/assembly policy; stock must be
  rechecked at order time.
- `docs/rev-a-drc-readiness.md`: current stable KiCad 10.0.5 full-DRC result
  bound to the exact source-board SHA; the former fabrication package is
  explicitly stale after the mux-enable and refresh-counter corrections.
- `docs/rev-a-lvs-coverage.md`: exact staged physical-LVS scope, negative
  control, and the groups still outside the whole-board comparison.
- `docs/rev-a-usb-c-candidate.md`: checksum- and geometry-guarded exact HRO
  TYPE-C-31-M-17/C283540 J3 candidate; order-time orientation/stock remains.
- `docs/rev-a-ptc-candidate.md`: checksum-, electrical-, topology-, and
  static-fit-guarded Bourns MF-RG300-0-14/C3761779 F1 candidate; thermal,
  stock, and first-article checks remain.
- `docs/rev-a-tvs-candidate.md`: checksum-, polarity-, topology-, geometry-,
  and routed-clearance-guarded Littelfuse P4KE6.8A-B/C1666224 D1 candidate;
  surge, stock, and first-article checks remain.
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

Run the completed physical-board LVS stages:

```sh
spinoffs/minimal-vga/sync/rev_a_power_clock_reset_lvs.sh
spinoffs/minimal-vga/sync/rev_a_decode_lvs.sh
spinoffs/minimal-vga/sync/rev_a_cpu_rom_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_bank_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_mux_lvs.sh
spinoffs/minimal-vga/sync/rev_a_refresh_counter_lvs.sh
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
   ~~and fold it into the Rev A physical top + GAL decode~~ **done** — the Rev A
   decode sockets the real РТ4/РЕ3 and both jumper modes boot byte-identical to
   cosim (`sim/vjuga_boot_check.sh`);
3. ~~render a deterministic real-ROM display result through the VGA path~~
   **waived for Rev A's bench-fixture scope** — the guarded framebuffer-capture
   path is the physical boot oracle; VGA remains an experimental output and is
   not required to test РУ5/РТ4/РЕ3 parts;
4. **decode and U24 DRAM-timing equations are simulated** (item 2 and
   `sim/u24_dram_timing_check.sh`); still compile, program, and review them on
   the exact chosen GAL22V10 devices;
5. validate DRAM, reset, clock, power, connector, and socket pinouts against
   selected parts;
6. receive an independent schematic, copper, Gerber, drill, and power-return
   review, plus full-board LVS or an explicit owner waiver that names this
   independent review as compensating evidence; and
7. regenerate all package artifacts after the design is frozen.

Until then, work on VJUGA must not distract from the main replica's P0 closure
items in the repository-root `PLAN.md`.
