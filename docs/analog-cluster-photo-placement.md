# Analog-cluster owner-photo placement

The assembly drawing and the populated owner board now jointly identify the
first three axial parts immediately below `D102`. This avoids assigning the
visually similar parts from colour or circuit expectations alone. `R65` can be
placed independently; `VD3` and `R66` expose a stale `L1` approximation and are
recorded without introducing shorts into the source PCB.

## Evidence and registration

- `ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` labels the positions
  below `D102`: `R65` at the left and `R67`/`VD3`/`R66` at the right.
- `ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows the corresponding
  populated region.  The upper visible row below `D102` is the left axial
  resistor `R65`, glass axial diode `VD3`, and right axial resistor `R66`.
- The owner image is mapped to board millimetres with the independently fitted
  16-pad `D102` affine registration.  Read body centres project to `(287.07,
  132.26)`, `(296.34, 133.56)`, and `(299.72, 134.75)` mm respectively.

The photo read is suitable for package placement but does not yet identify the
lower obscured/passive positions. `R65` is now placed at its observed centre.
Trial placement of `VD3` and `R66` created real-net shorts against the old
approximate `L1` pads (`SOUND_CLAMP` against both `RF_TANK` and `GND`), proving
that `L1` must be registered with that RF subcluster before those two observed
positions can safely be adopted. `R67` and the remainder likewise stay
unchanged until their bodies can be paired unambiguously. The generated `R65`
coordinate compensates for the KiCad axial-footprint anchor offset.

`kicad/check_analog_photo_placement.py` prevents regeneration from restoring
the former assembly-grid approximation for `R65`. The documented `VD3` and
`R66` centres are held as the next registration constraints, not silently lost.

After adopting `R65`, KiCad DRC reports zero `shorting_items` (11 clearance and
4 hole-to-hole findings remain elsewhere in the incomplete placement), and the
99-instance LVS remains fully matched at 239 nets.
