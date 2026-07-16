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
  the mode inverter, the jumpers, and the observability headers (119 refs / 135
  nets). The package must be regenerated from the re-laid-out PCB before it
  describes the current design.

## Release blockers

- T80 and tv80 VJUGA tops boot the patched real Juku firmware and match cosim's
  framebuffer at 6000 writes (`sim/boot_check.sh` and
  `sim/vjuga_boot_check.sh`); physical-board boot remains untested.
- The current routed copper includes every Phase 3 socket/header and passes
  zero-violation/zero-unconnected KiCad DRC with filled GND/VCC inner planes.
  The saved Gerber package still predates this route and is not orderable.
- U24's Gray-coded DRAM timing contract passes CPU read/write, RAS-only refresh,
  CPU/refresh collision handling, video arbitration, and vendored MK4564-12
  timing guards at 4 MHz. The tv80 real-ROM path uses those controls and remains
  framebuffer-identical to cosim. U5/U24 still need device-specific compilation,
  programmed-device tests, and review.
- The VGA proof is synthetic timing/activity, not a real firmware display.
- The schematic, selected-part pinouts, copper, power/return strategy, and
  Gerbers have not received the independent design review needed for release.

## Order-readiness checklist (bare PCB)

What is left before ordering an empty (bare, unpopulated) Rev-A PCB, in order.
Copper-blocking items must be closed; de-risking items are reprogrammable after
fab but their pinouts freeze in copper, so decide them first.

**Copper-blocking**

1. **Route the PCB (Phase 3 step f) — DONE.** All 119 refs are placed and
   collision-clean; every modeled pin lands on a real pad. The current board has
   2,394 F.Cu/B.Cu tracks, filled In1.Cu GND and In2.Cu VCC planes, and zero
   KiCad DRC violations/unconnected items. The deterministic route preserves
   only six independently DRC-checked seed segments (USB-C grounds and one
   keyboard-column escape).
2. **Footprint / pinout validation.** DONE for land-pattern correctness:
   `check_rev_a_footprints.sh` confirms every modelled pin lands on a real pad
   and DIP pad counts match, across all 119 parts (it caught the USB-C shield
   S1/SH and RES_TH slips). STILL A REVIEW ITEM: physical pin-1 orientation of
   the socketed parts and confirming the chosen real part variants (USB-C
   receptacle, PTC, TVS) against their datasheets.

**De-risking (freeze before copper, even though reprogrammable)**

3. **U24 DRAM-timing GAL (README gate 4).** **Simulation DONE:**
   `sim/u24_dram_timing_check.sh` guards the corrected GAL22V10 pin contract and
   slower MK4564-12 minima at 4 MHz. REMAINING: compile U5/U24 into the exact
   chosen GAL device format, preserve fuse checksums, program, and bench-test.
4. **VGA path (README gate 3) needs an explicit owner decision.** It is deferred
   for the workbench purpose and the framebuffer-readback oracle replaces it, but
   the gate still lists it. Recommendation: formally waive/re-scope it for the
   bench-fixture Rev-A here rather than leave it as an open blocker.

**Human gate + paperwork**

5. **Independent review (README gate 6):** current schematic/copper and the
   regenerated Gerber/drill and power-return strategy.
6. **Regenerate + freeze the fab package (README gate 7):** new Gerber ZIP + its
   SHA256 into this doc; recheck stock/vendor capability at order time.
Optional-but-recommended before order: finish the staged full-board LVS
(twin ↔ board, beyond the decode/observability contracts) — it is exactly the
check that catches a mis-bound pin before it is etched.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
