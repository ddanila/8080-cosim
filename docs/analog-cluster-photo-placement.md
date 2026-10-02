# Analog-cluster owner-photo placement

The assembly drawing and the populated owner board jointly identify the
passive groups below `D102`. This avoids assigning visually similar axial parts
from colour or circuit expectations alone. `R65` can be placed independently;
the RF group remains constrained but deferred while its tapped coil is traced.

## Evidence and registration

- `ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` labels the positions
  below `D102`: `R65` at the left and `R67`/`VD3`/`R66` at the right.
- `ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows the corresponding
  populated region. The red axial resistor left of the yellow three-lead
  КТ315 `VT2` is `R65`; the right group contains `R67`, glass `VD3`, and `R66`.
- The owner image is mapped to board millimetres with the independently fitted
  16-pad `D102` affine registration. A full-resolution reread projects the
  `R65` body centre to `(282.21, 125.14)` mm. The right-group observations are
  approximately `R67=(295.94,125.39)`, `VD3=(299.38,128.40)`, and
  `R66=(302.69,128.46)` mm.

The photo read is suitable for package placement but does not yet identify the
lower obscured/passive positions. `R65`, the visibly marked red `4К7` R67, glass
`VD3`, and rightmost `R66` are now placed at their observed centres. The
factory drawing fixes the left-to-right identity of the right-hand group, so
the photo centres no longer depend on colour or circuit-role inference.
Rotated native crops of the independent May 19 and July 10 owner views read
`К43` on the fitted R65 body (0.43 kΩ, or 430 Ω) and `1K0` on R66. Both match
the exact `.009` sheet-2 video detail in
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg`. The same detail
prints R67 as 2 kΩ, while both owner views read `4К7` on the fitted R67;
the source-versus-population difference remains recorded in
`ref/schematics/native-resistor-value-registration.json`. These photo reads
establish body markings, not isolated electrical measurements.
The former C94 identification of the yellow body is retracted. Full-resolution
review resolves three leads and the marking `Б / 8901`, the grade/date marking
of the factory-drawn КТ315 `VT2`. The raw July tile registers its E-C-B lap
joints at board coordinates `(280.068,130.501)`, `(281.381,133.201)`, and
`(279.700,135.892)` mm. Pin 1/emitter and R65.1 enter the directly visible common
`VIDEO_OUT` solder pool; pins 2 and 3 retain the native `P5V` collector and
`VT2_BASE` assignments. Cross-side projection places all three joints on bare
backside copper without annuli or drills, corroborating the raised, bent-lead
component-side construction shown by the factory mounting detail.

The assembly drawing separately labels a two-terminal C94 immediately right of
VT2. Its locally projected centre, corrected by the stronger owner-photo VT2
fit, is `(289.870,130.321)` mm. Exact `.009` sheet-1 supply detail
`PXL_20260718_101827714.jpg` groups C94 with the +5 V-to-ground bypasses.
May and July owner views expose bare board at C94's locally projected centre
between VT2 and the right-hand passive group. Its actual pad pair, population,
value, and individual physical pin-to-rail assignments remain explicit
boundaries; neither the former `680` value nor the former C94.2/VIDEO_OUT join is
retained. The remaining parts stay unchanged until their bodies can be paired
unambiguously.

The routed replica's two C94 through-hole pad centres `(289.87,132.821)` and
`(289.87,127.821)` mm project through the registered local affine to about
`(3252,2011)` and `(3250,1901)` in the July owner tile. Original-resolution
inspection shows bare substrate at both positions. That footprint is a
provisional placement, not a photo-registered copy of original drilling.

The factory 12 cm cable table and two component-photo angles prove that X6 is bracket-mounted.
An original-resolution reread places printed point A:3 beside VT2/R65, physically
separate from VD3; its former `SOUND_CLAMP` promotion is retracted. A:3/X6.1 is
an electrical boundary, while the separately insulated A:4/X6.2 return reaches
the wide ground strip. The generated PCB therefore carries
surface lap-joint footprints `AX603`/`AX604`, not an invented X6 body. The
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
target-continuity boundaries. R67.2 and X6 A:3 remain such boundaries; the
factory table still closes A:3/A:4 to X6 independently of the superseded RF nets. The
yellow `Б / 8901` part is the retained VT2; C94 remains separately bounded.

