# D104 solder-side registration audit

## Current findings

The component photo `PXL_20260710_200402344.jpg` identifies the marked,
notch-down К170УП2 package. Direct owner continuity establishes D104.10
as NC. The exact `.009 Э3` sheet-1 detail draws only receiver sections
`4→13`, `5→12`, and `6→11`; it omits the fourth `7→10` section.

D104.7 has a visible front-copper join to the lower R30 lead. The model
assigns that lead to GND, but its owner-board ground continuity remains
unproved. D104.16's +12 V supply also remains a physical rail hold; see
[the device/source conflict](../ref/schematics/d104-pin16-rail-conflict.json).

## Solder-field identity

The two eight-joint columns near x≈2565/2710, y≈1140–1480 in
`PXL_20260710_200506061.jpg` repeat near x≈767/912, y≈1280–1620 in
`PXL_20260710_200509593.jpg`. They lie above the independently registered
D11 field. A D11-local two-face transform puts D104's component corners
within about 21 pixels of those observed solder corners, supporting field
identity without establishing rail continuity.

The notch-down orientation puts pin 16 near `(2710,1480)` in `200506061`.
It has no exposed local B.Cu departure, and its front route is cable-covered.
Pin 8 near `(2565,1140)` and pin 15 near `(2710,1430)` each have short,
separate links to open holes; neither reaches a known rail in this crop.

The rejected x≈2212/2350 corridor in `200506061` does not contain the
package's 2×8 joint field. It must not be used for pin identity or a
no-copper-departure inference. A small algebraic rectangle-fit residual
does not establish that anchors are physical package joints.

## Placement boundary

The [registration record](../ref/schematics/d104-pin16-rail-conflict.json)
retains the two independent panorama projections, solder-field fit and rejected
board-coordinate inference. They support coarse D104 placement near its
modeled center. D11 is photo-registered in the source board but retains its
older routed placement; see [placement parity](board-placement-parity.md).
A D11-local pixel transform does not establish absolute board millimeters
or justify moving D104 from the rejected estimate.

## R30 and ground continuity

The [pin-7/R30 photo review](../ref/photos/juku-pcb-2/d104-pin7-r30-photo-review.json)
records D104.7’s visible front-copper join to R30 lower. R30 upper remains
on a separate conductor whose endpoint is hidden beneath the X3 wire bundle;
the overlapping view does not resolve it. Coordinates and probe sites belong
to that record.

The exact source prints R30=33 kΩ between GND and D12.3/OC SOUT, but does
not identify the installed upright body's lower lead. The model assigns
that lower lead to GND. Neither owner view independently resolves the
body's resistance marking, so 33 kΩ is a source nominal rather than a
photo-read installed value.

With power removed, verify D104.7↔R30 lower, R30 lower↔known ground,
and R30 upper↔D12.3/OC SOUT. Check isolated resistance between R30's
leads and record both meter polarities before claiming owner rail closure.
Photo-proved local copper and source-expected rail assignment remain
separate evidence.
