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
lower obscured/passive positions. `R65`, the visibly marked red `2к` R67, glass
`VD3`, and rightmost `R66` are now placed at their observed centres. The
factory drawing fixes the left-to-right identity of the right-hand group, so
the photo centres no longer depend on colour or circuit-role inference.
The yellow part beside `R65` was tested as an L1 candidate and rejected. Its
full-resolution marking reads `680п` (680 pF), and the registered solder view
does not yield the three coherent coil terminals required by the schematic.
The previously recorded `(287.07,132.26)` centre therefore belongs to a
capacitive part, not L1. The `.009` factory drawing identifies that populated
part as C94, and its visible marking reads `680п`; C94 is now restored to the
physical board model with two explicit continuity-boundary leads rather than
being silently omitted or misidentified as the tapped coil. The remaining
parts stay unchanged until their bodies can be paired unambiguously. The
generated vertical axial/diode coordinates
compensate for the KiCad footprint-anchor offset; the guarded body centres are
`VD3=(299.38,128.40)` and `R66=(302.69,128.46)` mm.

## RF-option revision disposition

The original `.006` sheet-2 circuit (`ref/schematics/p2_sheet2.png`) draws a
dashed RF option around VT3/VT4, adjustable three-terminal L1, R73, and their
dedicated C13/C14/R68-R77 passives. That source remains valid evidence for the
older revision, but not for target population. The archived group BOM assigns
the extra RF transistors and 4.7 kΩ adjustable trimmer to `.006`; the complete
`.009` assembly placement and complete owner-board component tile set instead
show only VT1/VT2 and no RF-option cluster.

Those fifteen legacy-only references are therefore DNP on the `.009` target.
The `.009` drawing reuses C9/C10/C11/C12/C15 around D93-D102, so those physical
capacitors remain at their factory positions with both leads left as explicit
target-continuity boundaries. R67.2 and physical connector contact X6.1 are
likewise boundaries rather than being forced onto the superseded RF nets. The
yellow `680п` part remains the separately proved C94.

`kicad/check_analog_photo_placement.py` prevents regeneration from restoring
the former assembly-grid approximations for `R65`/`R67`/`VD3`/`R66`/`C94`, and
guards C16/C19, R92/R99, plus the two registered capacitor drill spans beside D102.

## C16/R92/R99 drill registration

The `.009` factory drawing identifies C16 as the horizontal capacitor between
the upper and lower FDC IC rows, R92 as the upper/right horizontal resistor
below D95, and R99 as the lower/left horizontal resistor below-left of D95.
Raw component image `PXL_20260710_200418174.jpg` independently shows all three
parts populated: a grey axial C16 and two red axial resistors. Their visible
lead landings agree with the affine-projected factory centres and the solder
image `PXL_20260710_200522685.jpg` corroborates the paired backside locations.

C16 is therefore restored at `(267.094,101.055)` mm on a 12.50 mm horizontal
span, with pads at `(260.844,101.055)` and `(273.344,101.055)` mm. R92 is at
`(253.869,101.194)` mm and R99 at `(241.207,103.467)` mm, each on a 10.16 mm
horizontal span. The body markings are not readable confidently and the broad
nearby solder rails do not establish unique remote destinations, so the model
keeps all three values blank and all six leads as singleton boundary nets.

## C19 drill registration

The `.009` factory assembly drawing uniquely labels the vertical capacitor
immediately right of D99 as C19 and projects its body centre to
`(292.893,93.574)` mm. Raw owner component image
`PXL_20260710_200418174.jpg` independently shows the populated grey axial body,
both bent leads, and two separate board landings at that site. The registered
solder image `PXL_20260710_200522685.jpg` exposes the corresponding distinct
joints. A vertical 10.00 mm axial footprint therefore preserves the physical
part at pads `(292.893,88.574)` and `(292.893,98.574)` mm.

The body deliberately leans over the adjacent resistor column, so body overlap
does not imply an electrical join. Its marking is not read confidently and the
visible copper does not reach unique remote package pads; both leads remain
singleton boundary nets.

## C20/C22 drill registration

The factory `.009` drawing identifies the overlapping vertical bodies at the
right end of D102 as C20 and C22. Its previously recorded body-label points
project inside the D102 package outline and therefore are not usable as drill
centres. The full-resolution owner component view instead shows two grey axial
capacitors leaning to the right of the package, while the independently
registered solder view exposes both pairs of joints. Relative to D102's exact
2.54 mm pad grid, the only coherent paired-hole solution is:

- C20 centre `(303.997,110.024)` mm, pads at y `105.024/115.024` mm;
- C22 centre `(306.537,110.024)` mm, pads at y `105.024/115.024` mm.

Both spans are 10.00 mm and the columns are 2.54 mm apart. This geometry lands
on the visible component-side lead arcs and the corresponding four backside
joints within the D102 registrations' roughly 0.1--0.5 mm photographic read
uncertainty. Rotation and contrast enhancement makes C20's marking legible as
`1Н5`. GOST 11076-69 Table 1 maps that code exactly to 1500 pF / 1.5 nF, so
the source model now adopts C20=`1,5 нФ`; the narrow standard provenance is
recorded in `ref/datasheets/gost-11076-69-capacitance-code.md`. C20's tolerance,
voltage, and remote destinations remain unread. C22's marking and both remote
copper destinations also remain unread, so the four singleton boundary nets
retain those connectivity unknowns without omitting the populated hardware.

The R65/R67 increment removed their false D102-pad collisions. A later
full-source DRC audit correctly exposed ten unique pairs caused by the remaining
`.006` RF-option placeholders. The cross-revision population disposition above
removes those contradicted footprints rather than moving any registered `.009`
part. `docs/source-pcb-drc.md` now guards zero electrical pad/item collisions;
LVS remains a separate connectivity check and does not validate placement.
