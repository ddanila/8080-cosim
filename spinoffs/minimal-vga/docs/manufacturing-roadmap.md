# Manufacturing roadmap

Goal: get the VJUGA spin-off from verified behavior to a factory-assembly
order package without losing the simulator/LVS safety net.

## Gates

### Gate 1: Behavioral Proof

Status: passing.

- Real ROM boot oracle passes.
- T80/Z80 minimal top passes.
- DRAM row/column unit test passes.
- Logical KiCad schematic and HDL pass LVS.

Command:

```sh
spinoffs/minimal-vga/sim/check.sh
```

### Gate 2: Physical Schematic Target

Status: core target exists with partial real pin binding.

- `rev-a-physical.board.json` names the Rev A chips and nets.
- `rev-a-physical.kicad_sch` is generated from that target.
- `check_rev_a_physical.sh` validates endpoint consistency and regenerates the
  schematic.
- Z80, 28C256, 4164, 8255, and the selected 74xx support sockets use real DIP
  pin numbers from the local KiCad symbol library.
- First-pass oscillator, reset supervisor, pullups, VGA series resistors, bulk
  capacitance, and per-IC decoupling capacitors are explicit schematic/PCB
  parts.
- Rev A +5V can enter through a 2-pin terminal/header or power-only USB-C.
  Both feed `VCC_RAW`, which passes through resettable fuse `F1` to `VCC`;
  local TVS protection and a power debug header remain explicit.
- The first-pass +5V planning budget is documented in `rev-a-power-budget.md`.
- The Rev A placement style and decoupler placement rules are documented in
  `rev-a-placement-rules.md`; treat those rules as the placement review gate
  before spending time on production copper cleanup.
- Keyboard row inputs have explicit pullups, the 74148 enable input is tied
  active by default, and 8255 column outputs reach the keyboard connector
  through series resistors.
- Rev A decisions now target a real socketed DIP Z80, 27C256-class ROM,
  western 4164-compatible DRAM, a TTL640x480 bring-up timing header,
  western-only logic, GAL/PAL-style programmable decode/timing, and factory
  assembly of sockets/passives where practical.

Remaining work:

- GAL equations and pinouts are frozen for Rev A bring-up in
  `rev-a-gal-equations.md`.
- Bind the generated schematic to final KiCad library symbols instead of
  generated local symbols.
- Keyboard board connector is frozen for Rev A as a 1x15 inline 2.54 mm header;
  the external adapter wiring to the original keyboard remains owner-side
  bring-up work.
- U40 is frozen as a TTL640x480 bring-up/timing header for Rev A. Full onboard
  expansion of the TTL640x480 logic is deferred to the next PCB spin after the
  CPU/DRAM/refresh path is proven.

### Gate 3: Physical PCB Route Baseline

Status: routed FreeRouting baseline.

- `gen_rev_a_pcb.py` generates `rev-a-physical.kicad_pcb` with stock KiCad
  footprints.
- The generator emits the intended Rev A copper stack: `F.Cu`, `In1.Cu`,
  `In2.Cu`, and `B.Cu`.
- The generator can add filled inner-layer placeholders for `GND` on `In1.Cu`
  and `VCC` on `In2.Cu`; the current routed baseline was generated with
  `MINIMAL_VGA_NO_ZONES=1` and has explicit routed power instead.
- `route_rev_a_pcb.sh` regenerates a no-plane routing baseline, exports
  Specctra DSN, runs FreeRouting, imports the SES result, and checks KiCad DRC.
  The current default is `SEED_ROUTES=0`; deterministic route seeds are opt-in
  debug aids only. The preferred router is the `external/freerouting` submodule
  on the `custom` branch, built as
  `external/freerouting/build/libs/freerouting-current-executable.jar`. Route
  regeneration defaults to `FREEROUTING_ALGORITHM=freerouting-router-v19` as the
  current workaround for upstream v2.x routing-quality regressions; set
  `FREEROUTING_ALGORITHM=freerouting-router` only for comparison runs.
