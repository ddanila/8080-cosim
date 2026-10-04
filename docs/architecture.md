# Architecture and verification boundaries

## Data flow

```text
factory drawings / photos / dumps / measurements
                       |
                       v
             kicad/juku.board.json
                 /             \
                v               v
      generated KiCad       source/routed PCB
         schematic          physical audits
                |
                v
       schematic netlist ---- LVS ---- structural HDL
       (or board JSON)                  hdl/juku_top.v
                                             |
                                             v
                                  behavioral regression
                                         vs cosim
```

The structural HDL is maintained independently from the board model. MAME is
a behavioral reference for interpreting the machine, rather than a runtime
participant in these comparisons. PCB copper and placement require separate
physical audits; the LVS path above does not inspect them.

Historical sources are authoritative; `board.json` is the machine-readable
working model. The generated KiCad schematic and the structural HDL are not two
freely editable sources that synchronize bidirectionally.

## LVS

`sync/check.sh` regenerates `kicad/juku.kicad_sch` from the board JSON and
elaborates `hdl/juku_top.v` into `hdl/juku_top.json` with Yosys. When KiCad's
netlist export succeeds, it writes `kicad/juku.net.xml` and compares that
export with the HDL. If the CLI is absent or export fails for any reason,
it compares the board JSON directly. Inspect the printed “real KiCad
round-trip” or “KiCad-free” line to identify which path ran; a fallback pass
does not validate schematic export.

Yosys treats device internals as black boxes. LVS checks mapped instance/pin
connections, not chip behavior. The wrapper also runs glyph coverage and
board-population checks, conditionally checks routed-board silkscreen overlap
when KiCad Python is available, and prints a provenance summary. These checks
do not constitute DRC or a complete physical release audit.

The comparison uses connectivity rather than net names: mapped endpoints are
equivalent when they are partitioned into the same nets. `sync/map.json`
contains the refdes/instance and pin/port mappings.

The comparator drops constant connections and nets with fewer than two
endpoints after mapping and exclusions. It therefore does not prove constant
straps, singleton ownership, or intentional no-connects for this main-board map.
Those need separate source and endpoint checks.

The current check is intentionally partial. Unmapped analog parts, placement-
only footprints, simulation-only ports, power-only ports, and omitted pins
are outside its proof. A green result does not establish full-board electrical
completeness.

## Runnable structural model

`hdl/juku_top.v` instantiates board-level chips and interconnect. Behavioral
models live in `hdl/devices.v`; simulation-only adjuncts supply bounded behavior
where the physical circuit is not yet known. `sync/lvs.py` explicitly excludes
those non-board ports from connectivity comparison.

The independent C implementation under `cosim/` is the fast behavioral oracle.
Lockstep/framebuffer and subsystem tests compare it with HDL. The vendored MAME
Juku driver in `ref/mame_juku.cpp` is an additional reference for memory/I/O maps, media geometry, and
raster behavior, but schematic/measurement evidence wins when they disagree.

## Physical artifacts

`kicad/gen_kicad_pcb.py` creates a new board from the JSON, its placement
tables and footprint mappings. It overwrites the selected output rather than
updating an existing board or preserving its routed copper. To inspect a
fresh preview, use a Python environment with `pcbnew` and the KiCad footprint
libraries installed:

```sh
mkdir -p build
python3 kicad/gen_kicad_pcb.py kicad/juku.board.json build/juku-preview.kicad_pcb
```

Inspect its printed overlap results and run placement, endpoint and DRC checks
before adopting the output. A printed overlap `FAIL` does not make the generator
exit nonzero. Generating this preview does not refresh the routed boards or
fabrication package.

The source and routed PCB may contain more footprints than the LVS-mapped HDL.
KiCad DRC can also report zero unconnected items when a footprint pad has never
been assigned a net. Consequently physical release needs all of the following:

- required functional pins modeled and assigned;
- source and routed PCB endpoint coverage;
- LVS for the mapped digital structure;
- DRC and independent Gerber review;
- programmable-part contents and provenance;
- explicit disposition of analog/timing assumptions.

The historical zero-open package describes an earlier routed-board hash.
Current source/routed differences and DRC findings are recorded in
[the routed audit](routed-refresh-audit.md) and
[factory-wire fidelity](factory-wire-route-fidelity.md). The current package
requires regeneration and independent review
(**DESIGN HOLD / PACKAGE REGENERATION REQUIRED**).
[Manufacturing readiness](replica-manufacturing-readiness.md) separates current
holds from historical package checks. Functional connectivity, physical
layout, construction and sourcing/programming remain release requirements;
[the project plan](../PLAN.md) lists the remaining blockers.

## Design rules

- Preserve source provenance in `board.json`; never turn an inference into a
  scan/measurement claim.
- Change connectivity in the machine-readable model first, then regenerate and
  reroute downstream artifacts.
- Keep simulation-only signals visibly named and excluded from LVS only when
  they have no claimed physical endpoint.
- Prefer small guards with explicit oracles over narrative claims.
- Do not retain superseded experimental reports in the live documentation;
  Git history is the archive.
