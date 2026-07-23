# VJUGA Rev A manufacturing readiness

Status date: 2026-07-23.

Status: **DESIGN HOLD / CURRENT PACKAGE VERIFIED**.

The ignored fabrication directory contains the current internally coherent
200x200 mm bare-PCB package, generated with stable KiCad 10.0.5 after the
compact reroute, D1 DO-41 correction, and inner-plane refill. Its upload
archive is:

`fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`

SHA256:

`19d7e1fe1b8b80720f16dc4b8d096fa43af59f956f687e7a3e7f60799422d478`

The source PCB SHA-256 is
`a056d758c89801737bb285ce58f96e922cabff62d8d769d3e5c300267940b746`.
`order-readiness.md` reports **PACKAGE VERIFIED / DESIGN HOLD**, and
`SHA256SUMS.txt` verifies every retained upload/reference file. These checksums
prove artifact identity only. They are not permission to upload or order the
board.

The 2026-07-17 compact reroute and 2026-07-23 D1 correction superseded the
earlier 285x285 package. This is the first frozen package after both changes.

## Verified package facts

- The source PCB is four-layer, 200x200 mm, and routed.
- Current stable KiCad 10.0.5 checks report zero error-level DRC violations, zero
  unconnected items after refilling and saving both inner planes.
- Gerber/drill membership, deterministic ZIP metadata, checksums, drill count,
  and external rendering pass against the current package. The ZIP has 11
  deterministic-metadata members; Tracespace reports a 200000x200000 outline.
- The integrated export contains all ten Gerber/job files, one Excellon drill
  file with 887 matching PCB pad/via features, and all 119 position rows.
- Draft BOM/CPL, manual-install, socket-insertion, orientation, and review
  artifacts exist.
- The routed board is 119 refs / 135 nets, filled In1.Cu GND and In2.Cu VCC
  planes, 29 factory BOM rows, 96 CPL placements, 23 manual placements, and 22
  post-assembly socket insertions. The committed copper has 2,877 tracks/vias
  after the 200x200 reroute and bounded D1 clearance correction.
- The behavioral aggregate passes both real-ROM CPU
  implementations, dual decode modes, framebuffer readback, U24 timing, LVS,
  physical-model, footprint, PCB, and DRAM guards. The current-source full DRC
  and D1-specific static guard also pass.

## Release blockers

- T80 and tv80 VJUGA tops boot the patched real Juku firmware and match cosim's
  framebuffer at 6000 writes (`sim/boot_check.sh` and
  `sim/vjuga_boot_check.sh`); physical-board boot remains untested.
- The current routed copper includes every Phase 3 socket/header and retains
  filled GND/VCC inner planes. The current post-D1 source passes full KiCad
  10.0.5 DRC at zero violations/unconnected items as well as the
  dedicated static clearance/continuity guard. The frozen Gerber package now
  matches this route; vendor preview and independent human review remain open.
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
   current saved fills pass full KiCad 10.0.5 DRC with zero error-level
   violations or unconnected items. The router runs on Linux and macOS (fork
   jar + JDK 25).
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
6. **Regenerate + freeze the fab package (README gate 7) — DONE 2026-07-23:**
   the matching stable KiCad 10.0.5 CLI/`pcbnew` pipeline completed with every
   machine gate passing. The current ZIP SHA-256 is recorded above.
   REMAINING: vendor DFM/preview plus live stock and assembly-capability review
   at order time.
Two independently authored physical-LVS stages pass. Stage 1 covers all POWER
and CLOCK_RESET placement refs, J93, and the U1 clock/reset/power boundary (17
refs / 9 partitions). Stage 2 closes all 22 decode socket/glue parts plus six
exact non-power boundary projections (28 refs / 37 partitions / 5 NC pads).
Both require mutation controls; exact scope is `rev-a-lvs-coverage.md`. Before
order, finish the remaining staged full-board LVS groups (twin ↔ board), or
record a specific owner waiver backed by independent schematic, selected-part
pinout, and copper review. This is exactly the check that catches a mis-bound
pin before it is etched; the two stages and narrower direct contracts do not
make the remaining coverage optional.

Regenerate the package after every source change. Only change this status to a
release state after the functional and review gates in `../README.md` are
closed. Until then: **do not upload, order, or pay for this board**.
