# FDC lower assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / PARTIAL ELECTRICAL MAPPING**

The photographed factory assembly drawing is registered to the five package centres
already fitted in the owner board photograph. D95, D101, and D102 define the affine
fit; D99 and D97 are independent checks. This establishes reference identity and
placement only, except where the owner-evidence records below explicitly close
R92/R99/R100/R102/R108/R86/C20/C22 values or visible copper connectivity.

Held-out errors: D99 `0.910` mm; D97 `0.851` mm.

| Ref | Projected x,y mm | Current x,y mm | Delta mm | Drawing observation |
| --- | ---: | ---: | ---: | --- |
| D93 | 235.941, 73.335 | 235.941, 73.340 | -0.000, -0.005 | physical КР1818ВГ93 socket centre; factory drawing corrects the former D95-overlapping global placement |
| C10 | 252.361, 73.163 | 252.361, 73.163 | +0.000, -0.000 | vertical C10 immediately right of D93; replaces the former lower-row collision with D102 |
| C11 | 268.232, 93.540 | 268.232, 93.540 | +0.000, +0.000 | vertical capacitor between D95 and D99; owner component view shows its landings but no unambiguous body |
| C16 | 267.094, 101.055 | 267.094, 101.055 | +0.000, +0.000 | horizontal capacitor between the upper and lower IC rows |
| C15 | 280.230, 110.120 | 280.230, 110.120 | +0.000, -0.000 | vertical capacitor between D97 and D102; owner component view is cable-obscured |
| C19 | 292.893, 93.574 | 292.893, 93.574 | +0.000, -0.000 | vertical capacitor immediately right of D99; upper pad1 shares R100.1 and lower pad2 shares R86.1 |
| R92 | 253.869, 101.194 | 253.869, 101.194 | +0.000, +0.000 | horizontal resistor below D95 |
| R99 | 241.207, 103.467 | 241.207, 103.467 | +0.000, -0.000 | horizontal resistor below-left of D95 |
| R100 | 299.776, 94.000 | 299.776, 94.000 | -0.000, -0.000 | upper resistor in the four-part row right of C19; left-hand pin1 shares C19.1 and right-hand pin2 joins the common perimeter rail |
| R102 | 299.253, 97.229 | 299.253, 97.229 | +0.000, +0.000 | second resistor in the four-part row right of C19; right-hand pin2 joins the common perimeter rail |
| R108 | 298.731, 100.458 | 298.731, 100.458 | -0.000, +0.000 | third resistor in the four-part row right of C19; right-hand pin2 joins the common perimeter rail |
| R86 | 298.208, 103.688 | 298.208, 103.688 | +0.000, -0.000 | lowest resistor in the four-part row right of C19; left-hand pin1 shares C19.2 and right-hand pin2 joins the common perimeter rail |
| C20 | 299.917, 110.117 | 303.997, 110.024 | -4.080, +0.093 | factory C20 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 303.997,110.024 mm drill-span centre |
| C22 | 302.204, 110.093 | 306.537, 110.024 | -4.333, +0.069 | factory C22 identity/body marker at the right end of D102; registered owner photos supersede this label-centre projection with the actual 306.537,110.024 mm drill-span centre |
| C63 | 239.150, 140.065 | 176.100, 145.600 | +63.050, -5.535 | factory label reads C63, not C13, in the gap between D41 and D40; owner component photo shows no populated body or coherent drilled lead pair at that exact site |

D93, C10, C11, C15, C16, C19, R92, R99, and the populated R100/R102/R108/R86 right-edge row have source-PCB footprints at their projected
factory-drawing positions. C20/C22 are also restored, but their table deltas are intentional: the drawing points identify the
overlapping body labels, whereas registered owner component and solder photos prove the actual adjacent 2.54 mm drill columns
at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans. The C63 target site remains an explicit
population/BOM discrepancy: the factory drawing shows its outline, while the raw owner photo shows the exact D41/D40 gap bare, without a body or coherent drilled lead pair.
Owner component photo `PXL_20260710_200418174.jpg` independently shows C19's grey vertical axial body and the four stacked resistor bodies in the same top-to-bottom order;
that corroborates population and orientation. Two independent component angles read R100/R102/R108=`12К` and R86=`4К7`. Uninterrupted component copper joins all four right-hand pin-2 leads to one perimeter rail; its remote destination and R102/R108 pin-1 destinations remain continuity tasks. The same two angles directly show C19's upper lead and R100.1 sharing one landing, and C19's lower lead and R86.1 sharing another; only the two joined nets' remote destinations remain open. The registered solder view
`PXL_20260710_200522685.jpg` exposes C19's two distinct joints; cross-side review corrects their recorded order to upper pad1 `(875,712)` and lower pad2 `(823,893)`. The July view also registers all four resistor pin-1 joints, while the independent May angle and solder field expose no unique remote continuation for R102.1/R108.1. An oblique May view literally reads `22` on C19's exposed face, but no unambiguous unit/decimal glyph; its value/unit remains a boundary. The same owner views
also show populated grey horizontal C16 between the IC rows and the red horizontal R92/R99 pair below D95. Their component-side landings and
backside joints corroborate the factory identities and 12.5/10.16 mm spans. The alternate May angle directly reads R92=`1К3` and R99=`4К7`;
the registered July view independently shows the same strings beneath stronger glare. Uninterrupted component copper closes R92.2-D95.14,
R92.1-R99.2-D101.4, and R99.1-D101.8/GND. The May view likewise literally reads bare `27` on C16, but GOST 11076-69 Table 1 requires a unit/decimal letter for a coded capacitance; C16's value/unit and destinations therefore remain boundaries.
Those owner views additionally show the two grey C20/C22 axial bodies and all four solder joints independently of the factory identity drawing. Enhanced July pixels
read C20=`1Н5`, and an independent May angle directly reads the outer C22 body as `1Н5`; GOST 11076-69 Table 1 maps both codes exactly to 1500 pF / 1.5 nF, now adopted for both parts. Their tolerances, voltages, and endpoints remain unpromoted.
The lower drawing also labels the vertical part between D41 and D40 as `C63`, not `C13`.
The owner component view is bracketed by direct fits of both marked packages and contains neither a fitted C63 body nor a coherent two-hole span.
That makes DNP/removal the leading `.009` owner-board disposition, but the old generic array placement is not silently moved or deleted until factory-population intent is reconciled. The unrelated `.006` RF-option C13 is now correctly DNP on the `.009` target and must not be conflated with this C63 site.
The owner component view does not expose a complete electrical path at either corrected
site: C11's landings are visible without an unambiguous body, while C15 is hidden by the
factory cable. Neither placement is connectivity evidence.
