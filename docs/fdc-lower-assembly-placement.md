# FDC lower assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / PARTIAL ELECTRICAL MAPPING**

The upper FDC drawing places C12 between D94 and D100. May and early July
owner photos show that gap bare, while later July photo `PXL_20260710_202708344.jpg`
shows a fitted green bypass there with visible lap leads to D100.20/+5 V and
D94.8/GND. Its value and fitting history are unknown; the three matched open
holes in the earlier photo are not the visible lap-lead landings. See
`ref/photos/dgsh5-109-009-sb/fdc-upper-placement-registration.json`.

The photographed factory assembly drawing is registered to the five package centres
already fitted in the owner board photograph. D95, D101, and D102 define the affine
fit; D99 and D97 are independent checks. This establishes reference identity and
placement only, except where the owner-evidence records below explicitly close
R79-R85/R93/R94/R95/R98 plus R92/R99/R100/R102/R108/R86 values or visible copper connectivity.

Held-out errors: D99 `0.910` mm; D97 `0.851` mm.

| Ref | Projected x,y mm | Current x,y mm | Delta mm | Drawing observation |
| --- | ---: | ---: | ---: | --- |
| D93 | 235.941, 73.335 | 235.941, 73.340 | -0.000, -0.005 | physical КР1818ВГ93 socket centre; factory drawing corrects the former D95-overlapping global placement |
| R79 | 292.431, 19.166 | 292.431, 19.166 | -0.000, +0.000 | rightmost member of the factory R83..R79 vertical bank above D98; electrical sheet 3 assigns its 470-ohm pull-up to RD.DATA |
| R80 | 290.248, 19.189 | 290.248, 19.189 | +0.000, +0.000 | second-from-right member of the factory R83..R79 bank; electrical sheet 3 assigns its 470-ohm pull-up to -TR.00 |
| R81 | 288.066, 19.212 | 288.066, 19.212 | -0.000, +0.000 | centre member of the factory R83..R79 bank; electrical sheet 3 assigns its 470-ohm pull-up to -INDEX |
| R82 | 285.883, 19.235 | 285.883, 19.235 | +0.000, +0.000 | second-from-left member of the factory R83..R79 bank; electrical sheet 3 assigns its 470-ohm pull-up to -WR.PROTECT |
| R83 | 283.701, 19.258 | 283.701, 19.258 | -0.000, +0.000 | leftmost member of the factory R83..R79 bank; electrical sheet 3 assigns its 470-ohm pull-up to -READY |
| R84 | 245.220, 97.300 | 245.220, 97.300 | +0.000, +0.000 | vertical factory body immediately left of D95; electrical sheet 3 assigns its 470-ohm pull-up to D28.6/D93 READY. Registered component-photo joints supersede the coarse drawing-centre projection |
| R85 | 278.302, 66.090 | 278.302, 66.090 | +0.000, +0.000 | vertical factory body between D28 and D96; electrical sheet 3 assigns its 470-ohm pull-up to the separator clock |
| R94 | 271.987, 54.141 | 271.987, 54.141 | +0.000, -0.000 | leftmost vertical body in the R94/R93/R95 row above D28; owner identification and continuity confirm the sheet-3 10-kohm DRQ pull-up and supersede the former 220-ohm/D98 attribution |
| R93 | 277.444, 54.083 | 277.443, 54.083 | +0.001, +0.000 | left member of the paired vertical R93/R95 bodies above D28; exact sheet 3 assigns its 10-kohm pull-up to D93 INTRQ |
| R95 | 282.852, 54.319 | 282.852, 54.319 | +0.000, +0.000 | right member of the paired vertical R93/R95 bodies above D28; exact sheet 3 assigns its 2-kohm pull-up to the wired D28.10/.12 conditioner output |
| R78 | 267.999, 68.177 | 267.999, 68.177 | +0.000, +0.000 | left member of the factory-overlapped R78/R98 pair between D106 and D28; exact sheet 3 assigns the D106 preset/UP pull-up and the owner body directly reads 10K |
| R98 | 270.485, 68.177 | 270.485, 68.177 | +0.000, +0.000 | right member of the factory-overlapped R78/R98 pair between D106 and D28; electrical sheet 3 assigns its 4.7-kohm pull-up to -D.SEL1. Owner joints supersede the folded-drawing affine centre |
| C10 | 252.361, 73.163 | 252.361, 73.163 | +0.000, -0.000 | vertical C10 immediately right of D93; later July owner photo 202708344 exposes a green two-lead body at this position over neighboring D106; value and individual rail joins remain open; replaces the former lower-row collision with D102 |
| C11 | 268.232, 93.540 | 268.232, 93.540 | +0.000, +0.000 | vertical C11 between D95 and D99; earlier owner view shows landings without a secure body read, while later July image 202708344 exposes a green two-lead body there under the cable edge; value and individual rail joins remain open |
| C16 | 267.094, 101.055 | 267.094, 101.055 | +0.000, +0.000 | horizontal capacitor between the upper and lower IC rows |
| C15 | 280.230, 110.120 | 280.230, 110.120 | +0.000, -0.000 | vertical C15 between D97 and D102; later July views 202734776/202744232 show a green component edge at this factory position, but the cable hides most of the body and second lead; two-lead identity, value, and individual rail joins remain open |
| C19 | 292.893, 93.574 | 292.893, 93.574 | +0.000, -0.000 | vertical capacitor immediately right of D99; upper pad1 shares R100.1 and lower pad2 shares R86.1 |
| R92 | 253.869, 101.194 | 253.869, 101.194 | +0.000, +0.000 | horizontal resistor below D95 |
| R99 | 241.207, 103.467 | 241.207, 103.467 | +0.000, -0.000 | horizontal resistor below-left of D95 |
| R100 | 299.776, 94.000 | 299.776, 94.000 | -0.000, -0.000 | upper resistor in the four-part row right of C19; left-hand pin1 shares C19.1 and right-hand pin2 joins the common perimeter rail |
| R102 | 299.253, 97.229 | 299.253, 97.229 | +0.000, +0.000 | second resistor in the four-part row right of C19; right-hand pin2 joins the common perimeter rail |
| R108 | 298.731, 100.458 | 298.731, 100.458 | -0.000, +0.000 | third resistor in the four-part row right of C19; right-hand pin2 joins the common perimeter rail |
| R86 | 298.208, 103.688 | 298.208, 103.688 | +0.000, -0.000 | lowest resistor in the four-part row right of C19; left-hand pin1 shares C19.2 and right-hand pin2 joins the common perimeter rail |
| C20 | 299.917, 110.117 | 303.997, 110.024 | -4.080, +0.093 | factory C20 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 303.997,110.024 mm drill-span centre |
| C22 | 302.204, 110.093 | 306.537, 110.024 | -4.333, +0.069 | factory C22 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 306.537,110.024 mm drill-span centre |
| C17 | 303.000, 55.000 | 303.017, 55.000 | -0.017, +0.000 | factory-drawing identity plus local D98/D99 and target-photo lead correction for the populated vertical 120-uF axial electrolytic; the folded-sheet global affine drifts at this edge |
| R103 | 307.200, 47.200 | 307.200, 47.200 | +0.000, +0.000 | factory-drawing identity plus local right-edge correction for the vertical 47k timing resistor beside C17 |
| C18 | 303.000, 70.000 | 303.017, 70.000 | -0.017, +0.000 | factory-drawing identity plus target-photo lead registration for the populated vertical axial electrolytic directly marked 47 uF / 6.3 V |
| R97 | 298.620, 67.150 | 298.620, 67.150 | +0.000, +0.000 | factory-drawing identity plus local D99/right-edge correction for the vertical 47k timing resistor beside C18 |
| C83 | 239.150, 140.065 | absent | - | factory label reads C83 in the D41/D40 gap; the owner component photo has no fitted body. D41 package calibration maps two candidate front sites to x=246.172 mm, centered between D41.1 x=242.62 mm and D40.8 x=249.67 mm. The folded-drawing projection x=239.15 mm lies inside D41's span and is not an owner-pad placement. The promoted D41 fit aligns the front sites with solder crowns; same-hole identity remains unproved |

