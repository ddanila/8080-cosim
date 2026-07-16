# VJUGA Rev A manufacturing readiness

Status date: 2026-07-16.

Status: **DESIGN HOLD / PACKAGE VERIFIED**.

The ignored fabrication directory currently contains an internally coherent
bare-PCB package. Its upload archive is:

`fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`

SHA256:

`75920e90151dd0f5ba54693c6b9e74bb5334d50b807a8379905a2cd48e3e180a`

This checksum proves artifact identity only. It is not permission to upload or
order the board.

**SUPERSEDED (2026-07-16):** the board was rerouted for the design-review
placement fixes (USB-C J3 to the board edge, U20 clear of the block border,
observability-header labels, decode-cap spacing). The routed copper is
DRC-clean at 2,435 tracks, but the Gerber package above predates it. Because
Gerber SHAs are KiCad-version specific, the package must be regenerated and its
SHA re-frozen on the canonical (Linux) toolchain before any DFM/upload.

## Verified package facts

- The source PCB is four-layer and routed.
- Current KiCad checks report zero DRC violations and zero unconnected items.
- Gerber/drill membership, deterministic ZIP metadata, checksums, drill count,
  and external rendering have machine-generated checks.
- Draft BOM/CPL, manual-install, socket-insertion, orientation, and review
  artifacts exist.
- The routed board is 119 refs / 135 nets, filled In1.Cu GND and In2.Cu VCC
  planes, 29 factory BOM rows, 96 CPL placements, 23 manual placements, and 22
  post-assembly socket insertions. The committed copper now has 2,435 tracks
  after the review-fix reroute; the frozen Gerber ZIP above (2,394 tracks)
  predates it and must be re-exported (see the superseded note).
- The full behavioral aggregate passes both real-ROM CPU implementations,
  dual decode modes, framebuffer readback, U24 timing, LVS, physical-model,
  footprint, PCB, DRC, and DRAM guards. The order-readiness aggregate reports
  `PACKAGE VERIFIED / DESIGN HOLD`.

## Release blockers

- T80 and tv80 VJUGA tops boot the patched real Juku firmware and match cosim's
  framebuffer at 6000 writes (`sim/boot_check.sh` and
  `sim/vjuga_boot_check.sh`); physical-board boot remains untested.
- The current routed copper includes every Phase 3 socket/header and passes
  zero-violation/zero-unconnected KiCad DRC with filled GND/VCC inner planes.
  The saved Gerber package matches this route, but human review still withholds
  fabrication authorization.
- U24's Gray-coded DRAM timing contract passes CPU read/write, RAS-only refresh,
  CPU/refresh collision handling, video arbitration, and vendored MK4564-12
  timing guards at 4 MHz. The tv80 real-ROM path uses those controls and remains
  framebuffer-identical to cosim. U5/U24 still need device-specific compilation,
  programmed-device tests, and review.
- Real firmware framebuffer contents are proven byte-for-byte without display
  hardware; VGA timing/activity remains synthetic and physical video output is
  untested.
- The schematic, selected-part pinouts, copper, power/return strategy, and
  Gerbers have not received the independent design review needed for release.

## Order-readiness checklist (bare PCB)

What is left before ordering an empty (bare, unpopulated) Rev-A PCB, in order.
Copper-blocking items must be closed; de-risking items are reprogrammable after
fab but their pinouts freeze in copper, so decide them first.

**Copper-blocking**

1. **Route the PCB (Phase 3 step f) — DONE (rerouted 2026-07-16).** All 119 refs
   are placed and collision-clean; every modeled pin lands on a real pad. After
   the design-review placement fixes the board was regenerated and rerouted
   (freerouting fork, 0 unrouted / 0 violations), giving 2,435 F.Cu/B.Cu tracks
   with filled In1.Cu GND and In2.Cu VCC planes and zero KiCad DRC/unconnected
   items. The route runs on both the Linux box and macOS (fork jar + JDK 25).
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
6. **Regenerate + freeze the fab package (README gate 7) — RE-FREEZE PENDING:**
   the 2026-07-16 review-fix reroute superseded the previously frozen ZIP (see
   the superseded note at the top). Re-export the Gerber/drill package on the
   canonical (Linux) toolchain and record its new SHA256 here. THEN: vendor
   DFM/preview plus live stock and assembly-capability review at order time.
Optional-but-recommended before order: finish the staged full-board LVS
(twin ↔ board, beyond the decode/observability contracts) — it is exactly the
check that catches a mis-bound pin before it is etched.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
