# VJUGA Rev A fabrication notes

Status: **PACKAGE BASELINE EXISTS / DESIGN HOLD**.

The current Rev A board is a routed physical experiment generated from
`rev-a-physical.board.json`. KiCad reports zero error-level DRC violations and
zero unconnected items. Those checks establish file coherence for modeled
nets; they do not prove the proposed computer will boot or that the design is
safe to order.

## Current physical baseline

- Four copper layers: `F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.
- 95 footprints, 117 PCB nets, and 2,082 tracks in the current checked board.
- No copper zones; power is explicitly routed, including 0.20 mm power tracks.
- Four corner mounting holes and two-sided assembly/silkscreen review output.
- Factory-assembly exports are drafts. Socketed ICs are intended for owner
  insertion; factory files primarily describe sockets, passives, connectors,
  protection, and diagnostics.

The no-zone/0.20 mm power strategy is an experiment, not a production
recommendation. Return paths, voltage drop, transient current, and actual
vendor stackup require human review before any release.

## Generated package

`export_fab.sh` can produce, under ignored `fab/minimal-vga/`:

- Gerbers and Excellon drill;
- deterministic Gerber/drill ZIP and SHA256 list;
- schematic and assembly-review PDFs;
- engineering BOM and draft assembly BOM/CPL;
- manual-install and post-assembly-insertion lists; and
- mechanical, ERC, DRC, package-integrity, and vendor-preview check reports.

Per-report `READY` states describe the scope named by that report. They are not
design-release or purchase authorization. The top-level status is tracked in
`../docs/rev-a-manufacturing-readiness.md`.

## Design blockers

- The spin-off HDL executes only a synthetic program; real Juku ROM boot on
  the T80/VJUGA top is unproven.
- U5/U24 GAL equations are draft bring-up equations and have not been validated
  against a timing simulation or programmed-device test.
- VGA timing activity is proven, but no real-ROM prompt/banner is rendered from
  the shared DRAM path.
- The coarse Rev A memory/I/O mapping is not yet shown compatible with the
  desired Juku firmware path.
- Actual oscillator, reset supervisor, DRAM, ROM, GAL, socket, fuse, TVS,
  connector, and assembly-process choices require datasheet/footprint review.
- The autorouted copper and power/return strategy need independent review.

## Regeneration commands

```sh
spinoffs/minimal-vga/sim/check.sh
spinoffs/minimal-vga/sync/check.sh
spinoffs/minimal-vga/kicad/check_rev_a_physical.sh
spinoffs/minimal-vga/kicad/check_rev_a_pcb.sh
spinoffs/minimal-vga/kicad/export_fab.sh
```

Routing changes must be regenerated from the source model and then rechecked;
do not hand-edit a generated artifact and treat it as source truth.

## Future assembly policy

If the design hold is eventually cleared:

- recheck all stock-sensitive CPNs and vendor capabilities immediately before
  ordering;
- mount socketed/vintage/programmed ICs only according to the final insertion
  list;
- confirm DIP widths, pin 1, polarized parts, USB-C/terminal pinout, and every
  cable-facing connector from the selected parts' datasheets;
- save vendor DFM/preview settings and final checksums with the private order
  record; and
- never reuse the current ZIP after any schematic, footprint, net, or routing
  change.