D93, C10, C11, C15, C16, C19, R79-R85, R92/R93/R94/R95/R98/R99, and the populated R100/R102/R108/R86 right-edge row have source-PCB footprints at their projected
factory-drawing positions. C20/C22 are also restored, but their table deltas are intentional: the drawing points identify the
overlapping body labels, whereas registered owner component and solder photos prove the actual adjacent 2.54 mm drill columns
at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans. C83 is absent at its factory callout:
the factory drawing shows its intended outline, while the owner photo shows no body in the D41/D40 gap. Two candidate front sites align with solder crowns under the promoted D41 fit, pending same-hole continuity. The separately photo-registered inherited DRAM-grid landing at `(176.1,145.6)` mm remains fabricated as bare common artwork.
Owner component photo `PXL_20260710_200418174.jpg` independently shows C19's grey vertical axial body and the four stacked resistor bodies in the same top-to-bottom order;
that corroborates population and orientation. Two independent component angles read R100/R102/R108=`12К` and R86=`4К7`. Recovered `.009` Э3 sheet 3 closes the common right-hand rail to +5 V, R102.1 to C22.2/D102.15, R108.1 to C20.2/D102.7, and the C19/R100 side to D97.7. Target copper closes C19.2/R86.1 to D97.6 and overrides the sheet's conflicting R86=470 reset annotation. The registered solder view
`PXL_20260710_200522685.jpg` exposes C19's two distinct joints; cross-side review corrects their recorded order to upper pad1 `(875,712)` and lower pad2 `(823,893)`. The July view also registers all four resistor pin-1 joints. An oblique May view literally reads `22` on C19's exposed face; the opposite July angle repeats only `22`. Exact `.009` sheet 3 specifies C19=`22` (nominal 22 pF), but neither body view shows a complete unit code; the installed capacitance remains a boundary. The same owner views
also show populated grey horizontal C16 between the IC rows and the red horizontal R92/R99 pair below D95. Their component-side landings and
backside joints corroborate the factory identities and 12.5/10.16 mm spans. The alternate May angle directly reads R92=`1К3` and R99=`4К7`;
the registered July view independently shows the same strings beneath stronger glare. Uninterrupted component copper closes R92.2-D95.14,
R92.1-R99.2-D101.4, and R99.1-D101.8/GND. The May view likewise literally reads bare `27` on C16; exact sheet 3 specifies `27` (nominal 27 pF) and closes its endpoints to D97.15/.14. The incomplete GOST body code leaves its installed capacitance unproved.
Those owner views additionally show the two grey C20/C22 axial bodies and all four solder joints independently of the factory identity drawing. Native May/early-July crops retract the former `1Н5` reading: they show partial tolerance/type markings. Two later July angles instead show literal `22` on both bodies, matching exact sheet 3's `22` (nominal 22 pF) for each. The closer angle also shows `±10` on outer C22, closing its tolerance to 10%; C20's lower line remains obscured. No complete unit code or capacitance measurement verifies either installed value. Sheet 3 closes their D102 timing endpoints.
The original-resolution lower drawing labels the vertical part between D41 and D40 as `C83`.
The owner component view is bracketed by direct fits of both marked packages and contains no fitted C83 body. Two candidate front sites form a plausible span and align with solder crowns under the promoted D41 fit; physical identity still requires continuity.
Whether the part was omitted at assembly or removed later is not recoverable from the image, but both histories yield the same exact target population: absent. C83 is present in the logical source model on +5 V/GND, but physical PCB placement and the owner-board pad pair remain unresolved. C63 remains a separate bare inherited DRAM-grid footprint. The unrelated `.006` RF-option C13 is also DNP on the `.009` target.
The later July owner image `PXL_20260710_202708344.jpg` exposes green two-lead
bodies at the factory C10 and C11 positions. Their values and lead rails remain
unproved; the earlier C11 view only exposed landings. Two later views show
a green C15-position body edge between D97/D102, but the cable hides its
second lead, so component identity and rails remain candidate evidence.
See `ref/photos/juku-pcb-2/fdc-bypass-late-population-review.json`.
