# VJUGA spin-off

This spin-off is a correctness-first Juku-compatible motherboard experiment:
keep the original CPU, ROM, RAM, DRAM refresh/timing, and keyboard decode
behavior, but remove peripherals that are not needed to prove the core boot path.

The goal is a smaller, socketed, easier-to-debug board that still runs the real
Juku ROM firmware and is checked by the same simulation/LVS discipline as the
main project.

## Scope

Included:

- CPU bring-up path:
  - first prototype: Z80-native, +5V-only bus control;
  - later prototype: Z80-to-Juku/8080-style bus adapter.
- Original-style ROM mapping using the recovered Juku ROM images from
  `../../roms/`.
- One populated 64K x 8 DRAM bank using eight K565RU5-class 64K x 1 parts.
- Original-style DRAM address multiplexing, refresh, RAS/CAS, and write timing.
- Original-style keyboard matrix decode path: 8255 PPI column select plus 74148
  row encoder semantics.
- VGA output using onboard TTL640x480-derived sync/blanking logic as the display
  timing target.
- ATX connector power entry, plus any local rail generation required by the
  original chips.
- Socketed western ICs, with a real DIP Z80 for Rev A.
- Factory assembly target for passives, sockets, connectors, and protection
  parts where practical.
- Multi-layer PCB allowed. The board is not constrained to the original 2-layer
  mechanical reproduction.

Excluded:

- FDC / WD1793 and floppy connector.
- External bus, serial/tape/network/mouse connectors unless later needed for a
  firmware path.
- Historical component placement and original board dimensions.
- RF/composite video output chain, except where its logic is needed to feed the
  VGA path.

## Doability

Yes, this is doable, and it is a better proof board than the full replica for
testing the method:

- The existing project already boots real Juku ROMs in both `cosim/` and HDL.
- Keyboard behavior is already modeled from the 8255/74148 scan protocol.
- A K565RU5/4164-style row/column DRAM unit test already exists.
- A Z80 first stage removes the 8080 `+12V`/`-5V` CPU rail problem.
- The risky part is not the missing FDC or the CPU substitution. The risky part
  is preserving enough of the original DRAM/video timing so the firmware-visible
  RAM and display behavior remain correct.

## CPU Strategy

Use a progressive design:

1. **Option 1: Z80-native core board.**
   The Z80 drives a small memory/IO bus adapter using native `MREQ`, `IORQ`,
   `RD`, `WR`, `M1`, and clock/reset semantics. This is the fastest path to a
   +5V-only prototype that can run 8080-compatible ROM code and prove the ROM,
   RAM, keyboard, and VGA-side flow.
2. **Option 2: Z80-to-Juku bus adapter.**
   Keep the same board-level memory, keyboard, DRAM, and VGA blocks, but replace
   the thin Z80-native adapter with logic that emits Juku/8080-style memory and
   IO strobes. This lets the DRAM refresh/video side remain the test subject.

Design rule: the DRAM subsystem must not depend on Z80 `RFSH` for normal
operation. `RFSH` may be observed or exposed for diagnostics, but the point of
this spin-off is to test the original-style DRAM refresh/timing path.

Rev A physical policy:

- CPU: real socketed DIP Z80.
- ROM: 27C256-class DIP-28 ROM footprint.
- DRAM: western 4164-compatible DIP-16 parts, 150 ns or faster initial target.
- Logic: western +5V TTL-compatible parts only; use GAL/PAL-style programmable
  logic for the first decode/timing iteration.

## Power

ATX is a useful input connector, but do not assume it directly supplies every
rail the original chips need.

Known from the current project notes:

- The 8080 CPU uses `+5V`, `+12V`, and `-5V`.
- The original board power connector evidence lists `-12V`, `+12V`, `+5V`, and
  `GND`.
- Modern ATX supplies normally provide `+3.3V`, `+5V`, `+12V`, `-12V`, and `5VSB`,
  but usually not `-5V`.
- The Z80 and 4164/K565RU5-style DRAM path can be made `+5V`-only.

Design assumption for this spin-off:

- Use ATX for `+5V`, `+12V`, `-12V`, `5VSB`, `GND`, and `PS_ON#`.
- For the Z80-first prototype, populate only `+5V` logic unless a later option
  explicitly needs another rail.
