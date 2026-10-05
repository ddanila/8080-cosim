# Analog-cluster owner-photo placement

The assembly drawing and the populated owner board jointly identify the
passive groups below `D102`. This avoids assigning visually similar axial parts
from colour or circuit expectations alone. The retained `.009` groups have
photo-registered placements; the older `.006` RF group is excluded.

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
`VD3`, and rightmost `R66` are placed at their observed centres. The
factory drawing fixes the left-to-right identity of the right-hand group, so
the photo centres do not depend on colour or circuit-role inference.
Rotated native crops of the independent May 19 and July 10 owner views read
`К43` on the fitted R65 body (0.43 kΩ, or 430 Ω) and `1K0` on R66. Both match
the exact `.009` sheet-2 video detail in
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg`. The same detail
prints R67 as 2 kΩ, while both owner views read `4К7` on the fitted R67;
the source-versus-population difference remains recorded in
`ref/schematics/native-resistor-value-registration.json`. These photo reads
establish body markings, not isolated electrical measurements.
Full-resolution review resolves three leads and the marking `Б / 8901`, the grade/date marking
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
boundaries. C94 is modeled without an installed value or a VIDEO_OUT join.

The replica C94 through-hole pad projections land on bare owner-board
substrate. Its footprint remains provisional; the coordinates and image
controls are retained in [the VT2/C94 evidence](../ref/photos/juku-pcb-2/c94-endpoint-registration.json).

The factory 12 cm cable table and two component-photo angles prove that X6 is bracket-mounted.
An original-resolution reread places printed point A:3 beside VT2/R65, physically
separate from VD3. A:3/X6.1 is
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

The corrected R67 cross-side registration identifies its
upper lead's solder joint and an uninterrupted backside trace to an open
annulus. The annulus's front-side counterpart and the source-drawn VT2-base
destination remain unproved; direct continuity is required. Coordinates,
photo hashes and search limits are retained in
[the R67 registration evidence](../ref/photos/juku-pcb-2/r67-photo-exhaustion.json).

## C16/R92/R99 drill registration

The `.009` factory drawing identifies C16 as the horizontal capacitor between
the upper and lower FDC IC rows, R92 as the upper/right horizontal resistor
below D95, and R99 as the lower/left horizontal resistor below-left of D95.
Raw component image `PXL_20260710_200418174.jpg` independently shows all three
parts populated: a grey axial C16 and two red axial resistors. Their visible
lead landings agree with the affine-projected factory centres and the solder
image `PXL_20260710_200522685.jpg` corroborates the paired backside locations.

An oblique May component view directly resolves bare `27` on
C16's exposed face; the independent July angle repeats `27`, but D97 hides
the lower body line. GOST 11076-69 Table 1 nevertheless requires a unit/decimal
letter for a complete coded capacitance, and no such glyph is unambiguously
readable; `27` is
therefore registered literally without promoting a value. The broad nearby
photo alone does not establish the remote destinations, but recovered `.009`
Э3 sheet 3 closes C16.1 to D97.15 and C16.2 to D97.14. The model keeps
only C16's value/unit, tolerance, and voltage open. R92/R99 are separately
photo-closed as 1.3 kΩ and 4.7 kΩ with all endpoints traced.

## C19 drill registration

The `.009` factory assembly drawing uniquely labels the vertical capacitor
immediately right of D99 as C19 and projects its body centre to
`(292.893,93.574)` mm. Raw owner component image
`PXL_20260710_200418174.jpg` independently shows the populated grey axial body,
both bent leads, and two separate board landings at that site. The registered
solder image `PXL_20260710_200522685.jpg` exposes the corresponding distinct
joint pair. The guard retains the registered 10 mm vertical span and pad
positions.

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

R102.1 and R108.1's remote connections come from recovered electrical
sheet 3; the owner photos alone do not establish those continuations.

## C20/C22 drill registration

The factory `.009` drawing identifies the overlapping vertical bodies at the
right end of D102 as C20 and C22. The owner component view shows two grey
axial capacitors leaning to the right of the package; the registered solder view exposes both joint pairs.
Their retained geometry has 10 mm vertical spans and columns 2.54 mm apart,
checked against the D102 pad grid. Exact centres and pad positions are in
[the placement guard](../kicad/check_analog_photo_placement.py).

C20's early July opposite face reads `±5`, while C22's May face carries
the `М75` temperature-stability group marking
([standard cross-check](../ref/datasheets/gost-m75-capacitor-marking.md)),
not a complete capacitance code. Two later July angles expose
bare `22` on both bodies, matching exact sheet 3's 22 pF nominal numerals.
The closer angle also reads `±10` on outer C22. Thus the photographed
tolerances are 5% for C20 and 10% for C22; both installed units remain
unverified. The standard's code mapping is retained only as a generic reference
in `ref/datasheets/gost-11076-69-capacitance-code.md`. Sheet 3 still closes
C20 on D102.6/.7 with R108 and C22 on D102.14/.15 with R102.

## Verification

Run from the repository root using Python with KiCad's `pcbnew` module and
NumPy. The original photographs must be materialized through
[Git LFS](git-lfs-policy.md#local-use) for the evidence hash checks.

```sh
/usr/bin/python3 kicad/check_analog_photo_placement.py
```

The guard checks stored centers and rotations, selected pad positions, VT2's
lap-pad construction and net assignments, and C94's boundary nets. It also
checks VT2/C94 evidence and R67's recorded value, photo hashes, and cross-side
transform. C16/C19, R92/R99, and C20/C22 are checked for placement and pad
positions here; their net assignments are not checked by this script.

These checks do not establish physical continuity or validate all board copper. See
[the source-PCB DRC audit](source-pcb-drc.md) for source pad/item collisions;
LVS is a separate connectivity check and does not validate placement.