- Freerouting caveats carried over from the main juku board (2026-07):
  (a) stock v2.x headless/CLI routing has had board-specific settings gaps
  (upstream discussion #508); the repo submodule fork's `custom` branch applies
  board-specific optimizations in the headless load/scheduler path, honours the
  v1.9 router selection in headless mode, and is the preferred router for VJUGA;
  (b) **duplicate footprint references make `ExportSpecctraDSN` fail silently**
  (returns False, no diagnostics) — the script now pre-checks and fails loudly;
  (c) the script prefers the repo submodule fork jar (ddanila/freerouting
  `custom`: PolylineTrace.combine recursion fix, headless settings application,
  headless v1.9 router selection, and stagnation tuning) when built;
  (d) wrappers use `scripts/find-kicad-python.sh` so the KiCad `pcbnew` module
  is loaded from a compatible interpreter even when Homebrew or another Python
  appears first in `PATH`;
  (e) the routing wrapper defaults `JAVA_HEAP=auto`, which sets `-Xmx` to about
  70% of available RAM to reduce whole-machine OOM risk during experiments.
- `check_rev_a_pcb.py` rejects accidental layer-count regressions before the
  fabrication exporter is allowed to run.
- `report_rev_a_source_model.py` produces
  `fab/minimal-vga/source-model-readiness.md`, recording the Rev A physical
  source-model ref/net/pin-binding coverage and explicit no-connect policy
  before schematic export.
- `report_rev_a_router_readiness.py` produces
  `fab/minimal-vga/router-readiness.md`, recording the custom Freerouting
  submodule state and the fast checks behind the headless v1.9 route path used
  for the upstream #508 workaround.
- `report_rev_a_erc_readiness.sh` records the current KiCad ERC status for the
  physical schematic and exits nonzero if error-level ERC findings return. The
  Rev A source model now has explicit no-connect policy for unused pins; the
  cleanup history is tracked in `rev-a-erc-cleanup.md`.
- `report_rev_a_behavioral_readiness.py` produces
  `fab/minimal-vga/behavioral-readiness.md`, running the spin-off simulator
  entry point and recording the ROM/cosim boot oracle, T80 smoke test,
  schematic/HDL LVS, physical checks, PCB scaffold, DRC summary, and DRAM unit
  test markers.
- `report_rev_a_fab_readiness.sh` produces a non-gating DRC/unconnected summary
  in `fab/minimal-vga/fab-readiness.md`.
- `report_rev_a_routing_geometry.py` produces
  `fab/minimal-vga/routing-geometry-readiness.md`, recording track widths, via
  sizes/counts, power-net route statistics, and whether power planes/zones are
  present.
- `report_rev_a_fab_package_integrity.py` produces
  `fab/minimal-vga/fab-package-integrity.md`, verifying the upload Gerber/drill
  ZIP member list, deterministic ZIP metadata, source-file format markers, and
  `SHA256SUMS.txt` entries before independent visual Gerber review.
- `report_rev_a_order_readiness.py` produces
  `fab/minimal-vga/order-readiness.md`, which combines the ERC, DRC, assembly,
  upload package, artifact, manual-row, and post-assembly-insertion checks with
  the remaining human sign-off items.
- `report_rev_a_manual_rows.py` produces
  `fab/minimal-vga/assembly/manual-row-readiness.md`, checking that every
  manual/non-factory row is in the expected Rev A policy table and has an
  explicit disposition.
- `report_rev_a_cpn_consistency.py` produces
  `fab/minimal-vga/assembly/cpn-consistency.md`, checking factory-mounted CPNs
  across the generated JLCPCB BOM, the engineering BOM, and the sourcing
  checklist.
- `export_jlcpcb_assembly.py` produces a draft JLCPCB BOM/CPL pair from the
  generated PCB plus engineering BOM and rejects BOM/CPL designator mismatches.
  It also writes an assembly-readiness report that counts missing LCSC part
  numbers and unresolved TBD sourcing rows.
- `report_rev_a_socket_fit.py` writes
  `fab/minimal-vga/assembly/socket-fit-readiness.md`, checking each socketed
  `U*` footprint against the engineering BOM's expected DIP pin count and socket
  width.
- The engineering BOM now carries socket CPNs for socketed `U*` footprints and
  current candidate CPNs for many passives, USB-C, J1, fuse, decouplers, bulk
  capacitance, debug headers, and LEDs. The generated assembly readiness report
  now has zero missing LCSC part numbers in the factory BOM/CPL subset, with 6
  deliberate manual rows.
- Current routed baseline has zero KiCad error-level DRC violations and zero
  unconnected items after the Rev A source-model ERC cleanup and a clean
  no-seed FreeRouting run.
- Current behavioral readiness passes the spin-off simulator entry point:
  ROM/cosim boot oracle, T80 smoke test, logical schematic/HDL LVS, physical
  target checks, PCB scaffold check, DRC summary, and DRAM row/column unit.
- Current source-model readiness passes the Rev A required ref/net/pin-binding
  policy and records 38 explicit no-connect pins.
- Current router readiness passes the fast custom-fork checks: the submodule is
  on `custom`, the built fork jar is present, headless scheduler v1.9 selection
  is present, and `route_rev_a_pcb.sh` defaults to that path.
- Current routing-geometry report has zero hard geometry failures. It records
  the explicit no-zone baseline and flags 0.20 mm routed power traces for human
  review before ordering.
- Current fabrication-package integrity passes: the upload ZIP contains the 11
  expected Gerber/drill/job files, matches the exported sources, has
  deterministic ZIP metadata, and is covered by `SHA256SUMS.txt`.
- Current physical source/routed PCB counts: 95 schematic refs, 116 source
  nets, 95 PCB footprints, 117 KiCad PCB nets, and 2067 routed tracks. The PCB
  net count includes KiCad-generated net bookkeeping beyond the source-model
  named nets.
- Current draft JLCPCB export: 26 factory BOM rows, 89 CPL placements, 19
  post-assembly socketed IC insertions, and 6 deliberate manual placements.
- `export_fab.sh` now gates on both ERC and DRC before exporting Gerbers,
  Excellon drill, fab notes, engineering BOM, and draft JLCPCB assembly files
  from the routed board. It also rebuilds `fab/minimal-vga/upload/` with a
  deterministic Gerber/drill ZIP, upload-named BOM/CPL copies, notes,
  `SHA256SUMS.txt`, and `package-manifest.md`, then emits the root
  `order-readiness.md` for the upload review.

Remaining work:

- Choose final connector footprints.
- Review whether production Rev A should restore GND/+5V copper pours after the
  route is stable. The first autoroute with placeholder planes produced split
  VCC islands, so the committed route uses traces only for power connectivity.
- Refine mechanical constraints and mounting holes.
- Human-review and clean up the autorouted trace geometry before ordering.
- Review component placement against `rev-a-placement-rules.md` after any
  schematic/netlist change that moves CPU, ROM, DRAM, keyboard, VGA, or power
  ownership boundaries.
- Assign concrete JLCPCB/LCSC CPNs for factory-mounted sockets, passives,
  connectors, oscillator/reset, and protection parts.
- Confirm diagnostic LED colors and brightness/loading after part selection.

### Gate 4: Fabrication Candidate

Status: fabrication-output candidate.

The routed PCB passes KiCad DRC with zero unconnected items, and `export_fab.sh`
exports Gerbers/drills, schematic PDF, assembly PDFs, position data, and draft
JLCPCB BOM/CPL files. It also emits upload-ready fabrication and assembly file
names under `fab/minimal-vga/upload/`. `fab/minimal-vga/order-readiness.md` now
summarizes the machine gates and the remaining human sign-offs. This is still
not a buy-ready design because sourcing, connector, and manual layout review
gates remain open.

Treat this route as a physical manufacturability smoke test, not logical proof
that VJUGA boots or that the DRAM/refresh/video handoff is correct. Production
copper polish should wait until cosim and schematic review have frozen the
netlist enough that routing churn is unlikely.

Open production blockers:

- Keep schematic ERC clean after any further source-model changes and complete
  human schematic review; the current report is generated as
  `fab/minimal-vga/erc-readiness.md`.
- Decide whether the remaining Rev A manual rows (`D1`, `J30`, `R6`, `R15`,
  `U50`, and `U51`) stay owner-installed or get factory CPNs /
  footprint changes before ordering. The generated manual-row readiness report
  now verifies that this exact manual set is deliberate and classified.
- Re-check assigned candidate CPNs immediately before order and confirm
  footprint fit for the mechanically sensitive rows: J1 and R30-R31. F1 now has
  a footprint-matched Bourns MF-RG300-class candidate, but still needs final
  load/current review before upload. U51 is manual for Rev A unless a matching
  MCP130 F-bondout assembly CPN is found.
- Review autorouted traces, power widths, via count, and return paths.
- Decide whether GND/+5V pours return after manual cleanup.
- Do final Gerber inspection in an independent viewer.
- Confirm all socket footprints match the exact socket widths selected for
  factory assembly; the generated socket-fit report covers BOM/PCB pin-count
  and width consistency, but the exact purchased socket drawings still need
  order-time review.
- Confirm whether JLCPCB will assemble the chosen through-hole sockets and
  connectors, or whether some must move to manual insertion.

Required before ordering:

- KiCad ERC passes.
- KiCad DRC passes.
- Logical HDL/KiCad LVS still passes.
- Rev A physical checker passes.
- Routed PCB has no unrouted nets.
- Gerbers and Excellon drill files export cleanly.
- Gerbers are visually inspected in an independent viewer.
- Engineering BOM uses orderable parts or clearly marks manual/socketed/DNP
  items.
- JLCPCB draft BOM and CPL have identical designator sets.
- JLCPCB/LCSC candidate SKUs are assigned for every factory-mounted row, and
  rows without CPNs are deliberately marked manual/DNP before upload.
- Post-assembly insertion list names every socketed IC that should be installed
  after factory socket assembly.
- Socket-fit readiness report passes for every socketed `U*` footprint.
- Upload package manifest and SHA256 checksum list are regenerated from the
  current fab export.

### Gate 5: Factory Assembly Order Package

Status: draft package generated; not order-ready.

PCB fabrication package:

- Gerber/drill upload ZIP:
  `fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`.
- Fabrication notes.
- Schematic PDF.

Factory assembly package:

- JLCPCB BOM generated from the board, with manufacturer part numbers and
  JLCPCB/LCSC candidate part numbers:
  `fab/minimal-vga/upload/vjuga-rev-a-jlcpcb-bom.csv`.
- JLCPCB CPL/position file generated from the same board:
  `fab/minimal-vga/upload/vjuga-rev-a-jlcpcb-cpl.csv`.
- ERC readiness report generated from the physical schematic.
- Upload package manifest and checksum list.
- Manual assembly CSV for rows kept out of the factory BOM/CPL.
- Assembly drawings.
- Manual/DNP list.
- Polarity and socket orientation notes.
- Notes for owner-supplied post-assembly insertion of Z80, ROM, DRAM, 8255, and
  GAL/PAL devices if they are not factory-sourced.

Remaining order-package work:

- Keep every missing CPN row out of the factory BOM/CPL unless an orderable
  JLCPCB/LCSC part is selected immediately before upload.
- Verify factory assembly availability for selected through-hole sockets,
  headers, oscillator, reset supervisor, fuse, and TVS.
- Add explicit socket/polarity/orientation notes to the assembly package.
- Inspect Gerbers in an independent viewer and record the review result.
- Decide whether to order bare PCB first or accept factory assembly risk for
  Rev A sockets/passives/connectors.
