# 8080-cosim

Reconstruction of the Soviet/Estonian Juku E5104 processor board as both a
physical PCB and a runnable, headless digital model. The project’s distinctive
piece is an LVS-style check that compares the structural Verilog connectivity
with the machine-readable board model.

## Current result

- The C emulator and the structural `juku_top` model boot the real Juku ROM,
  render the same framebuffer, accept keyboard input, boot EKDOS from the
  vendored disk images, and reach disk BASIC `READY`.
- `sync/check.sh` currently compares 101 mapped instances and 259 nets with no
  KiCad/HDL mismatch.
- The routed main-board artifact has 240 footprints, no KiCad clearance/short
  errors, and one explicit `M5V_DERIVED` airwire after correcting D105.10. Its
  saved Gerber/drill ZIP is checksum-reproducible, but the manufacturing gate
  correctly marks the package invalid until that airwire and the stale routed
  snapshot are replaced. Current ZIP SHA256:
  `341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4`.
- The main board is **not released for fabrication**. Validated physical D2
  `.037` and D6 `.038` tables are preserved; the measured D2/D30/D105 and
  D6/D13 continuity is adopted in the source model and HDL, while the routed
  snapshot still needs replacement. D94 still
  lacks pin 15, outputs D3-D7, and PROM truth. There are 9 official
  FDC-support ICs with only their physical pin maps and power endpoints modeled.
  The measured D105 DBIN/H and MEMW paths are modeled in the source PCB and HDL;
  the routed snapshot still carries the superseded topology.
  D30 READY section A and the section-B R5/D105 connections are modeled; pins
  8 and 11 remain explicit boundaries. In total, 226 modeled nets retain source-risk annotations requiring
  evidence or explicit redesign.
  See [PLAN.md](PLAN.md).

That last distinction matters: a clean DRC and a green LVS prove only the
connectivity represented in those checks. They do not prove omitted pins,
unmodeled footprints, reconstructed PROM contents, or analog/timing assumptions.

## Evidence and source hierarchy

1. Factory drawings, board photographs, dumps, and owner measurements under
   `ref/` are the historical evidence.
2. `kicad/juku.board.json` is the current machine-readable connectivity model.
3. `kicad/juku.kicad_sch`, the PCB files, and fabrication outputs are derived
   from or checked against that model.
4. `hdl/juku_top.v` is independently maintained structural Verilog and is
   checked against the modeled connectivity by `sync/`.
5. `cosim/` and the current upstream MAME Juku driver are behavioral oracles;
   they are not substitutes for missing physical wiring evidence.

## Board previews

These renders show the current routed engineering artifact, not a fabrication
release.

| 3D | 2D |
| --- | --- |
| ![3D top](renders/board_3d_top.png) | ![component side](renders/board_2d_front.png) |
| ![3D perspective](renders/board_3d_persp.png) | ![solder side](renders/board_2d_back.png) |

## Useful entry points

- [PLAN.md](PLAN.md) — remaining work and release criteria.
- [docs/README.md](docs/README.md) — documentation map and generated-report
  policy.
- [docs/development-workflow.md](docs/development-workflow.md) — canonical
  branch, intermediate commit, and direct-push policy.
- [docs/architecture.md](docs/architecture.md) — model boundaries and data flow.
- [docs/source-coverage-audit.md](docs/source-coverage-audit.md) — adopted
  external evidence and remaining source gaps.
- [sync/README.md](sync/README.md) — verification commands.
- [docs/replica-manufacturing-readiness.md](docs/replica-manufacturing-readiness.md)
  — fabrication-package integrity and the current design hold.

## Quick checks

```sh
sync/check.sh
sync/boot_check.sh
sync/cosim_check.sh
python3 scripts/check_documentation_consistency.py
```

The long reset-to-EKDOS/BASIC and Monitor 3.3 diagnostics are intentionally
separate from the fast default checks; `sync/README.md` identifies their entry
points.

## Layout

| Path | Purpose |
| --- | --- |
| `ref/` | Factory drawings, photographs, firmware evidence, and external references |
| `kicad/` | Board model, generated schematic, source/routed PCB, and fabrication tooling |
| `hdl/` | Structural runnable model and device behavior |
| `cosim/` | Independent software emulator/oracle |
| `sync/` | LVS, behavioral comparisons, and subsystem guards |
| `roms/`, `media/` | Vendored preservation inputs with provenance/checksums |
| `docs/` | Current specifications and generated evidence reports |
| `spinoffs/minimal-vga/` | Independent VJUGA experiment; not on the replica critical path |
