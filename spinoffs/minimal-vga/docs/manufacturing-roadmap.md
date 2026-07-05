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
  `external/freerouting/build/libs/freerouting-current-executable.jar`.
- Freerouting caveats carried over from the main juku board (2026-07):
  (a) stock v2.x headless/CLI routing has had board-specific settings gaps
  (upstream discussion #508); the repo submodule fork's `custom` branch applies
  board-specific optimizations in the headless load/scheduler path and is the
  preferred router for VJUGA;
  (b) **duplicate footprint references make `ExportSpecctraDSN` fail silently**
  (returns False, no diagnostics) — the script now pre-checks and fails loudly;
  (c) the script prefers the repo submodule fork jar (ddanila/freerouting
  `custom`: PolylineTrace.combine recursion fix, headless settings application,
  and stagnation tuning) when built;
  (d) wrappers use `scripts/find-kicad-python.sh` so the KiCad `pcbnew` module
  is loaded from a compatible interpreter even when Homebrew or another Python
  appears first in `PATH`.
- `check_rev_a_pcb.py` rejects accidental layer-count regressions before the
  fabrication exporter is allowed to run.
- `report_rev_a_erc_readiness.sh` records the current KiCad ERC status for the
  physical schematic. It is non-gating until generated unused pins and
  intentional no-connects are explicitly resolved; the current cleanup list is
  tracked in `rev-a-erc-cleanup.md`.
- `report_rev_a_fab_readiness.sh` produces a non-gating DRC/unconnected summary
  in `fab/minimal-vga/fab-readiness.md`.
- `export_jlcpcb_assembly.py` produces a draft JLCPCB BOM/CPL pair from the
  generated PCB plus engineering BOM and rejects BOM/CPL designator mismatches.
  It also writes an assembly-readiness report that counts missing LCSC part
  numbers and unresolved TBD sourcing rows.
- The engineering BOM now carries socket CPNs for socketed `U*` footprints and
  current candidate CPNs for many passives, USB-C, J1, reset, fuse, decouplers,
  and LEDs. The generated assembly readiness report now has zero missing LCSC
  part numbers in the factory BOM/CPL subset, with 12 deliberate manual rows.
- Current routed baseline has zero KiCad error-level DRC violations and zero
  unconnected items after the Rev A source-model ERC cleanup and a clean
  no-seed FreeRouting run.
- Current physical source/routed PCB counts: 95 schematic refs, 116 source
  nets, 95 PCB footprints, 117 KiCad PCB nets, and 2083 routed tracks. The PCB
  net count includes KiCad-generated net bookkeeping beyond the source-model
  named nets.
- Current draft JLCPCB export: 22 factory BOM rows, 83 CPL placements, 19
  post-assembly socketed IC insertions, and 12 deliberate manual placements.
- `export_fab.sh` now exports Gerbers, Excellon drill, fab notes, engineering
  BOM, and draft JLCPCB assembly files from the routed board.

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
JLCPCB BOM/CPL files. This is still not a buy-ready design because sourcing,
connector, and manual layout review gates remain open.

Treat this route as a physical manufacturability smoke test, not logical proof
that VJUGA boots or that the DRAM/refresh/video handoff is correct. Production
copper polish should wait until cosim and schematic review have frozen the
netlist enough that routing churn is unlikely.

Open production blockers:

- Fix or explicitly mark remaining schematic ERC findings; the current report
  is generated as `fab/minimal-vga/erc-readiness.md`, with the cleanup plan in
  `rev-a-erc-cleanup.md`.
- Decide whether the Rev A manual rows (`C50`, `D1`, `J30`, `J40`, `J90-J93`,
  `R6`, `R15`, `U40`, and `U50`) stay owner-installed or get factory CPNs /
  footprint changes before ordering.
- Re-check assigned candidate CPNs immediately before order and confirm
  footprint fit for the mechanically sensitive rows: J1, F1, U51, and R30-R31.
- Review autorouted traces, power widths, via count, and return paths.
- Decide whether GND/+5V pours return after manual cleanup.
- Do final Gerber inspection in an independent viewer.
- Confirm all socket footprints match the exact socket widths selected for
  factory assembly.
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

### Gate 5: Factory Assembly Order Package

Status: draft package generated; not order-ready.

PCB fabrication package:

- Gerbers.
- Excellon drill files.
- Fabrication notes.
- Schematic PDF.

Factory assembly package:

- JLCPCB BOM generated from the board, with manufacturer part numbers and
  JLCPCB/LCSC candidate part numbers.
- JLCPCB CPL/position file generated from the same board.
- ERC readiness report generated from the physical schematic.
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
