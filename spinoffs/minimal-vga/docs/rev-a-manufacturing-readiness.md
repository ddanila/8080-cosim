# VJUGA Rev A manufacturing readiness

Status date: 2026-07-10.

Status: **DESIGN HOLD / PACKAGE VERIFIED**.

The ignored fabrication directory currently contains an internally coherent
bare-PCB package. Its upload archive is:

`fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`

SHA256:

`4c6553e1eaef0a72ac24a2a3ad89998cab806d236a18404764c18ba064ca7138`

This checksum proves artifact identity only. It is not permission to upload or
order the board.

## Verified package facts

- The source PCB is four-layer and routed.
- Current KiCad checks report zero DRC violations and zero unconnected items.
- Gerber/drill membership, deterministic ZIP metadata, checksums, drill count,
  and external rendering have machine-generated checks.
- Draft BOM/CPL, manual-install, socket-insertion, orientation, and review
  artifacts exist.

## Release blockers

- No real Juku ROM has booted on the VJUGA T80 top.
- The passing main-project ROM check does not execute this spin-off.
- U5/U24 GAL behavior and DRAM timing are unvalidated bring-up drafts.
- The VGA proof is synthetic timing/activity, not a real firmware display.
- The schematic, selected-part pinouts, copper, power/return strategy, and
  Gerbers have not received the independent design review needed for release.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