R67.2's July upper-lead coordinate is corrected from `(3321,1698)` to about
`(3365,1730)` in `200418174`. Both July and May views read `4K7` on the
factory-identified body, superseding the printed 2 kΩ value. The D102-local
cross-side fit now projects that lead near `(874,956)` in solder image
`PXL_20260710_200522685.jpg`, about 5 px from an actual solder joint
`(869,953)`. Native copper runs east without a break to open annulus
`(1295,958)`; overlapping `200506061` repeats the joint-to-annulus pattern.
The prior bare-copper/no-via claim used the wrong front point. The local route
is photo-supported. Independent D102 and D97 inverse fits search for the far
annulus near front `(2937,1739)` and `(2905,1736)` respectively, but neither
has a unique visible drill. Three adjacent July holes repeat in the May
component view under a consistent (+26,-935) px local shift; both predicted
points remain bare there too. The source-drawn VT2-base destination still
requires continuity. Evidence is in
`ref/photos/juku-pcb-2/r67-photo-exhaustion.json`.

`kicad/check_analog_photo_placement.py` prevents regeneration from restoring
the former assembly-grid approximations for `VT2`/`R65`/`R67`/`VD3`/`R66`/`C94`, and
guards VT2's three lap joints, both C94 boundaries, C16/C19, R92/R99, plus the two
registered capacitor drill spans beside D102. Machine-readable VT2/C94 correction
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
photo alone does not establish the remote destinations, but recovered `.009`
Э3 sheet 3 now closes C16.1 to D97.15 and C16.2 to D97.14. The model keeps
only C16's value/unit, tolerance, and voltage open. R92/R99 are separately
photo-closed as 1.3 kΩ and 4.7 kΩ with all endpoints traced.

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
`D97_RC2_C19_R100` at D97.7 and `D97_C2_C19_R86_TARGET` at D97.6. The second
join follows direct target copper and overrides the electrical sheet's
conflicting R86=470 reset annotation. The same oblique May view directly resolves
bare `22` on C19's exposed face, but no unambiguous unit/decimal glyph, so the
marking is registered literally without assigning a capacitance.

The four adjacent horizontal resistors' right-hand pin-2 leads all terminate
on one uninterrupted component-side perimeter rail. R100.2, R102.2, R108.2,
and R86.2 are closed to `P5V` by the target common rail plus electrical sheet
3. The sheet also closes R102.1 to C22.2/D102.15 and R108.1 to
C20.2/D102.7. The solder-side D102.8 ground trace is not mistaken for this
component-side +5 V rail.

The July component view now also registers the four left joints at R100.1
`(3294,1064)`, R102.1 `(3317,1142)`, R108.1 `(3325,1217)`, and R86.1
`(3320,1276)` pixels. The independent May angle separates the same joints.
Neither photo alone exposes a complete remote continuation for R102.1 or
R108.1; their promotion comes specifically from recovered electrical sheet 3.

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
uncertainty. Native July and May crops retract the earlier `1Н5` reading:
C20's early July opposite face reads `±5`, while C22's May face carries
glyphs resembling `М75`, not a complete capacitance code. Two later July angles expose
bare `22` on both bodies, matching exact sheet 3's 22 pF nominal numerals.
The closer angle also reads `±10` on outer C22. Thus the photographed
tolerances are 5% for C20 and 10% for C22; both installed units remain
unverified. The standard's code mapping is retained only as a generic reference
in `ref/datasheets/gost-11076-69-capacitance-code.md`. Sheet 3 still closes
C20 on D102.6/.7 with R108 and C22 on D102.14/.15 with R102.

The R65/R67 increment removed their false D102-pad collisions. A later
full-source DRC audit correctly exposed ten unique pairs caused by the remaining
`.006` RF-option placeholders. The cross-revision population disposition above
removes those contradicted footprints rather than moving any registered `.009`
part. `docs/source-pcb-drc.md` now guards zero electrical pad/item collisions;
LVS remains a separate connectivity check and does not validate placement.
