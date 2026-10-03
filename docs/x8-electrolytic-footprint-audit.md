# X8 C31–C33 footprint audit

Status: **HOLD**

## Current mismatch

The exact `.009 СБ` assembly view
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114615300.jpg` draws three
horizontal axial electrolytics above X8: C31/C32 positive on the right,
C33 positive on the left. Owner component views `PXL_20260710_200450127.jpg`
and `PXL_20260710_200439607.jpg` show the corresponding long metal cans
and widely separated joints. Their order and polarity marks identify the
bodies; owner rail continuity remains unmeasured.

All three PCB variants use `CP_Radial_D5.0mm_P2.00mm` at C31/C32/C33,
with 2.00 mm pad spacing. The generic `C_ELEC` mapping in
[kicad/gen_kicad_pcb.py](../kicad/gen_kicad_pcb.py) selects that footprint.
It cannot represent the photographed axial bodies and solder joints.
The axial family used for C17/C18 is available, but its nominal 25 mm
pitch must not be adopted without registering these six installed joints.

## Supported trial scale

In solder image `PXL_20260710_200537608.jpg`, the can pairs span roughly
625 pixels and the four labeled power landings have roughly 125-pixel
intervals. The source model's 5 mm landing interval gives a 25 mm trial
span. An independent D13 DIP-14 scale in the same image gives about
25.8 mm for that can span; see the
[package registration](../ref/photos/juku-pcb-2/local-package-registration.json).

These approximate reads support a 25–26 mm trial range. Perspective,
solder-blob center uncertainty, and separation from D13 prevent treating
that range as a certified drill pattern. Register the six can joints and
four power landings locally on both faces before selecting final pitch
and coordinates.

## E4 placement dependency

E4 is the three-pad +12 V/+5 V DRAM-rail selector. Its source-model
provenance identifies the sheet-2 power corner; its physical joints and
assembly placement are unregistered. A 25 mm axial placement trial
collided with the current E4 footprint. That collision does not identify
which placement is wrong.

Neither the solder view above nor the independent May close-up
`PXL_20260519_202052986.jpg` identifies a unique E4 three-joint row.
Register E4's three solder joints alongside the six can joints before
moving either footprint.

## Closing the hold

This mechanical fabrication hold is separate from the corrected C32/C33
logical rail names and routed electrical nets. Register the owner joints
to board coordinates, select and place axial footprints, refresh copper
in both routed variants, then run DRC and pad-net/rail review. Confirm
original-board rail continuity separately. Installed can markings are in
[the power-corner review](../ref/photos/juku-pcb-2/c93-power-corner-candidate-review.json).
