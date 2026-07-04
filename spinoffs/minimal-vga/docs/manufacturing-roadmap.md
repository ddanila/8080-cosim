# Manufacturing roadmap

Goal: get the minimal VGA spin-off from verified behavior to a factory-assembly
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
- ATX +5V now enters as `VCC_RAW`, passes through resettable fuse `F1` to
  `VCC`, and has a local TVS clamp plus PS_ON jumper/pullup and power debug
  header.
- Keyboard row inputs have explicit pullups, the 74148 enable input is tied
  active by default, and 8255 column outputs reach the keyboard connector
  through series resistors.
- Rev A decisions now target a real socketed DIP Z80, 27C256-class ROM,
  western 4164-compatible DRAM, onboard TTL640x480-derived VGA timing,
  western-only logic, GAL/PAL-style programmable decode/timing, and factory
  assembly of sockets/passives where practical.

Remaining work:

- Freeze GAL equations and header/connector pinouts.
- Bind the generated schematic to final KiCad library symbols instead of
  generated local symbols.
- Confirm the original keyboard connector pinout and mechanical connector.
- Replace the current TTL640x480 header placeholder with onboard timing logic.

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
- `check_rev_a_pcb.py` rejects accidental layer-count regressions before the
  fabrication exporter is allowed to run.
- `report_rev_a_fab_readiness.sh` produces a non-gating DRC/unconnected summary
  in `fab/minimal-vga/fab-readiness.md`.
- `export_jlcpcb_assembly.py` produces a draft JLCPCB BOM/CPL pair from the
  generated PCB plus engineering BOM and rejects BOM/CPL designator mismatches.
  It also writes an assembly-readiness report that counts missing LCSC part
  numbers and unresolved TBD sourcing rows.
- Current routed baseline has zero KiCad error-level DRC violations and zero
  unconnected items.
- `export_fab.sh` now exports Gerbers, Excellon drill, fab notes, engineering
  BOM, and draft JLCPCB assembly files from the routed board.

Remaining work:

- Re-run after GAL/header pinouts and the final keyboard connector are frozen.
- Choose final connector footprints.
- Review whether production Rev A should restore GND/+5V copper pours after the
  route is stable. The first autoroute with placeholder planes produced split
  VCC islands, so the committed route uses traces only for power connectivity.
- Refine mechanical constraints and mounting holes.
- Human-review and clean up the autorouted trace geometry before ordering.
- Assign concrete JLCPCB/LCSC CPNs for factory-mounted sockets, passives,
  connectors, oscillator/reset, and protection parts.

### Gate 4: Fabrication Candidate

Status: partially reached.

The routed PCB passes KiCad DRC and exports Gerbers/drills. This is still not a
buy-ready design because several electrical/mechanical decisions remain
placeholders.

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
- JLCPCB/LCSC candidate SKUs are assigned for factory-mounted sockets,
  passives, connectors, power/protection, oscillator, and reset parts.
- Post-assembly insertion list names every socketed IC that should be installed
  after factory socket assembly.

### Gate 5: Factory Assembly Order Package

Status: not reached.

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
