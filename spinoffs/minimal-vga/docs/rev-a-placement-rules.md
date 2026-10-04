# Rev A placement rules

Rev A is the monolithic workbench design. Its generated 200×200 mm placement
is defined by [gen_rev_a_pcb.py](../kicad/gen_rev_a_pcb.py), especially
`build_placement`, `IC_CAP`, `CAP_DIR` and the silkscreen block definitions.
The [Rev B status](rev-b-status.md) describes the current modular order target.

## Current generated layout

The generator packs functional bands on a 5.08 mm grid using footprint body
sizes. CPU/ROM and the larger GAL/PPI packages are horizontal; narrow logic
and DRAM packages are vertical. The main bands are CPU/ROM, decode,
refresh/timing, DRAM, and keyboard. Power is at the top left, clock/reset at
the top right, VGA at the right edge, and debug headers along the bottom.

Pull-up and keyboard resistor banks occupy a regular field at the left.
Diagnostic LEDs have paired local resistors at the right. U40 is a passive
video header, so C22 is placed with the spare capacitors rather than treated
as an active-device decoupler.

`IC_CAP` associates IC/socket positions with 100 nF capacitors, including the
unpopulated U23 socket. Most capacitors are placed above the rotated footprint
bounding box; U50's is to its left and U51's below. This is not always the package
short side. DRAM capacitors form a row above their owners. Offsets come from
bounding-box dimensions and grid rounding, without a power-pin distance limit.
C3, C4, C19 and C22 occupy spare-capacitor positions.

## Rules for changes

1. Keep connector access, board outline, mounting and assembly constraints
   ahead of visual alignment.
2. Keep timing, address-mux and memory-control paths short. Move repeated
   DRAM cells coherently unless a specific electrical constraint requires an
   exception.
3. Keep local bypass capacitors associated with their owners and review the
   actual power/ground return loop after routing. Visual proximity alone does
   not qualify decoupling or signal integrity.
4. Preserve regular package orientation, passive fields, LED pairs and readable
   assembly labels. Block labels must clear pads, soldering access and edges.
5. Change the generator and regenerate the PCB. Moving footprints invalidates
   existing routed copper until it has been rerouted or reviewed and passes
   the applicable DRC/connectivity checks.

Routing feedback can expose placement problems; fabrication readiness also
requires the [manufacturing checks](rev-a-manufacturing-readiness.md) and
[physical LVS coverage](rev-a-lvs-coverage.md).

## Placement check

From the repository root, with KiCad Python and footprint libraries available:

```sh
spinoffs/minimal-vga/kicad/check_rev_a_placement.sh
```

The wrapper generates a temporary PCB without zones, checks it and deletes it;
it does not overwrite the retained routed board. The checker compares component
and text bounding boxes, requiring overlap greater than 0.3 mm on both axes to
report a collision. It also checks component bodies against computed block
boundaries, with an exception for edge connector J3.

The check excludes intended connector pin labels, permits standalone labels
contained within a component body, and skips a component's own reference/value
pair. Standalone text is checked only on front silkscreen. This is a placement
screen; it does not check routed clearance, 3-D fit or capacitor return paths.
Routed DRC, mechanical fit and electrical return-path review remain separate.

## Layout references

- [KiCad PCB editor](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html): placement,
  ratsnest and routing tools.
- [TI decoupling notes](https://www.ti.com/content/dam/videos/external-videos/de-de/9/3816841626001/6313253251112.mp4/subassets/notes-decoupling_capacitors.pdf):
  minimize the bypass power-pin/ground return loop.
