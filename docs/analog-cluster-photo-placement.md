# Analog-cluster owner-photo placement

The assembly drawing and the populated owner board jointly identify the
passive groups below `D102`. This avoids assigning visually similar axial parts
from colour or circuit expectations alone. `R65` can be placed independently;
the RF group remains constrained but deferred while its tapped coil is traced.

## Evidence and registration

- `ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` labels the positions
  below `D102`: `R65` at the left and `R67`/`VD3`/`R66` at the right.
- `ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows the corresponding
  populated region. The red axial resistor left of the yellow three-lead RF
  part is `R65`; the right group contains `R67`, glass `VD3`, and `R66`.
- The owner image is mapped to board millimetres with the independently fitted
  16-pad `D102` affine registration. A full-resolution reread projects the
  `R65` body centre to `(282.21, 125.14)` mm. The right-group observations are
  approximately `R67=(295.94,125.39)`, `VD3=(299.38,128.40)`, and
  `R66=(302.69,128.46)` mm. The earlier `(287.07,132.26)` reading was the yellow
  three-lead part, not `R65`, and is explicitly superseded here.

The photo read is suitable for package placement but does not yet identify the
lower obscured/passive positions. `R65` and the visibly marked red `2к` R67 are
now placed at their observed centres.
The yellow part beside `R65` was tested as an L1 candidate and rejected. Its
full-resolution marking reads `680п` (680 pF), and the registered solder view
does not yield the three coherent coil terminals required by the schematic.
The previously recorded `(287.07,132.26)` centre therefore belongs to a
capacitive part, not L1. `VD3`, `R66`, and the remainder stay unchanged
until their bodies can be paired unambiguously. The generated `R65` coordinate
compensates for the KiCad axial-footprint anchor offset.

## L1 model discrepancy

The original sheet-2 RF circuit (`ref/schematics/p2_sheet2.png`) draws `L1` as
an adjustable three-terminal coil with a `1/5` tap feeding `R76` and the `HF`
output. The source model now preserves those three electrical terminals as
`RF_TANK`, `VT4_C`, and `RF_TAP`; this also restores previously omitted C12.2
to the collector/coil-return node. The PCB uses an explicit three-pad stand-in
until the real coil and its solder landings are registered. The adjacent yellow
`680п` part is explicitly excluded from that search.

`kicad/check_analog_photo_placement.py` prevents regeneration from restoring
the former assembly-grid approximations for `R65`/`R67`. The documented `VD3` and
`R66` centres are held as the next registration constraints, not silently lost.

After adopting `R65` and `R67`, KiCad DRC reports zero `shorting_items` (10 clearance and
4 hole-to-hole findings remain elsewhere in the incomplete placement), and the
100-instance LVS remains fully matched at 243 nets.
