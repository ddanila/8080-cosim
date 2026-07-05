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
- Freerouting caveats carried over from the main juku board (2026-07):
  (a) v2.x **headless/CLI jobs skip the board-specific parameter optimizations**
  that GUI runs apply (upstream discussion #508) — this small board converges
  headless anyway, but if a rerun stagnates, route through the GUI;
  (b) **duplicate footprint references make `ExportSpecctraDSN` fail silently**
  (returns False, no diagnostics) — the script now pre-checks and fails loudly;
  (c) the script prefers the local fork jar (ddanila/freerouting `custom`:
  PolylineTrace.combine recursion fix + stagnation tuning) when built.
- `check_rev_a_pcb.py` rejects accidental layer-count regressions before the
  fabrication exporter is allowed to run.
- `report_rev_a_fab_readiness.sh` produces a non-gating DRC/unconnected summary
  in `fab/minimal-vga/fab-readiness.md`.
- `export_jlcpcb_assembly.py` produces a draft JLCPCB BOM/CPL pair from the
  generated PCB plus engineering BOM and rejects BOM/CPL designator mismatches.
  It also writes an assembly-readiness report that counts missing LCSC part
  numbers and unresolved TBD sourcing rows.
- The engineering BOM now carries socket CPNs for socketed `U*` footprints and
  current candidate CPNs for many passives, USB-C, J1, reset, fuse, decouplers,
  and LEDs. The generated assembly readiness report is down to 10 missing CPN
  rows.
- Current routed baseline has zero KiCad error-level DRC violations and zero
  unconnected items.
- `export_fab.sh` now exports Gerbers, Excellon drill, fab notes, engineering
  BOM, and draft JLCPCB assembly files from the routed board.

Remaining work:

- Choose final connector footprints.
- Review whether production Rev A should restore GND/+5V copper pours after the
  route is stable. The first autoroute with placeholder planes produced split
  VCC islands, so the committed route uses traces only for power connectivity.
- Refine mechanical constraints and mounting holes.
- Human-review and clean up the autorouted trace geometry before ordering.
- Assign concrete JLCPCB/LCSC CPNs for factory-mounted sockets, passives,
  connectors, oscillator/reset, and protection parts.
- Confirm diagnostic LED colors and brightness/loading after part selection.

### Gate 4: Fabrication Candidate

Status: fabrication-output candidate.

The routed PCB passes KiCad DRC and exports Gerbers/drills, schematic PDF,
assembly PDFs, position data, and draft JLCPCB BOM/CPL files. This is still not
a buy-ready design because sourcing, connector, and manual layout review gates
remain open.

Open production blockers:

- Assign the remaining generated JLCPCB/LCSC CPNs for C50, D1, J30, J40,
  J90-J93, R6, R15, U40, and U50.
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
- JLCPCB/LCSC candidate SKUs are assigned for every factory-mounted row, or
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
- Assembly drawings.
- DNP list.
- Polarity and socket orientation notes.
- Notes for owner-supplied post-assembly insertion of Z80, ROM, DRAM, 8255, and
  GAL/PAL devices if they are not factory-sourced.

Remaining order-package work:

- Replace every missing factory-populated CPN with an orderable JLCPCB/LCSC
  part selected immediately before upload, or mark that row manual/DNP.
- Verify factory assembly availability for selected through-hole sockets,
  headers, oscillator, reset supervisor, fuse, and TVS.
- Add explicit socket/polarity/orientation notes to the assembly package.
- Inspect Gerbers in an independent viewer and record the review result.
- Decide whether to order bare PCB first or accept factory assembly risk for
  Rev A sockets/passives/connectors.
