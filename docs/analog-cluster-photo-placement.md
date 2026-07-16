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
physical board model rather than being silently omitted or misidentified as the
tapped coil. A later endpoint review of the raw July tile, its overlapping lower
tile, and an independent May angle separates the two physical leads. In all
three views the upper C94 lead and lower R65 lead enter one common component-side
solder pool. The modeled physical orientation maps those leads to C94.2 and
R65.1, so C94.2 is now closed to `VIDEO_OUT`. The separate lower C94.1 lap joint
is visible but none of the three angles exposes a continuous remote route; its
registered solder-side region is likewise non-unique. C94.1 therefore remains a
photo-exhausted continuity boundary. The remaining
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

R67.2 has now been chased to the limit of the owner imagery. The registered
July component view and an independent May angle both expose its upper physical
lead ending in a distinct solder pool without visible onward copper. A local
cross-side affine built from all fourteen paired D102 pin centres projects that
joint to `(916,988)` in solder image `PXL_20260710_200522685.jpg` with less than
0.001 px anchor residual. That location is a bare copper corner with no annulus,
drill, or solder joint; the overlapping `200506061` tile independently shows the
same absence. The coincident backside trace is therefore not promoted as an
inter-layer join. R67.2 remains a photo-exhausted continuity measurement, with
the evidence preserved in `ref/photos/juku-pcb-2/r67-photo-exhaustion.json`.

`kicad/check_analog_photo_placement.py` prevents regeneration from restoring
the former assembly-grid approximations for `R65`/`R67`/`VD3`/`R66`/`C94`, and
guards C94's pad orientation/net assignment, C16/C19, R92/R99, plus the two
registered capacitor drill spans beside D102. Machine-readable C94 endpoint
evidence is in `ref/photos/juku-pcb-2/c94-endpoint-registration.json`.

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
horizontal span. An oblique May component view directly resolves bare `27` on
C16's exposed face. GOST 11076-69 Table 1 nevertheless requires a unit/decimal
letter for a complete coded capacitance, and no such glyph is unambiguously
readable; `27` is
therefore registered literally without promoting a value. The broad nearby
solder rails do not establish unique remote destinations, so the model keeps
C16's value blank and both leads as singleton boundary nets. R92/R99 are
separately photo-closed as 1.3 kΩ and 4.7 kΩ with all endpoints traced.

## C19 drill registration

The `.009` factory assembly drawing uniquely labels the vertical capacitor
immediately right of D99 as C19 and projects its body centre to
`(292.893,93.574)` mm. Raw owner component image
`PXL_20260710_200418174.jpg` independently shows the populated grey axial body,
both bent leads, and two separate board landings at that site. The registered
solder image `PXL_20260710_200522685.jpg` exposes the corresponding distinct
joint pair. Cross-side review corrects their recorded order: upper component
pad 1 is solder coordinate `(875,712)`, while lower pad 2 is `(823,893)`; the
former record contained the same coordinates in reverse order. A vertical
10.00 mm axial footprint therefore preserves the physical
part at pads `(292.893,88.574)` and `(292.893,98.574)` mm.

The body deliberately leans over the adjacent resistor column, so body overlap
alone does not imply an electrical join. Here, however, two independent
component angles expose the leads themselves: C19's upper pad 1 and R100.1
terminate on one physical landing, while C19's lower pad 2 and R86.1 terminate
on another. Those pairs are therefore modeled as
`C19_1_R100_1_BOUNDARY` and `C19_2_R86_1_BOUNDARY`; each joined net's remote
destination remains unresolved. The same oblique May view directly resolves
bare `22` on C19's exposed face, but no unambiguous unit/decimal glyph, so the
marking is registered literally without assigning a capacitance.

The four adjacent horizontal resistors' right-hand pin-2 leads all terminate
on one uninterrupted component-side perimeter rail. R100.2, R102.2, R108.2,
and R86.2 are therefore closed to one shared
`RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY` net. The rail's remote destination plus
R102.1 and R108.1 remain explicit continuity boundaries; the solder-side
D102.8 ground trace is not promoted as a cross-layer join without visible or
measured inter-layer continuity.

The July component view now also registers the four left joints at R100.1
`(3294,1064)`, R102.1 `(3317,1142)`, R108.1 `(3325,1217)`, and R86.1
`(3320,1276)` pixels. The independent May angle separates the same joints.
Neither angle nor the registered solder field exposes a complete, uniquely
attributable remote continuation for R102.1 or R108.1, so those two paths are
photo-exhausted continuity measurements rather than guessed copper.

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
the source model now adopts C20=`1,5 нФ`. An independent May component
angle directly exposes `1Н5` on the outer C22 body too, fixed by D102 and the
inner C20 body against the already registered column order; C22 therefore also
adopts `1,5 нФ`. The narrow standard provenance is recorded in
`ref/datasheets/gost-11076-69-capacitance-code.md`. Both parts' tolerances,
voltages, and remote destinations remain unread, so the four singleton boundary
nets retain those connectivity unknowns without omitting the populated hardware.

The R65/R67 increment removed their false D102-pad collisions. A later
full-source DRC audit correctly exposed ten unique pairs caused by the remaining
`.006` RF-option placeholders. The cross-revision population disposition above
removes those contradicted footprints rather than moving any registered `.009`
part. `docs/source-pcb-drc.md` now guards zero electrical pad/item collisions;
LVS remains a separate connectivity check and does not validate placement.
