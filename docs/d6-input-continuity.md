# D6 input continuity correction

Status date: 2026-07-20

Status: **D6 A5/A6/A7 SOURCES MEASURED**

Direct continuity measurements on a physical `.009` processor board correct
the older-sheet assignment of D6's three high address inputs. The measurements
were accompanied by a visual copper trace where noted by the owner.

## Confirmed routes

```text
D26.15 PC1 --+-- D3.3 -> inverter -> D3.4 -- D6.1  A6
             +-- resistor pull-up -> +5 V

D26.14 PC0 --+-- D3.5 -> inverter -> D3.6 -- D6.2  A5
             +-- resistor pull-up -> +5 V

D6.15 A7 ------------------------------ D105.1
```

`D6.1 <-> D3.4` was reported as zero ohms and its copper was followed
visually. Direct continuity also proves `D6.2 <-> D3.6`, `D3.3 <-> D26.15`,
`D3.5 <-> D26.14`, and `D6.15 <-> D105.1`. An original-resolution
reread of the exact `.009` sheet-1 detail `PXL_20260718_101809608.jpg`
(crop `(1100,2750)`–`(2150,3850)`) confirms `R15=12k` on D26.14/D3.5
and `R16=12k` on D26.15/D3.3. Both terminate in the drawing's perpendicular
ground bar: vertical at R15, horizontal at R16. The rotated form agrees with
the ground symbol at D2.V1/V2 on sheet-1 detail `PXL_20260718_101817644.jpg`. The `.009`
assembly detail `PXL_20260711_114556899.jpg` places **R15 vertically to the
right of D3** and **R16 horizontally below D3**. The owner component photo
`PXL_20260710_200418174.jpg` shows distinct fitted bodies at those positions;
their dark markings are compatible with `12K`, but neither value nor both lead
connections have been measured.

The two upright red-black-red/gold **2 kΩ bodies left of D3 are R10 (outer)
and R9 (inner)** in the same original-resolution assembly crop. Their position
and value agree with exact `.009` sheet 1's 2 kΩ INT6/INT7 pull-ups. The former
R15/R16 `12k`-versus-`2k` claim came from assigning that left pair to the
wrong drawing labels and is retracted. The owner views show an apparent common
upper solder bridge for R9/R10. Test it to +5 V and test the separate lower
leads to D3.1/INT6_RAW and D3.13/INT7_RAW before treating their physical nets
as closed. Separately measure the right-side R15 and lower horizontal R16:
each signal lead against D3.5/D26.14 or D3.3/D26.15, and each return lead
against ground and +5 V. The source return bars and earlier owner-reported
+5 V paths remain a real electrical conflict for R15/R16 until the correct
physical bodies are probed. Source/photo registration is recorded in
`ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json`.

A separate actual-R15/R16 solder review uses the mirrored D3 field in
`PXL_20260710_200522685.jpg`. The vertical R15 candidate joints are near
`(2635,315)` and `(2635,525)`; the lower joint has a **direct, uninterrupted
B.Cu bridge to D3.5 near `(2723,530)`**. This physically corroborates the
source signal side of R15. The upper R15 lead leaves on front copper, whose
rail identity remains open. The horizontal R16 candidate pair is near
`(2855,855)`/`(2635,855)`. Its right lead runs on F.Cu from component
`(1555,1198)` to a plated annulus near `(1555,965)`; the matching B.Cu
annulus near `(2635,637)` has a direct bar to **D3.3** near `(2723,638)`.
The neighboring bright D3.2 front trace is separate and stops short of this
route. Thus R16’s signal side is photo-closed, while its left return lead
and both return-rail identities remain open. Inspect and measure the return
leads; see `ref/photos/juku-pcb-2/r15-r16-actual-pad-review.json`.

The adjacent solder panorama `PXL_20260710_200525009.jpg` overlaps the
right side of `PXL_20260710_200522685.jpg`. Two independent image patches
give an approximate translation of `(-2060,-112)` pixels between them.
The broad lower-lead search locations consequently move to about `(964,761)`
and `(905,783)` in the second panorama. At full resolution neither point
lands on an identifiable drilled annulus. Two narrow east-going routes cross
this region, but their attribution to the fitted resistors is unproven; the
cross-face package fit is only a search aid and cannot identify exact resistor
holes or D3 destinations.

A direct four-joint comparison for the R10/R9 left pair gives a stronger
provisional physical match in the first solder photo: outer R10 upper/lower near
`(2997,637)`/`(2995,863)` and inner R9 upper/lower near
`(2935,666)`/`(2935,889)`. In the component photo, the right upper lead
actually enters near `(1253,1005)` under the shared bridge; the earlier
`(1253,982)` point was on bare board. Both photos thus show the same
roughly 30-pixel stagger and mirrored column spacing. The lower solder
pads enter separate east-going tracks. A local affine fit of these four
joint pairs has a 2.15-pixel RMS residual. This is a provisional hole match,
not a traced connection to D3.1/D3.13 or proof of the common rail.

In overlapping solder photo `200525009`, the right lower candidate moves
to about `(875,777)`. Its separate copper line can be followed east to
an open annulus near `(3205,786)`. The left lower candidate moves to
about `(935,751)` and follows a separate line to another open annulus
near `(3260,786)`. The later `200527310` photo independently shows the
two annuli about 55 pixels apart, beneath a long soldered bar. A narrow
neck near the left annulus appears to approach that bar; continuity is
needed to decide whether they are joined. Both annuli are probe targets;
neither route yet identifies its D3.1/D3.13 signal or any front-side continuation.

