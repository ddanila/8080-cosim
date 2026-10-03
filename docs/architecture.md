# Architecture and verification boundaries

## Data flow

```text
factory drawings / photos / dumps / measurements
                       |
                       v
             kicad/juku.board.json
                 /             \
                v               v
      generated KiCad       structural HDL
      schematic + PCB       hdl/juku_top.v
                \               /
                 \---- LVS ----/
                         |
                         v
             behavioral regression
             vs cosim and MAME
```

Historical sources are authoritative; `board.json` is the machine-readable
working model. The generated KiCad schematic and the structural HDL are not two
freely editable sources that synchronize bidirectionally.

## LVS

`sync/check.sh` elaborates `hdl/juku_top.v` with Yosys and compares its mapped
instance/pin net partitions with a KiCad netlist. When a compatible KiCad CLI export is unavailable, the checker reads
`board.json` directly. Yosys treats device internals as black boxes for this
comparison; LVS checks their mapped connections, not chip behavior.

The comparison uses connectivity rather than net names: mapped endpoints are
equivalent when they are partitioned into the same nets. `sync/map.json`
contains the refdes/instance and pin/port mappings.

The current check is intentionally partial. Unmapped analog parts, placement-
only footprints, simulation-only ports, power-only ports, and omitted pins
are outside its proof. A
green result must never be interpreted as full-board electrical completeness.

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
