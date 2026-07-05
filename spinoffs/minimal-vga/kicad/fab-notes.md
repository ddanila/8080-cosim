# Fabrication notes

Status: **routed fabrication-output baseline; not buy-ready yet**.

The current default KiCad file is a connectivity/LVS scaffold generated from
`minimal-vga.board.json`. `rev-a-physical.board.json` and
`rev-a-physical.kicad_pcb` are the first physical chip/footprint targets. The
current committed PCB is a FreeRouting-routed baseline generated from the Rev A
physical target.

Current routed baseline: KiCad reports zero error-level DRC violations and zero
unconnected items. `export_fab.sh` exports Gerbers, Excellon drill, fabrication
notes, the engineering BOM, review PDFs, and draft JLCPCB assembly files.

Factory assembly scope: populate sockets, passives, connectors, protection
parts, oscillator/reset, and diagnostic LEDs where practical. Do not include
Z80, ROM, DRAM, 8255, GAL/PAL, or other socketed ICs as factory-populated IC
parts; insert those manually after the assembled board is received.

## Intended Rev A Fabrication Defaults

- 4-layer PCB.
- Layer proposal:
  - L1: components and signals.
  - L2: signals / future GND pour candidate.
  - L3: signals / future +5V pour candidate.
  - L4: signals.
- Current generator guard: `check_rev_a_pcb.py` requires `F.Cu`, `In1.Cu`,
  `In2.Cu`, and `B.Cu`.
- Current route baseline: `route_rev_a_pcb.sh` uses `MINIMAL_VGA_NO_ZONES=1`
  and routes power explicitly. The earlier placeholder `GND`/`VCC` planes made
  FreeRouting/KiCad produce split VCC islands, so production pours should be
  reintroduced only after a focused power-plane review.
- The routing script defaults to a clean no-seed FreeRouting run
  (`SEED_ROUTES=0`) using the repo submodule fork jar from
  `external/freerouting` when it has been built. It defaults to
  `FREEROUTING_ALGORITHM=freerouting-router-v19`, using the custom fork's
  headless legacy-router selection as the current workaround for upstream v2.x
  routing-quality regressions. Set `FREEROUTING_ALGORITHM=freerouting-router`
  only for comparison runs. Earlier deterministic seed routes remain available
  for debug with `SEED_ROUTES=1`, but the current Rev A netlist routes cleanly
  without them and avoids carrying stale hand routes across topology changes.
- `JAVA_HEAP=auto` is the default for routing and maps to about 70% of available
  RAM (`-Xmx...`) on Linux/macOS. Set `JAVA_HEAP`, for example `JAVA_HEAP=8g`,
  to override this for controlled experiments.
- Board thickness: 1.6 mm unless mechanical constraints change.
- Copper: 1 oz default.
- Soldermask: any.
- Silkscreen: both sides useful for debug. Generated board-owned silkscreen
  labels use the same default KiCad stroke text style as footprint
  reference/value labels.
- Assembly: factory assembly target for passives, sockets, connectors, and
  protection parts where practical; owner-supplied IC insertion where needed.
- Diagnostics: first-pass LED bank for +5V, PWR_OK, CLK, RESET_N, M1_N
  instruction fetch, and RFSH_N refresh activity.

## Files Needed Before Ordering

PCB fabrication:

- Routed `.kicad_pcb`.
- Final KiCad schematic using real library symbols and finalized GAL/header
  pinouts.
- Final routed `rev-a-physical.kicad_pcb`, regenerated after GAL/header pinouts
  and passives are frozen.
- Gerber set.
- Excellon drill files.
- JLCPCB upload fabrication archive:
  `upload/vjuga-rev-a-gerbers-drill.zip`.
- Edge.Cuts outline.
- Fabrication notes with layer stack.
- Schematic PDF for review.
- Front/back assembly PDFs for orientation review.

Factory assembly:

- Engineering BOM: `rev-a.engineering-bom.csv` in the final fab export.
- JLCPCB upload BOM: `assembly/jlcpcb-bom-draft.csv`, generated from the
  physical PCB and engineering BOM.
- JLCPCB upload CPL: `assembly/jlcpcb-cpl-draft.csv`, generated from the same
  physical PCB.
