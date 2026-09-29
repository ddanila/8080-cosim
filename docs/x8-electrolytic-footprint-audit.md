# X8 C31–C33 footprint audit

Status: **HOLD**

The exact `.009 СБ` assembly view
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114615300.jpg` draws three
horizontal axial electrolytics above X8: C31 and C32 with positive leads
on the right, C33 with its positive lead on the left. Owner component views
`PXL_20260710_200450127.jpg` and `PXL_20260710_200439607.jpg` show the
corresponding three long metal cans with their leads bent outward to widely
separated board joints. Their order and polarity marks photo-register the
fitted C31/C32/C33 bodies; rail continuity remains unmeasured.

`pcbnew` inspection of the current source, routed, and routed-candidate PCBs
finds the same `CP_Radial_D5.0mm_P2.00mm` footprint at each of C31, C32,
and C33. Every pad pair has a 2.00 mm center distance. That geometry cannot
represent the photographed axial body or its separated solder joints. The
generator selects this radial footprint from the generic `C_ELEC` mapping.
The repository already has an axial electrolytic footprint family used for
C17/C18, but the X8 can body sizes and exact hole pitch have not yet been
registered from both owner faces. Do not substitute its nominal 25 mm pitch
without confirming the three installed hole pairs.

The original-pixel solder view `PXL_20260710_200537608.jpg` shows three
roughly aligned large-joint pairs in the X8 corner, around image x
`2750/3375` and y `1870`, `2050`, and `2240`. The four labeled power
landings directly below them are spaced about 125 pixels apart in that same
local view; each can pair spans about 625 pixels, or approximately five
landing intervals. The present A59–A62 source-board model uses 5.0 mm
landing intervals, making **25 mm a plausible can-pad pitch**. This is a
local ratio, not a certified drill pattern. There is an independent scale
check in the **same solder image**: the registered D13 DIP-14 pin-8 to pin-14
row spans 369 pixels for six 2.54 mm intervals, or 24.21 pixels/mm
(`ref/photos/juku-pcb-2/local-package-registration.json`). At that scale
the ~625-pixel can span is ~25.8 mm and the ~125-pixel power-landing spacing
is ~5.16 mm, consistent with the source model's nominal 5 mm. D13 is
roughly 800–1200 pixels above the cans, so perspective and approximate
joint-center reads prevent treating 25.8 mm as a drill dimension. A
25–26 mm axial footprint is the supported trial range. The six can joints
and four power landings still need a local two-face registration for final
coordinates and pad pitch.

A closer read of that solder tile puts the four X8 cable-hole centers at
approximately x `2888`, `3013`, `3138`, and `3263` pixels, all near y
`2433` pixels. Their three intervals are each about `125` pixels. The
three left can joints are near x `2750` and the three right joints near x
`3375`, so the local horizontal span is about `625/125 = 5.0` cable
intervals. In the source PCB the cable pads A59–A62 are at x `34`, `29`,
`24`, and `19` mm, respectively, giving a **25.0 mm horizontal trial
span** for the can joints. This improves the internal consistency of the
25 mm trial, but the centers are visually estimated from solder blobs and
the cable-pad row alone fixes only one image axis. It cannot certify the
two-dimensional drill centers, assign E4's nearby joints, or justify
replacing the footprints yet.

A temporary copy of the current source PCB replaced C31/C32/C33 with the
available 25 mm axial footprint and kept their logical pin nets. Trial pads
were placed at x `15/40` mm and y `230.0/237.4/245.0` mm, respectively;
positive pin 1 was put right for C31/C32 and left for C33. This used the
X8-landing frame only as a placement approximation. Error-only KiCad DRC
found 177 violations and 499 unconnected items, versus the source baseline
173/499. The four added findings are one C31–E4 courtyard overlap and three
pad-inside-courtyard records involving those two footprints. There were no
new shorts or clearance violations. The trial was not adopted: E4's
photo-relative position and all six can hole centers need a local fit before
the source footprint can be moved, and the routed variants need a coordinated
copper replacement.

E4 is the three-pad +12 V/+5 V DRAM-rail selector, not a capacitor part.
Its current source-board pads are all at x `39.9` mm, y `223.96`, `226.50`,
and `229.04` mm. The generator previously called its placement assembly-derived;
that claim has been removed because the current E4 model provenance names
only the sheet-2 power corner and the
archived X8 assembly close-up does not show an E4 label or three-hole fit.
An OCR pass over the archived `.009 СБ` photo tiles returned no E4/Е4
callout; this is only a search result, not proof that the label is absent.
In the original-pixel solder image `PXL_20260710_200537608.jpg`, the
approximate projection of the modeled E4 row falls near image x `2750`,
y `1740/1800/1860`, using the local X8 landing and D13 pitch estimates
above. Inspection of that area does not reveal an unambiguous three-joint
row; the lowest predicted position nearly meets the upper can's large
joint around y `1870`. Projection error and perspective prevent assigning
either feature to E4 from this view alone.
The C31/E4 trial collision therefore does not identify which footprint is
misplaced. Register E4's three physical solder joints alongside the six can
joints before shifting either footprint.

The independent May component close-up
`ref/photos/juku-pcb-2/PXL_20260519_202052986.jpg`, native crop
`(2200,1230)–(3450,2050)`, exposes several isolated holes and short joined
features around the small axial parts beside the cans. None is a uniquely
identified collinear E4 three-hole row or fitted jumper. This oblique view
cannot supply pad identity or pitch; it adds no basis for moving E4 or any
electrolytic footprint.

This is a mechanical fabrication hold independent of the already-corrected
C32/C33 logical rail names and routed electrical nets. A safe repair needs
the six owner joint centers registered to board coordinates, then axial
footprint selection/placement, copper refresh in both routed variants, and
DRC plus pad-net/rail review. Installed can markings are in
`ref/photos/juku-pcb-2/c93-power-corner-candidate-review.json`.
