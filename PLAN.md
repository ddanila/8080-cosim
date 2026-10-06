# Juku reconstruction plan

Release status: **DESIGN HOLD / PACKAGE REGENERATION REQUIRED**.

The runnable model executes the adopted ROM and has guarded bus and framebuffer
agreement with the software oracle for selected workloads; see the
[runtime reference](docs/cosim-runtime-reference.md) for coverage limits. The
physical replica still needs source closure, placement/routing repair, parts
review and a regenerated fabrication package. The tracked `fab/gerbers` files
are review evidence; the upload ZIP is absent and fabrication is not authorized.

## Current priorities

1. Close the hidden or conflicting connectivity listed in the
   [owner measurement shortlist](docs/owner-measurement-shortlist.md). Accept
   drawing/photo evidence only within its recorded scope; use continuity or
   powered captures for paths the archive cannot resolve.
2. Resolve the remaining READY/WAIT, FDC support, bus-direction and shared
   memory/video timing boundaries. The
   [fidelity ledger](docs/board-fidelity-gap-ledger.md) and
   [bring-up points](docs/replica-bringup-verification-points.md) own the current
   endpoint inventory and source-risk counts.
3. Fit the physical package and landing geometry before routing. PPI
   orientation, D42/D43/D58, X9 landings, X8 electrolytics and factory insulated
   wires have explicit source/placement limits in their linked evidence.
4. Refresh the routed board from the corrected source and repair copper.
   [Routed refresh](docs/routed-refresh-audit.md) defines reusable copper;
   [factory-wire fidelity](docs/factory-wire-route-fidelity.md) owns the current
   source/routed drift. A historical zero-open snapshot is not a release.
5. Complete the [sourcing decision](docs/replica-sourcing-readiness.md),
   regenerate and review the exact package, and pass the
   [manufacturing release gate](docs/replica-manufacturing-readiness.md).

The adopted four small-PROM tables and D15/D16 firmware pair are verified in
[the firmware ledger](docs/firmware-gap-ledger.md). Cartridge BASIC remains a
separate [artifact boundary](docs/cartridge-basic-boundary.md).

## Release criteria

- Historical source gaps affecting boot, bus direction, memory, interrupts or
  video are closed by evidence or an explicitly accepted redesign.
- Source model, schematic, physical pads, factory wires and routed copper agree.
  DRC and ERC must report the intended circuit, not an incomplete approximation.
- The exact Gerber/drill ZIP, source stamp, checksums, visual review, part
  substitutions and order evidence pass `kicad/check_replica_manufacturing_ready.sh`.
- Vendor review and an explicit order decision precede payment. Passing CI or
  packaging the evidence archive alone does not authorize fabrication.

## Physical acceptance

Tier 1 checks controlled power-up, clock/reset, ROM/RAM and serial bootstrap.
Tier 2 checks keyboard, disk, interrupts, display and sound against the accepted
workloads. Tier 3 compares physical continuity and timing with a surviving
`.009` board. A behavioral pass does not establish Tier 3 authenticity.
Use the [first-article record](docs/replica-first-article-record.md) for the
actual assembled board and staged power-up evidence.

- [ ] P0 physical connectivity is complete and rerouted.
- [ ] Main-board design release passes; board is ordered.
- [ ] Functional parts kit is received and tested.
- [ ] Replica completes Tier 1 bring-up.
- [ ] Replica completes Tier 2.
- [ ] Replica completes Tier 3.

## Parallel projects

| Project | Current scope and next boundary |
| --- | --- |
| Portable network host | C runtime is implemented; [platform qualification](docs/portable-c-host-plan.md) retains the physical DOS, macOS and Windows gates |
| Windows GUI | [Juku Host](docs/windows-jukuhost-client.md) supports stock/C11/C12; physical serial/GUI/endurance qualification remains |
| Jukuravi | [Diagnostic firmware and physical evidence](spinoffs/jukuravi/README.md); D55 diagnosis uses the clocked T34 policy |
| VJUGA | [Rev A](spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md) and [modular Rev B](spinoffs/minimal-vga/docs/rev-b-status.md) keep separate hardware/release gates |
| JukuPoly | [PIT music engine](spinoffs/jukupoly/README.md), independent of replica release |
| Composite/CRT model | [Remaining waveform and receiver work](docs/crt-cvbs-simulation-plan.md), gated by source-complete physical slot timing |

## Working rules

Work and publish on `master` in the user's fork. Keep source provenance and
explicit unknowns; do not infer hidden wiring from the runnable twin. Update
report writers and regenerate their output with the source change. Use
[development workflow](docs/development-workflow.md) and
[verification commands](sync/README.md) for checks appropriate to each change.
