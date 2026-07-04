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
- Silkscreen: both sides useful for debug.
- Assembly: bare PCB first; manual socketed assembly.

## Files Needed Before Ordering

Bare PCB:

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

Optional assembly:

- BOM with orderable MPNs.
- CPL / position file.
- Assembly drawings.
- DNP list.
- Polarity/orientation notes.

## Pre-Order Checks

- `spinoffs/minimal-vga/sim/check.sh`
- `spinoffs/minimal-vga/sync/check.sh`
- KiCad ERC.
- KiCad DRC.
- Zero unrouted nets.
- `export_fab.sh` blocks export unless KiCad DRC exits cleanly. Override only
  for debug artifacts with `MINIMAL_VGA_ALLOW_DRC_EXPORT=1`.
- `report_rev_a_fab_readiness.sh` writes the current DRC/unconnected summary to
  `fab/minimal-vga/fab-readiness.md`.
- Visual inspection of Gerbers in an independent viewer.
- Confirm all socket footprints match actual sockets and IC widths.
- Confirm ATX connector pinout, F1 current rating, D1 TVS rating, and PS_ON
  behavior against the target supply.
- Confirm reset supervisor pinout and oscillator package before ordering.
