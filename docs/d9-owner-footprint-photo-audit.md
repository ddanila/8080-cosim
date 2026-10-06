# D9 owner footprint photo audit

## Current source and routed placement

The native component crop `(2520,1160)–(3100,1610)` in
`PXL_20260710_200411500.jpg` resolves D9's complete marked 2×8 field:
x≈2590..2977, upper/lower y≈1318/1480. The overlapping
`PXL_20260710_200415237.jpg` independently supports its spacing from D7.
See the [package registration](../ref/photos/juku-pcb-2/local-package-registration.json).

D8-local and D7-local scales predict D9.1 near x=116.77/116.70 mm.
The source PCB uses D9.1 `(116.77,109.4)` mm and −90° orientation;
its body center is `(107.88,113.205)` mm. The generator matches that
placement. Both routed variants retain D9.1 `(118.813,109.498)` mm
and need a coordinated footprint/copper correction. Logical pin nets
are unchanged.

Check source/generator placement with:

```sh
/usr/bin/python3 kicad/check_source_chip_placement_parity.py
```

This checks modeled chip placement, not original-board continuity or DRC.
A routed repair requires full DRC and connectivity checks.

## C88 candidates

The upper front hole `(3030,1365)` matches a solder strip photo-traced to
D6.8/source GND; the lower hole `(2978,1530)` has a visible front stem from
D9.16/source +5 V. These rail-consistent candidate holes project
from D9 to approximately `(119.21,111.61)`/`(116.82,119.37)` mm.
An independent D7-local x fit agrees within 0.07 mm. Their approximate
8.12 mm spacing cannot be represented by C35's current 5 mm footprint.
Owner same-hole identity and rail continuity remain unmeasured; see
[the C88 review](../ref/photos/juku-pcb-2/c88-d9-d7-gap-review.json).

C35 is modeled on RAIL_G/GND; RAIL_G is +5 V with E4 at the РУ5 setting.
C35 and C88 therefore have the same bypass rail roles in that configuration,
but this does not identify their physical holes. The `.009` assembly omits
C35; the older `.006` assembly names it above D67.

## DRAM-grid and C35 hole holds

Projection through D9 places the current source C35 pads on unperforated
board, separate from the visible C88 +5 V candidate. Proximity in modeled
board coordinates does not establish a physical collision or shared holes.

Independent D67 and D66 package fits agree on a first-row displacement
of roughly 5.0–5.2 mm leftward and 6.7 mm downward relative to the source
DRAM grid. Package widths and spacing agree, supporting a group alignment
problem. These local fits do not establish an absolute correction for all
four banks.

The broad `component_grid` transform disagrees with independently checked
D9/D7 positions by about 16 mm horizontally and 1.8 mm vertically.
Its residual within the capacitor grid does not establish accuracy across
these regions. Register shared holes between D9 and the DRAM field before
moving the group or placing C88.

The proposed C35 grid pair can instead be package contacts: D67.16 and
D66.1 have source roles GND and RAIL_H, distinct from C35's RAIL_G/GND pair.
A D67-local search for current C35 pads near `(2872,1699)`/`(2981,1699)`
in `200411500` found no corresponding drilled pair in the solder or
overlapping component views. C35's current placement remains unsupported;
a distinct physical pair must be identified.

Keep the `.006` reference pattern, identify capacitor holes separately
from package contacts, and confirm their cross-face identities and rails
before changing package or decoupler geometry. The package fits do not prove
32 independent fabricated capacitor pairs.
