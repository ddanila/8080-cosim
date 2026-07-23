# VJUGA Rev A manufacturing readiness

Status date: 2026-07-23.

Status: **DESIGN HOLD / SOURCE UPDATED, DRC AND PACKAGE STALE**.

The ignored fabrication directory currently contains an internally coherent
bare-PCB package. Its upload archive is:

`fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`

SHA256:

`75920e90151dd0f5ba54693c6b9e74bb5334d50b807a8379905a2cd48e3e180a`

This checksum proves artifact identity only. It is not permission to upload or
order the board.

**SUPERSEDED (2026-07-17):** the board was re-laid-out from the sparse 285x285
experiment to a compact **200x200 mm** floorplan, with parts and functional-block
borders aligned to a 0.2" (5.08 mm) grid and decoupling caps at each chip's short
side. It was re-placed (collision-clean, 5 mm edge keepout) and fully rerouted:
DRC-clean at **2,873 tracks**, 0 violations, 0 unconnected. The Gerber package
above predates the 285x285 board entirely and is now doubly stale. Because Gerber
SHAs are KiCad-version specific, the package must be regenerated and its SHA
re-frozen on the canonical (Linux) toolchain before any DFM/upload.

**CURRENT SOURCE ADDENDUM (2026-07-23):** exact D1 qualification corrected its
DO-35 placeholder to a DO-41 footprint and replaced one nearby `VCC_RAW`
segment with a five-segment clearance detour. The current source therefore has
**2,877 tracks/vias**. Its dedicated static guard passes, but the last full
KiCad DRC predates this bounded correction; rerun DRC with KiCad 10 before
package regeneration.

## Verified package facts

- The source PCB is four-layer, 200x200 mm, and routed.
- The last full KiCad checks reported zero DRC violations and zero unconnected
  items; the subsequent bounded D1 correction passes its local static guard and
  awaits the required full KiCad 10 DRC rerun.
- Gerber/drill membership, deterministic ZIP metadata, checksums, drill count,
  and external rendering have machine-generated checks (against the stale package).
- Draft BOM/CPL, manual-install, socket-insertion, orientation, and review
  artifacts exist.
- The routed board is 119 refs / 135 nets, filled In1.Cu GND and In2.Cu VCC
  planes, 29 factory BOM rows, 96 CPL placements, 23 manual placements, and 22
  post-assembly socket insertions. The committed copper has 2,877 tracks/vias
  after the 200x200 reroute and bounded D1 clearance correction; the frozen
  Gerber ZIP above predates even the 285x285 board and must be re-exported (see
  the superseded note).
- The behavioral aggregate previously passed both real-ROM CPU
  implementations, dual decode modes, framebuffer readback, U24 timing, LVS,
  physical-model, footprint, PCB, DRC, and DRAM guards. The D1-specific static
  guard now also passes; repeat the KiCad-dependent PCB/DRC/package portions
  after regenerating with the canonical toolchain.

## Release blockers

- T80 and tv80 VJUGA tops boot the patched real Juku firmware and match cosim's
  framebuffer at 6000 writes (`sim/boot_check.sh` and
  `sim/vjuga_boot_check.sh`); physical-board boot remains untested.
- The current routed copper includes every Phase 3 socket/header and retains
  filled GND/VCC inner planes. The pre-D1 source passed
  zero-violation/zero-unconnected KiCad DRC; the current bounded correction
  passes its static clearance/continuity guard but awaits full KiCad 10 DRC.
  The saved Gerber package is older and does not match this route.
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

1. **Route the PCB (Phase 3 step f) — DONE (re-laid-out + rerouted 2026-07-17).**
   All 119 refs are placed and collision-clean on the compact 200x200 board (grid-
   aligned parts and block frames, caps at chip short sides, 5 mm edge keepout);
   every modeled pin lands on a real pad. The board was regenerated and fully
   rerouted (freerouting fork, all 357 nets, 0 unrouted / 0 violations), then
   received the bounded D1 clearance detour, giving 2,877 F.Cu/B.Cu tracks
   (segments plus vias) with filled In1.Cu GND and In2.Cu VCC planes. The
   pre-D1 route had zero KiCad DRC/unconnected items; rerun full KiCad 10 DRC
   for the current source. The router runs on Linux and macOS (fork jar + JDK
   25).
2. **Footprint / pinout validation.** DONE for land-pattern correctness:
   `check_rev_a_footprints.sh` confirms every modelled pin lands on a real pad
   and DIP pad counts match, across all 119 parts (it caught the USB-C shield
   S1/SH and RES_TH slips). The exact HRO TYPE-C-31-M-17/C283540 J3 candidate
   is now checksum- and geometry-guarded by `rev-a-usb-c-candidate.md`,
   including all six contacts, four shell tabs, body outline, and power-only
   CC/VBUS/GND contract. The exact Bourns MF-RG300-0-14/C3761779 F1 candidate
   is likewise checksum-, electrical-, topology-, and static-fit-guarded by
   `rev-a-ptc-candidate.md`. The exact Littelfuse P4KE6.8A-B/C1666224 D1
   candidate is checksum-, polarity-, topology-, geometry-, and local
   routed-clearance-guarded by `rev-a-tvs-candidate.md`. STILL REVIEW ITEMS:
   physical pin-1 orientation of the socketed parts; F1 thermal/load
   qualification; D1 surge-environment qualification; and order-time stock,
   process, orientation, and first-article checks for J3/F1/D1.

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
   the 2026-07-16 review-fix reroute and 2026-07-23 D1 correction superseded
   the previously frozen ZIP (see the notes at the top). Run full DRC, re-export
   the Gerber/drill package on the canonical KiCad 10 toolchain, and record its
   new SHA256 here. THEN: vendor DFM/preview plus live stock and
   assembly-capability review at order time.
Before order, finish the staged full-board LVS (twin ↔ board, beyond the
decode/observability contracts), or record a specific owner waiver backed by
independent schematic, selected-part pinout, and copper review. This is exactly
the check that catches a mis-bound pin before it is etched; it is not silently
optional merely because the narrower decode contract passes.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
