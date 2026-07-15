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
  the mode inverter, the jumpers, and the observability headers (119 refs / 134
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

## Order-readiness checklist (bare PCB)

What is left before ordering an empty (bare, unpopulated) Rev-A PCB, in order.
Copper-blocking items must be closed; de-risking items are reprogrammable after
fab but their pinouts freeze in copper, so decide them first.

**Copper-blocking**

1. **Re-layout the routed PCB (Phase 3 step f).** Source model is 119 refs /
   134 nets; `rev-a-physical.kicad_pcb` still holds the old 95-ref board.
   Regenerate placement + routing from the model (`gen_rev_a_pcb.py` →
   `route_rev_a_pcb.sh`), then `check_rev_a_pcb.sh` must report zero DRC and zero
   unconnected. First-pass footprint mappings + placement for the new parts now
   exist in `gen_rev_a_pcb.py` (see the silk preview); routing + refinement is
   the remaining work.
2. **Footprint / pinout validation against the selected parts (README gate 5).**
   Datasheet-vs-footprint pass for every socket and passive, especially the new
   DIP-16 РТ4/РЕ3 sockets, the DIP-14 inverter, the pin headers, the USB-C
   receptacle, PTC, and TVS.

**De-risking (freeze before copper, even though reprogrammable)**

3. **U24 DRAM-timing GAL (README gate 4).** Simulate against the `dram_64kx1` /
   KM4164B-10 timing so no needed signal is missing from its frozen pinout. The
   U5 decode half is already simulated in both jumper modes.
4. **VGA path (README gate 3) needs an explicit owner decision.** It is deferred
   for the workbench purpose and the framebuffer-readback oracle replaces it, but
   the gate still lists it. Recommendation: formally waive/re-scope it for the
   bench-fixture Rev-A here rather than leave it as an open blocker.

**Human gate + paperwork**

5. **Independent review (README gate 6):** schematic, copper, Gerber/drill,
   power-return — after the re-layout.
6. **Regenerate + freeze the fab package (README gate 7):** new Gerber ZIP + its
   SHA256 into this doc; recheck stock/vendor capability at order time.
7. **Doc + guard cleanup:** the "real Juku ROM boot unproven" language in
   `../kicad/fab-notes.md` and the checker-pinned "No real Juku ROM has booted"
   phrase here both predate the boot proof; releasing requires updating the docs
   and the consistency guard together, not editing the text alone.

Optional-but-recommended before order: finish the staged full-board LVS
(twin ↔ board, beyond the decode/observability contracts) — it is exactly the
check that catches a mis-bound pin before it is etched.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
