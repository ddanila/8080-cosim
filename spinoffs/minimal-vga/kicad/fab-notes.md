# Fabrication notes

Status: **not ready for manufacture**.

The current default KiCad file is a connectivity/LVS scaffold generated from
`minimal-vga.board.json`. `rev-a-physical.board.json` and
`rev-a-physical.kicad_pcb` are the first physical chip/footprint targets. The
PCB scaffold is generated as a 4-layer board, but it is still not a routed
production PCB file.

Current generated-placement baseline: KiCad reports zero error-level DRC
violations after filling the generated `GND` and `VCC` zones. The board is
still blocked from fab export until routing removes the remaining unconnected
ratsnest items.

## Intended Rev A Fabrication Defaults

- 4-layer PCB.
- Layer proposal:
  - L1: components and signals.
  - L2: solid GND.
  - L3: +5V plane/islands and signals.
  - L4: signals.
- Current generator guard: `check_rev_a_pcb.py` requires `F.Cu`, `In1.Cu`,
  `In2.Cu`, and `B.Cu`.
- Current generated placeholders: filled `GND` zone on `In1.Cu` and filled
  `VCC` zone on `In2.Cu`. These still need routing review before ordering.
- Board thickness: 1.6 mm unless mechanical constraints change.
- Copper: 1 oz default.
- Soldermask: any.
- Silkscreen: both sides useful for debug. Generated board-owned silkscreen
  labels use the project-local `GOST type B italic` font face from
  `../../../fonts/gost-type-b-italic.ttf`.
- Assembly: factory assembly target for passives, sockets, connectors, and
  protection parts where practical; owner-supplied IC insertion where needed.

## Files Needed Before Ordering

PCB fabrication:

- Routed `.kicad_pcb`.
- Final KiCad schematic using real library symbols and finalized GAL/header
  pinouts.
- Final routed `rev-a-physical.kicad_pcb`, regenerated after GAL/header pinouts
  and passives are frozen.
- Gerber set.
- Excellon drill files.
- Edge.Cuts outline.
- Fabrication notes with layer stack.
- Schematic PDF for review.

Factory assembly:

- Engineering BOM: `rev-a.engineering-bom.csv` in the final fab export.
- JLCPCB upload BOM: `assembly/jlcpcb-bom-draft.csv`, generated from the
  physical PCB and engineering BOM.
- JLCPCB upload CPL: `assembly/jlcpcb-cpl-draft.csv`, generated from the same
  physical PCB.
- Post-assembly insertion list: `assembly/post-assembly-insertion.csv`.
- Assembly readiness report: `assembly/assembly-readiness.md`.
- Assembly drawings.
- DNP list.
- Polarity/orientation notes.
- Socket orientation notes for every socketed DIP device.
- Owner-supplied/post-assembly insertion notes for Z80, ROM, DRAM, 8255, and
  GAL/PAL devices if those parts are not factory-sourced.

## Pre-Order Checks

- `spinoffs/minimal-vga/sim/check.sh`
- `spinoffs/minimal-vga/sync/check.sh`
- `spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py`
- KiCad ERC.
- KiCad DRC.
- Zero unrouted nets.
- `export_fab.sh` blocks export unless KiCad DRC exits cleanly. Override only
  for debug artifacts with `MINIMAL_VGA_ALLOW_DRC_EXPORT=1`.
- `export_fab.sh` emits the generated JLCPCB BOM/CPL pair only after the DRC
  gate, so a real order package cannot silently use a stale position file.
- `report_rev_a_fab_readiness.sh` writes the current DRC/unconnected summary to
  `fab/minimal-vga/fab-readiness.md`.
- Visual inspection of Gerbers in an independent viewer.
- Confirm all socket footprints match actual sockets and IC widths.
- Assign and re-check JLCPCB/LCSC SKUs for factory-mounted sockets, passives,
  connectors, oscillator/reset, and protection parts immediately before order.
- Confirm whether the selected factory assembly process will mount the intended
  through-hole sockets/connectors or requires those parts to be left manual.
- Confirm ATX connector pinout, F1 current rating, D1 TVS rating, and PS_ON
  behavior against the target supply.
- Confirm reset supervisor pinout and oscillator package before ordering.

## JLCPCB Assembly File Policy

Do not upload `rev-a.bom.csv` directly as the factory BOM. That file is the
engineering BOM and keeps design intent such as "Z80 CPU" at `U1`.

The generated JLCPCB BOM instead treats socketed DIP footprints as sockets to
be factory-mounted at the `U*` designators. The matching post-assembly list
then records which owner-supplied IC should be inserted into each socket after
the board comes back from assembly.

The generated BOM and CPL must have the same designator set. This follows
JLCPCB's current BOM/CPL guidance and is checked by
`export_jlcpcb_assembly.py`.