- Upload-directory BOM/CPL copies:
  `upload/vjuga-rev-a-jlcpcb-bom.csv` and
  `upload/vjuga-rev-a-jlcpcb-cpl.csv`.
- Manual assembly list: `assembly/manual-assembly.csv`, generated from rows
  marked `Manual`, `DNP`, or `Do not populate` in the engineering BOM.
- Post-assembly insertion list: `assembly/post-assembly-insertion.csv`.
- Assembly readiness report: `assembly/assembly-readiness.md`.
- Socket-fit readiness report: `assembly/socket-fit-readiness.md`.
- Schematic ERC readiness report: `erc-readiness.md`.
- Order readiness report: `order-readiness.md`.
- Upload package manifest: `upload/package-manifest.md`.
- Upload package checksum list: `upload/SHA256SUMS.txt`.
- Position file: `assembly/rev-a-position.csv`.
- Order-time CPN checklist: `assembly/rev-a-jlcpcb-cpn-checklist.csv`.
- Assembly/orientation notes: `assembly/rev-a-assembly-orientation-notes.md`.
- Assembly drawings.
- Manual/DNP list.
- Polarity/orientation notes.
- Socket orientation notes for every socketed DIP device.
- Owner-supplied/post-assembly insertion notes for Z80, ROM, DRAM, 8255, and
  GAL/PAL devices if those parts are not factory-sourced.

## Pre-Order Checks

- `spinoffs/minimal-vga/sim/check.sh`
- `spinoffs/minimal-vga/sync/check.sh`
- `spinoffs/minimal-vga/kicad/route_rev_a_pcb.sh` when regenerating the routed
  baseline.
- `spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py`
- KiCad ERC.
- KiCad DRC.
- Zero unrouted nets.
- `export_fab.sh` blocks export unless KiCad ERC and DRC exit cleanly.
  Override only for debug artifacts with `MINIMAL_VGA_ALLOW_ERC_EXPORT=1` or
  `MINIMAL_VGA_ALLOW_DRC_EXPORT=1`.
- `export_fab.sh` emits the generated JLCPCB BOM/CPL pair only after the ERC
  and DRC gates, so a real order package cannot silently use a stale schematic
  or position file.
- `export_fab.sh` rebuilds `upload/` on every run with a deterministic
  Gerber/drill ZIP, upload-named BOM/CPL CSV copies, upload notes, SHA256
  checksums, and a package manifest.
- `export_fab.sh` also emits `review/rev-a-physical-schematic.pdf`,
  `review/rev-a-assembly-front.pdf`, and `review/rev-a-assembly-back.pdf`.
- `render_previews.sh` emits top-view PNG previews:
  `review/rev-a-top-bare.png` and `review/rev-a-top-populated.png`.
- `render_placement_preview.sh` emits a fast unrouted placement/silkscreen
  review from the generator:
  `review/vjuga-placement-top.svg` and `review/vjuga-placement-top.png`.
- `report_rev_a_source_model.py` writes
  `fab/minimal-vga/source-model-readiness.md`, recording the Rev A physical
  source-model ref/net/pin-binding coverage and explicit no-connect policy
  before schematic export.
- `report_rev_a_router_readiness.py` writes
  `fab/minimal-vga/router-readiness.md`, recording that the VJUGA autoroute
  path uses the `external/freerouting` custom branch, its built executable jar,
  and the headless v1.9 scheduler selection used as the current #508 workaround.
- `report_rev_a_behavioral_readiness.py` writes
  `fab/minimal-vga/behavioral-readiness.md`, running the spin-off simulator
  entry point and recording the ROM/cosim boot oracle, T80 smoke test,
  schematic/HDL LVS, physical checks, PCB scaffold, DRC summary, and DRAM unit
  test markers.
- `report_rev_a_fab_readiness.sh` writes the current DRC/unconnected summary to
  `fab/minimal-vga/fab-readiness.md`.
- `report_rev_a_routing_geometry.py` writes
  `fab/minimal-vga/routing-geometry-readiness.md`, summarizing track widths,
  vias, power-net routing, and zone policy. It catches hard geometry
  regressions while keeping power-width and return-path review explicit.