Neither broad cross-face projection can place these two remote annuli
reliably in the component photos. The five-package fit extrapolates beyond
the left edge of `200418174`; a separate four-package fit into `200411500`
has about 61-pixel package-centre RMS. After registering adjacent component
photos, their search positions in `200415237` disagree by more than 120
horizontal pixels. No resistor-bank pad or front copper is assigned from
either projection.

The D3 solder field itself can be read more closely in `200522685`: its
two regular seven-joint rows are near `x=2723` and `x=2887`, from
`y=418` to `y=748` at roughly 55-pixel pitch. With the registered D3
component orientation, R10's expected D3.1 endpoint is near `(2723,748)`
and R9's expected D3.13 endpoint is near `(2887,693)`. Separately, the
source R15/R16 endpoints D3.5 and D3.3 are near `(2723,530)` and
`(2723,638)`; their visible solder copper approaches from the west. The
broad package projection falls roughly 8–30 pixels below this row and
cannot select the R9/R10 resistor holes by itself. Their front-side
continuations remain untraced.

In the component panorama `200418174`, a bright trace east of inner R9
ends near `(1278,1228)`, while its lower joint is
near `(1243,1215)`. The full-resolution image shows bare board across
the gap. The trace cannot be assigned to that resistor from proximity;
the lower lead still needs an identified solder-side hole or continuity.

The next solder panorama, `PXL_20260710_200527310.jpg`, overlaps only the
farther right region: two upper-image patches place its origin around
`x=1836` in `200525009`. Both resistor lower-lead search sites are left of
that frame. A route in the later image cannot be assigned to either
resistor without following it across the intermediate view first.

A cross-face fit from five already registered upper packages puts the two
upper resistor joints near `(3005,664)` and `(2935,671)` in solder panorama
`PXL_20260710_200522685.jpg` (package-centre RMS 15.9 px). The corresponding
solder region shows a narrow dogleg joining the upper joints and reaching a
long horizontal conductor near y615. The line reaches an open annulus near
`(3325,615)` farther east in the same solder view. Reverse registration
places that annulus near `(865,923)` on the component view, under D10's
body, so the front continuation is occluded; the lower-lead regions follow separate
narrow routes. This supports a common physical upper conductor while leaving
the exact hole matches and its +5 V/GND identity for continuity. See
`ref/photos/juku-pcb-2/r15-r16-two-face-review.json`.

The resulting proved D6 address order is:

```text
A0..A7 = BA15, BA14, BA13, BA12, BA11, /PC0, /PC1, D7.8 IO_CYCLE_H
```

## Explicit negative evidence

- D6.1 does not connect to D26; the older D26.17/PC3 assignment is rejected.
- D6.2 does not connect to any D26 pin; the older D26.16/PC2 assignment is
  rejected.
- D6.15 does not connect to any D26 pin; the older D26.13/PC4/FDC-density
  assignment is rejected.
- D105.1 does not connect to D105.12.
- The separately reconfirmed write-strobe net remains
  `D105.12 <-> D105.13 <-> D5.26`.

The initial session found no continuation beyond `D6.15 <-> D105.1`.
With D6 removed, resistance from D6.15 to both GND and +5 V fluctuates at
approximately 100-200 kohm. This excludes a simple low-value pull-up or
pull-down; the variation may reflect in-circuit charging or leakage, but does
not by itself prove a capacitor. That observation is retained as measurement
history. A later owner session on 2026-07-19 directly closed
`D7.8 -> D105.1 -> D6.15`; D7.8 is the output of the D7 NAND receiving raw
`/IORD` and `/IOWR`, so A7 is the I/O-cycle-active-high qualifier. The model
must not merge it with MEMW or FDC density.

## Modeling consequence

The structural model now routes D26 PC1 and PC0 through the measured D3
inverters before D6 A6 and A5, and routes D7.8 to D105.1/D6 A7.
Runnable selection now comes from the physical D6 table through `U_DECODE` under
the direct physical output mapping. The 2026-07-19 revision-3 reread proved that
the earlier artifact had all four data channels reversed; the separately named
functional decoder is retained only by the B37A diagnostic comparison. The A7
source and output-order questions are independently closed.

## Chip-removed output correction

A subsequent D6-removed measurement invalidates the earlier installed-PROM
claim that D6.11, D6.12, and D13.12 form one zero-ohm conductor. The physical
socket pads are separate:

```text
D6.12 ROM_N -> D8.15 E_N
D6.11 RAM_N -> D2.15 A7 / -WREQ
D6.11 RAM_N -> D92.5 and R12.2 pull-up branch
D6.11 RAM_N -/-> D8.15
D6.11 -/-> D6.12
D13.12 -> D6.14 V2
D6.13 V1 <-> D6.14 V2 (bottom-layer copper visually confirmed)
```

The same powered-off owner session directly confirms the complete decode-path
endpoint chain: `D6.9 -> D13.1`, `D13.2 -> D37.4`, and
`D37.6 -> D58.9`.

The other D37 NAND input is not an open continuity ask: the native sheet-2
route closes global `MEMR -> D33.3`, inverter output `D33.4 -> D37.5`, while
the guarded D37 package contract fixes pins 5/4->6 as that NAND section.

The model therefore restores the independent `ROM_SEL` output and moves
D6.11 onto the measured `WREQ_N` conductor. Follow-up owner continuity proves
that conductor also reaches D92.5/R12.2, with R12's other side at +5 V,
physically confirming the older-sheet pull-up branch while keeping D6.12
separate. D13.12
therefore feeds both physically tied D6 enable pins. The reported D13.12-to-D16.13 reading
is recorded as a follow-up candidate, not promoted connectivity, until D16 is
removed and the socket pad is rechecked.
