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
- **This package predates the Phase 3 decode-socket addition.** The committed
  Gerbers/ZIP reflect the earlier 95-ref board; the schematic and connectivity
  (source of truth, `check_rev_a_physical`) now carry the real РТ4/РЕ3 sockets,
  the mode inverter, the jumper, and the observability header (116 refs / 134
  nets). The package must be regenerated from the re-laid-out PCB before it
  describes the current design.

## Release blockers

- No real Juku ROM has booted on the VJUGA T80 top.
- The passing main-project ROM check does not execute this spin-off.
- The routed copper does not yet include the Phase 3 decode sockets; the PCB
  must be re-laid-out from the current schematic (Phase 3 step f) before fab.
- U24 DRAM timing is an unvalidated bring-up draft; the U5 decode is now
  simulated in both jumper modes but not yet programmed or reviewed on a device.
- The VGA proof is synthetic timing/activity, not a real firmware display.
- The schematic, selected-part pinouts, copper, power/return strategy, and
  Gerbers have not received the independent design review needed for release.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
