# VJUGA minimal-VGA experiment

Status date: 2026-07-10.

Status: **EXPERIMENTAL / DESIGN HOLD**.

VJUGA explores a smaller +5 V, Z80-based board with socketed ROM, one 64 KiB
4164-style DRAM bank, keyboard I/O, and a VGA-oriented display path. It is an
independent experiment, not the main Juku replica and not a released hardware
product.

## What works

- The pinned T80 core executes a built-in synthetic ROM.
- The synthetic test exercises CPU ROM/RAM/I/O cycles, a bit-sliced DRAM
  model, independent refresh, video arbitration, keyboard-style input, and one
  VGA timing frame.
- An eight-instance logical HDL/KiCad model passes structural comparison.
- The Rev A physical source has 95 refs and 116 modeled nets.
- The committed four-layer routed PCB passes the repository's KiCad DRC and
  unconnected-item checks.
- The ignored `fab/minimal-vga/` package can be regenerated and its current
  Gerber/drill ZIP is internally checksummed.

## What does not work yet

- The VJUGA top has not booted a real Juku ROM. The main project's boot check
  runs as a regression, but it executes the main 8080 design, not this board.
- The Rev A ROM map is a coarse synthetic lower-ROM/upper-RAM map, not the
  verified Juku overlay behavior.
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

1. boot the intended real Juku ROM on the VJUGA T80 top;
2. match the intended memory and I/O behavior with an explicit oracle;
3. render a deterministic real-ROM display result through the VGA path;
4. replace draft GAL timing with simulated, programmed, reviewed equations;
5. validate DRAM, reset, clock, power, connector, and socket pinouts against
   selected parts;
6. receive an independent schematic, copper, Gerber, drill, and power-return
   review; and
7. regenerate all package artifacts after the design is frozen.

Until then, work on VJUGA must not distract from the main replica's P0 closure
items in the repository-root `PLAN.md`.
