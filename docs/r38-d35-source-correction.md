# R38 and D35 sheet-2 source correction

The native `.009 Э3` sheet-2 frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101917240.jpg`, original crop
approximately `(1530,1750)`–`(2400,2650)`, prints **R38 1к** and **R39 12к**.
The power table in `PXL_20260718_101924004.jpg` defines rail **A as +5 V**.

The filled junction left of R38 connects D35.6 to the D42/D43 output-control
line at pins 8. That line is the existing `SHIFT_G` timing rail, also joined
to D41.9. R38's other terminal ends at rail A. POF enters both D35.3 and
D35.5 and R39's left terminal; R39's right terminal ends at A. D35.4 bends north and reaches the filled D42.10/D37.13 junction. D37.12
arrives on upper numbered rail 3, shared with D42.9/D43.9/XTAL16M; D37.11 descends separately
near x2400, crossing the D0-D7 rows without marked junctions before leaving that tile. The full-sheet overview and lower-right native tile carry it west into D34.12; the nearby 1.23 MHz/tag-13 line stays separate. D35.1/.2 remain unused in this detail. See
`ref/schematics/d35-d37-d42-source-recheck.json`.

## Model and physical placement

The board JSON, generated schematic, and source PCB adopt the source topology
above. Pad-net parity checks logical assignments; current routed findings and
missing endpoints belong to [factory-wire fidelity](factory-wire-route-fidelity.md)
and [placement parity](board-placement-parity.md). They do not establish
original-board continuity or release either routed PCB.

The full-resolution .009 assembly identifies the D50/C95-adjacent resistor as **R58** (`PXL_20260711_114556899.jpg`, rotated native crop). A separate lower-centre assembly panel `PXL_20260711_114617677.jpg` explicitly labels **R38** right/below D59. The source and routed boards place R38 beside D59 at pads `(121.4,252.91)`/`(121.4,245.29)` mm. The owner pale horizontal 1K0 beside D59 matches R38 position and value, and its left front lead joins physical D59.14/P5V and red R32 right; the far lead-to-SHIFT_G route still needs continuity (`ref/photos/juku-pcb-2/d59-orientation-audit.json`). The D51-right pale 5K1 body instead matches assembly R58 position and 5.1 kΩ source value. Its upper joint visibly joins D51.8/GND through solder copper, consistent with R58's grounded rail-E terminal; the lower joint heads west and needs a CAS continuity check. The current R58 PCB footprint at `(200.29,220.5)`/`(207.91,220.5)` mm is far from the D51-local owner estimate `(106.632,155.905)`/`(106.818,166.537)` mm, so R58 placement and copper remain on hold (`ref/photos/juku-pcb-2/c95-d50-r58-placement-review.json`). The owner-board
continuity of these source paths has not been measured, so neither routed
board is released.

## Simulation and measurement boundary

The source topology puts D35.4 on D42_Q with D42.10/D37.13;
D37.12 shares numbered rail 3 with D42.9/D43.9, while D37.11 reaches D34.12 on a separate pixel line. The runnable pixel oracle retains its
separate functional POF clamp and constant shift-enable stimulus; the
owner-board connectivity and behavior of this source-drawn output junction
remain unmeasured.
The controlled video probe and POF reports document simulation evidence within that boundary.
The two-package owner view fixes D37.11 and D35.4 as separate inspection
targets. Their output-tie photo review records the local visibility limits; see
`ref/photos/juku-pcb-2/d35-d37-output-tie-photo-review.json`.
The [D34.12 via review](../ref/photos/juku-pcb-2/d34-pin12-video-via-review.json)
records photo-supported copper toward D37.11; electrical continuity and
isolation still require measurement.

The same owner tile shows a separate red **12К** body directly left of
marked D35, matching R39's assembly position and sheet-2 value. Its
lower joint is visible, but the upper lead is covered by white wires;
neither physical lead has a proved POF/+5 V assignment. See
`ref/photos/juku-pcb-2/r39-d35-body-review.json`.
Projecting that lower joint into the overlapping solder-side tile from
D35.13 only provides a search area: no unique R39 hole or continuous
copper route can be identified there. Its lead polarity remains a
two-lead continuity measurement.
The ИР16 readiness and video-slot timing reports record D35.6/R38.1
as the source-drawn `SHIFT_G` driver and pull-up; they retain the
unmeasured physical-continuity and slot-schedule limits.

To identify physical R38, read or measure its 1 kOhm body, then with
power off check one lead against D35.6 and D42.8/D43.8, and the other
against an independently identified +5 V landing. Do not use D37.11 as an R38 lead target. Probe D35.4 against
D42.10/D37.13, then D37.12 against D42.9/D43.9/XTAL16M, and D37.11 against D34.12 while checking isolation from D103.11/D57.9/CLK_123M.
