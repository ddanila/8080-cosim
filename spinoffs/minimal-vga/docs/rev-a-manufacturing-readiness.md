# VJUGA Rev A manufacturing readiness

Status: **DESIGN HOLD / PACKAGE REGENERATION REQUIRED**.

Rev A remains the monolithic workbench design. The current order target is the
[Rev B five-board system](rev-b-five-board-order-plan.md). This report does not
authorize fabrication of either design.

## Source and package identity

The recorded Rev A PCB is four-layer, 200×200 mm, with 119 refs / 133 nets
and 2,887 F.Cu/B.Cu tracks (segments plus vias), with
filled In1.Cu GND and In2.Cu VCC planes:

- Source: `spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb`
- SHA-256: `1326703605818b168dff3fd9f0879d36f8494393e8f8567ca7894061c7419650`
- [Recorded source DRC](rev-a-drc-readiness.md): KiCad 10.0.6, zero error-level
  violations and zero unconnected items after saved inner-plane fills.

The historical fabrication export predates corrections to the U20/U21 mux
enables and U22 refresh counter. Its upload ZIP is absent from the current
workspace and is not tracked. Regenerate the package from the accepted source
and complete independent review before vendor preview.

## Implemented checks

Real-ROM T80/tv80 boot comparisons at 6000 writes are guarded by
`sim/boot_check.sh` and `sim/vjuga_boot_check.sh`. The two decode modes and
framebuffer capture replay also have executable gates.
U24's DRAM timing contract passes the modeled CPU, refresh, video
and collision checks at 4 MHz (`sim/u24_dram_timing_check.sh`). Nine physical LVS slices
are recorded in [the coverage guide](rev-a-lvs-coverage.md); whole-board coverage
is incomplete. Simulation and source/route checks do not establish physical
boot, signal integrity or programmed-GAL behavior.

The source uses grounded U20/U21 active-low enables and U22 active-high resets,
with U22.6 cascaded to U22.13. The exact-part candidates for
[USB-C](rev-a-usb-c-candidate.md), [PTC](rev-a-ptc-candidate.md) and
[TVS](rev-a-tvs-candidate.md) have static contracts. First-article orientation,
thermal/load and surge qualification remain separate.

## Remaining release requirements

1. Complete the physical CPU-column and video-address paths described in
   [the chip map](rev-a-chip-map.md#dram-and-arbitration). The current U20/U21
   inputs carry only CPU A0–A7 and refresh-row outputs; zero DRC opens and
   matching LVS do not establish a working full DRAM address path.
2. Finish remaining physical LVS groups, or record an explicit owner waiver
   supported by independent schematic, selected-part pinout and copper review.
3. Compile U5/U24 for the selected GAL devices; retain fuse identities and
   independent programmed-device readbacks, then validate their timing.
4. Resolve the physical video acceptance scope. The framebuffer oracle checks
   captured memory writes; it does not qualify an electrical VGA output.
5. Review socket orientation, connector fit, selected-part compatibility,
   power/return paths and protection limits. Recheck stock and assembly support
   at order time.
6. Regenerate Gerber/drill and assembly outputs from the accepted source; rerun
   package integrity/render checks, record new hashes, and complete independent
   review and vendor DFM/preview.
Follow [fabrication notes](../kicad/fab-notes.md) for the export workflow and
[the sourcing policy](rev-a-sourcing-plan.md) for assembly responsibilities.
Until the functional and review gates are closed: **do not upload, order, or
pay for this board**.

## Acceptance after fabrication

After an authorized order is received and the board is assembled, perform
staged physical acceptance using [the Rev A bench procedure](phase4-bench-bringup.md).
Design/package release permits ordering; it does not establish physical
boot, signal integrity or acceptance of the assembled unit.
