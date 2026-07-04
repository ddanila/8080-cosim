# Manufacturing roadmap

Goal: get the minimal VGA spin-off from verified behavior to a bare PCB order
package without losing the simulator/LVS safety net.

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

Remaining work:

- Freeze GAL equations and header/connector pinouts.
- Bind the generated schematic to final KiCad library symbols instead of
  generated local symbols.
- Confirm the final keyboard connector pinout against the intended keyboard
  module.

### Gate 3: Physical PCB Scaffold

Status: 4-layer placement/ratsnest scaffold, not routed.

- `gen_rev_a_pcb.py` generates `rev-a-physical.kicad_pcb` with stock KiCad
  footprints.
- The generator emits the intended Rev A copper stack: `F.Cu`, `In1.Cu`,
  `In2.Cu`, and `B.Cu`.
- The generator adds and fills inner-layer placeholders for `GND` on `In1.Cu`
  and `VCC` on `In2.Cu`.
- `check_rev_a_pcb.py` rejects accidental layer-count regressions before the
  fabrication exporter is allowed to run.
- `report_rev_a_fab_readiness.sh` produces a non-gating DRC/unconnected summary
  in `fab/minimal-vga/fab-readiness.md`.
- Current generated placement has zero error-level DRC violations after filling
  the power zones; the readiness report still shows signal ratsnest
  connections.
- The PCB scaffold is useful for footprint availability, board sizing, connector
  placement, and routing feasibility.

Remaining work:

- Re-run after GAL/header pinouts and the final keyboard connector are frozen.
- Choose final connector footprints.
- Review production GND and +5V copper zones after routing constraints are
  settled.
- Refine mechanical constraints and mounting holes.
- Route the board.

### Gate 4: Fabrication Candidate

Status: not reached.

Required before ordering:

- KiCad ERC passes.
- KiCad DRC passes.
- Logical HDL/KiCad LVS still passes.
- Rev A physical checker passes.
- Routed PCB has no unrouted nets.
- Gerbers and Excellon drill files export cleanly.
- Gerbers are visually inspected in an independent viewer.
- BOM uses orderable parts or clearly marks manual/socketed/DNP items.

### Gate 5: Order Package

Status: not reached.

Bare PCB package:

- Gerbers.
- Excellon drill files.
- Fabrication notes.
- Schematic PDF.
- BOM for manual assembly planning.

Factory assembly package, if later wanted:

- BOM with manufacturer part numbers.
- CPL/position file.
- Assembly drawings.
- DNP list.
- Polarity and socket orientation notes.
