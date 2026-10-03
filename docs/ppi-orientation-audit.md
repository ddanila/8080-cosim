# PPI physical orientation audit

Status: **HOLD** for both routed variants; source PCB orientation corrected.

## Current PCB mapping

Factory `.009 СБ` assembly views and owner photos show horizontal D26 and
D27 8255 packages with right-edge notches. The source PCB uses 270°
(equivalent to −90°) at the existing package centers. Both routed variants
still use 90°, which places the notch on the left in these DIP-40 footprints.
Their copper must be rebuilt against the corrected physical pin identities.

The [physical pin mapping](ppi-physical-pin-mapping.json) records the
orientation of all three PCB variants and the routed board's complete
40-pin permutation. **All 40 of 40 pin locations on each PPI carry a different
net** from the net intended for the photographed physical pin. Physical
pin 7/GND falls at routed pad 27/DB7; physical pin 26/+5 V falls at routed
pad 6/CS_D26 or CS_D27. Net-name parity alone cannot establish physical
pin correctness.

Regenerate the mapping with:

```sh
/usr/bin/python3 kicad/report_ppi_physical_pin_mapping.py
```

This report reads saved PCB orientation and pad nets and applies the
20-position permutation required by the photographed notch direction.
It does not trace original copper or run DRC. Rotating routed footprints
alone would invalidate their existing copper connections.

## Photo registration and placement

The [package-local registration](../ref/photos/juku-pcb-2/local-package-registration.json)
identifies all forty pad centers on both faces of each PPI. These fits
establish pad identity; they do not establish copper continuity or absolute
board coordinates. The vertical package near X2 is D11, the 8251 USART,
and its solder registration must not be used for D27.

D27's independent [top-edge](../ref/photos/juku-pcb-2/d27-top-edge-placement.json)
and [left-edge](../ref/photos/juku-pcb-2/d27-left-edge-placement.json)
checks give approximately −0.86 mm vertical and −0.64 mm horizontal
residuals against the routed placement. They support its coarse placement;
exact coordinates remain subject to local registration.

D26 has a separate placement hold. The direct bottom-edge check in
[photo registration](photo-registration.md) puts its photographed lower
row near y=243 mm, versus routed y=258.62 mm. A local fit must reconcile
the D26/D54/D55/D57 cluster and surrounding passives before applying a
placement correction. Broad panorama residuals are insufficient for that
change. The routed orientation and placement repair remains open.

## Original-board supply evidence

- D26.26 has a visible solder-side path to the third of four power landings,
  marked `+5V`. This supports the right-notch pin sequence but does not
  verify the cable contact or every branch of the rail.
- [D26.7 ground](../ref/photos/juku-pcb-2/d26-pin7-ground-chase.json)
  remains untraced. Neither face exposes a unique outward branch; measure
  continuity to an independently marked ground landing.
- [D27.7 ground](../ref/photos/juku-pcb-2/d27-pin7-ground-chase.json)
  likewise requires direct continuity. Nearby bright traces are insufficient
  evidence for a join beneath the body.
- [D27.26 via review](../ref/photos/juku-pcb-2/d27-pin26-via-review.json)
  closes the visible front trace to its via, but leaves the opposite-face
  landing and onward +5 V route unresolved. The shared D11/D27 homography
  does not identify that landing; the nearby west annulus is a rejected match.

## Closing the hold

Verify D26.7 ground and D27's power and selected signal routes against the
`.009` electrical drawing and original-board evidence. Correct the routed
footprint orientations, pad identities, and associated copper together.
Repeat electrical DRC, zero-open, source-pad parity, and visual package
checks. Set this status to **READY** only after independent review of the
corrected routed PCB.