- `report_rev_a_mounting_holes.py` writes
  `fab/minimal-vga/mounting-hole-readiness.md`, checking the generated Rev A
  corner mounting holes, 3.2 mm diameter, edge web, footprint clearance, and
  routed-track clearance before Gerber packaging.
- `report_rev_a_fab_package_integrity.py` writes
  `fab/minimal-vga/fab-package-integrity.md`, verifying the Gerber/drill ZIP
  member list, deterministic ZIP metadata, source-file format markers, and
  `SHA256SUMS.txt` entries before human Gerber review.
- `report_rev_a_erc_readiness.sh` writes the current schematic ERC summary to
  `fab/minimal-vga/erc-readiness.md`. ERC should remain clean before ordering;
  human schematic review still applies. The cleanup history is tracked in
  `../docs/rev-a-erc-cleanup.md`.
- `report_rev_a_order_readiness.py` writes
  `fab/minimal-vga/order-readiness.md`, combining ERC, DRC, assembly, upload
  package, artifact, manual-row, and post-assembly-insertion status with the
  remaining human sign-off checklist.
- `report_rev_a_manual_rows.py` writes
  `fab/minimal-vga/assembly/manual-row-readiness.md`, recording the explicit
  disposition for every row excluded from factory assembly and failing if a new
  unclassified manual row appears.
- `report_rev_a_cpn_consistency.py` writes
  `fab/minimal-vga/assembly/cpn-consistency.md`, cross-checking the generated
  JLCPCB BOM CPNs against the engineering BOM and CPN checklist.
- `export_jlcpcb_assembly.py` excludes engineering BOM rows marked `Manual`,
  `DNP`, or `Do not populate` from the factory BOM/CPL and writes them to
  `assembly/manual-assembly.csv`.
- `report_rev_a_socket_fit.py` checks every socketed `U*` footprint against the
  engineering BOM's expected DIP pin count and socket width before the order
  readiness report is emitted.
- `report_rev_a_socket_insertion_policy.py` writes
  `fab/minimal-vga/assembly/socket-insertion-policy.md`, verifying that
  socketed `U*` rows are factory socket placements, not IC placements, and that
  every owner-supplied IC appears in the post-assembly insertion list.
- Visual inspection of Gerbers in an independent viewer.
- Confirm all socket footprints match actual sockets and IC widths.
- Assign and re-check JLCPCB/LCSC SKUs for factory-mounted sockets, passives,
  connectors, oscillator/reset, and protection parts immediately before order.
- The Rev A draft package deliberately leaves `D1`, `J30`, `R6`, `R15`, `U50`,
  and `U51` as manual/non-factory placements until their CPNs or footprint
  changes are selected. The generated manual-row readiness report gates that
  this exact set is known and classified. `C50`, `J40`, `J90`-`J93`, and `U40`
  have factory candidates but still need order-time fit and assembly-process
  review.
- Confirm whether the selected factory assembly process will mount the intended
  through-hole sockets/connectors or requires those parts to be left manual.
- Confirm J1 terminal/header and J3 USB-C footprints against the exact selected
  parts; verify F1 current rating/lead spacing and D1 TVS rating/footprint
  against the target supply.
- Confirm reset supervisor source/package and oscillator package before
  ordering.
- Review autorouted trace geometry, via count, power widths, and return paths.
- Decide whether to restore GND/+5V pours after routing cleanup.
- Program U5/U24 from `../docs/rev-a-gal-equations.md` or update that file
  before ordering if the equations change.

## JLCPCB Assembly File Policy

Do not upload `rev-a.bom.csv` directly as the factory BOM. That file is the
engineering BOM and keeps design intent such as "Z80 CPU" at `U1`.

The generated JLCPCB BOM instead treats socketed DIP footprints as sockets to
be factory-mounted at the `U*` designators. The matching post-assembly list
then records which owner-supplied IC should be inserted into each socket after
the board comes back from assembly.

Socket BOM rows intentionally omit the IC manufacturer part number. For
example, `U1` in the JLCPCB BOM means "DIP-40 socket at U1", while the Z80 CPU
itself appears only in `post-assembly-insertion.csv`.

The generated BOM and CPL must have the same designator set. This follows
JLCPCB's current BOM/CPL guidance and is checked by
`export_jlcpcb_assembly.py`.