- Keep footprints/jumpers flexible enough that an 8080-family experiment could
  add local `-5V` later, but do not make it part of the first prototype.

## VGA Strategy

TTL640x480 is treated as the onboard VGA timing block:

- It provides 640x480 sync/blanking timing.
- The Juku memory/display side remains the source of character/framebuffer data.
- The bridge design must define how Juku video memory is sampled into a VGA-safe
  pixel/character stream without breaking CPU DRAM access or refresh.
- A header may remain for diagnostics, but the Rev A goal is not a daughterboard
  video timing dependency.

The simplest first simulation target is not a perfect video card. It is:

1. Boot real ROM.
2. Preserve DRAM contents and refresh semantics.
3. Accept keyboard input.
4. Produce a deterministic framebuffer/character output that can later be mapped
   onto TTL640x480 timing.

## Directory Layout

- `docs/` - design notes and decision records.
- `hdl/` - spin-off-specific HDL wrappers or extracted modules.
- `kicad/` - future KiCad project for the minimal board.
- `sim/` - simulation entry points for this spin-off.
- `external/` - notes for third-party design sources, not vendored by default.
- `sync/` - spin-off LVS checks.

Early manufacturing planning files live in `kicad/`:

- `../docs/manufacturing-roadmap.md` - gates from behavioral proof to order
  package.
- `../docs/rev-a-sourcing-plan.md` - JLCPCB/factory-assembly sourcing plan.
- `../docs/rev-a-erc-cleanup.md` - current schematic ERC blocker
  classification.
- `rev-a-physical.board.json` - first physical chip-level schematic target.
- `rev-a-physical.kicad_sch` - generated schematic from that physical target.
- `rev-a-physical.kicad_pcb` - generated placement/ratsnest PCB scaffold.
- `check_rev_a_physical.sh` - validates/generates the physical target.
- `check_rev_a_pcb.sh` - validates/generates the PCB scaffold with stock KiCad
  footprints and the intended 4-layer copper stack.
- `check_rev_a_pcb.py` - PCB scaffold invariant checks.
- `report_rev_a_erc_readiness.sh` - non-gating ERC summary for the current Rev
  A physical schematic.
- `render_placement_preview.sh` - fast placement/silkscreen preview from the
  generator without running FreeRouting or touching the routed PCB.
- `report_rev_a_fab_readiness.sh` - non-gating DRC/unconnected summary for the
  current PCB scaffold.
- `report_rev_a_order_readiness.py` - generated order checklist combining
  machine gates with remaining human review gates.
- `rev-a.bom.csv` - initial physical BOM skeleton.
- `fab-notes.md` - fabrication assumptions and pre-order checklist.
- `export_fab.sh` - ERC/DRC-gated Gerber, drill, review PDF, BOM/CPL, and
  readiness-report exporter.

Generated Rev A board-owned silkscreen labels use the same default KiCad stroke
text style as the footprint reference/value labels.

The selected Z80 HDL core is the `external/T80` git submodule. See
`external/Z80-core.md` and `hdl/README.md`.

## Simulator Entry Point

Run:

```sh
spinoffs/minimal-vga/sim/check.sh
```

Current requirements:

- `cc` for the C cosim build used by the main boot oracle.
- `ghdl` or another VHDL simulator for the T80 Z80 core.
- `iverilog` and `vvp` for the HDL boot and DRAM unit tests.
- `yosys` and `kicad-cli` later, once this spin-off has its own LVS target.

At this scaffold stage the script deliberately reuses the main project boot
oracle before a trimmed spin-off HDL top exists.

Run the spin-off schematic/HDL connectivity check:

```sh
spinoffs/minimal-vga/sync/check.sh
```

## First Milestones

1. Freeze the minimal chip/function list.
2. Build a Z80-native HDL top with a narrow CPU-to-memory/IO adapter boundary.
3. Run the existing ROM/cosim checks where instruction compatibility is enough,
   then add Z80-specific boot checks.
4. Replace flat RAM behavior with the row/column K565RU5 model and refresh
   timing.
5. Add the VGA timing bridge and a test that proves the boot banner or prompt is
   visible through the VGA-side model.
6. Replace the Z80-native adapter with a Juku/8080-style adapter and compare
   behavior.
7. Start the KiCad schematic once the HDL boundary is stable enough to LVS.
