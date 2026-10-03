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

Photo-matched GND/+5 V front holes `(3030,1365)`/`(2978,1530)` project
from D9 to approximately `(119.21,111.61)`/`(116.82,119.37)` mm.
An independent D7-local x fit agrees within 0.07 mm. Their approximate
8.12 mm spacing cannot be represented by C35's current 5 mm footprint.
Owner same-hole identity and rail continuity remain unmeasured; see
[the C88 review](../ref/photos/juku-pcb-2/c88-d9-d7-gap-review.json).

C35 is modeled on RAIL_G/GND; RAIL_G is +5 V with E4 at the РУ5 setting.
C35 and C88 therefore have the same bypass rail roles in that configuration,
but this does not identify their physical holes. The `.009` assembly omits
C35; the older `.006` assembly names it above D67.

## DRAM-grid alignment hold

D9-local projection of current source C35 pads lands near
`(2984,1563)`/`(3093,1563)` in `200411500`, on unperforated board.
The C88 +5 V candidate is a separate visible drill at `(2978,1530)`
with a D9.16 front-copper stem. The apparent C35/C88 proximity in board
coordinates is insufficient evidence for a physical collision.

The independently registered D67 and D66 package fields show a shared
misalignment against the source DRAM grid. D67's photographed top contacts
near `(2843,1776)`/`(3010,1776)` differ from D9-scaled source predictions
by about `(−113,+143)` pixels. D66 gives approximately `(−109,+143)`
pixels. Package widths and spacing agree, supporting a group-alignment
problem rather than a C35-only error. At the local scale this implies
roughly 5.0–5.2 mm leftward and 6.7 mm downward displacement for the first
row; it does not establish an absolute correction for all four banks.

The broad `component_grid` transform disagrees with independently checked
D9/D7 positions by about 16 mm horizontally and 1.8 mm vertically.
Its small residual within the capacitor grid is not an accuracy estimate
across these regions. Establish a shared-hole D9-to-DRAM bridge before
moving the group or placing C88.

## C35 hole-identity hold

The first proposed capacitor-grid midpoint in
`docs/photo-registration/solder_grid-rectified.jpg` is within about 1.7 pixels
of the midpoint of independently identified D67.16 and D66.1 solder contacts.
Those package contacts are modeled GND and RAIL_H, not C35's RAIL_G/GND.
A regular two-hole feature does not independently prove a capacitor landing.
The corresponding package joints are roughly 247 pixels below C88's
separate +5 V candidate in `PXL_20260710_200525009.jpg`.

An independent D67-local projection of current C35 geometry places its
front pads near `(2872,1699)`/`(2981,1699)` in `200411500` and solder
positions near `(2678,1415)`/`(2570,1415)` in `200525009`. Neither solder
position has a drilled annulus. The overlapping component view also places
the projected pads on bare board. This rejects the current C35 geometry
at that local position; another C35 hole pair remains possible.

Keep the `.006` reference pattern, but identify capacitor holes separately
from package contacts at each site. Register cross-face identity and test
candidate rails before changing package or decoupler geometry. The two
package fits support a local alignment diagnosis, not a completed board-wide
registration or proof of 32 independent fabricated capacitor pairs.
