# Factory modification disposition

Status date: **2026-07-17**.

Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**

The `ДГШ5.109.009 СБ` Вид В detail marks local assembly work around
D56, D15, D14, and D11. Assembly note 11 explicitly identifies position
150 as tubing fitted at solder locations; position 159 is therefore kept
as an unexpanded solder-location callout because its specification row
was not photographed. Only the D15 detail explicitly says `Разрезать`.
Three component views plus two overlapping solder views register D56's
callout row. The same two solder views independently close D56.1 and
D56.9 onto its pin-8 ground perimeter; this trigger closure is separate
from the still-held position-159 field. Independent evidence also closes
the D15 cut topology and local D14 ground link. D11 bridge endpoints and
the remaining D14 auxiliary paths stay held.

| Ref | Factory operation locality | Current disposition | Closure evidence |
| --- | --- | --- | --- |
| D56 | АГ3 timing area: trigger pins D56.1/D56.9 are photo-closed to the D56.8 ground perimeter; the separate position-150 tubing and three position-159 solder locations remain held | PARTIAL PHOTO-CLOSE — D56.1/D56.9 are grounded with D56.8; all three separate callout locations are fixed but their installed conductor is held | two solder views show uninterrupted perimeter copper through pins 1/8/9; validated fits also identify the distinct left annulus and D56.5/D56.12 callout row, where continuity or item 159 is still required |
| D15 | EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail | PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches | two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held |
| D14 | АП2 serial-driver area: registered notch-up orientation maps both package rows; local copper closes the D32.4/GND-to-D14.1 link and the fifth auxiliary landing is geometry-registered, while its conductor and remaining traces stay held | PARTIAL PHOTO-CLOSE — local copper preserves D32.4/GND-to-D14.1 and the fifth landing is registered; its conductor and remaining drawn traces are held | two independent component views plus notch-oriented factory row registration; map the fifth landing conductor, three long traces, and right-row dogleg before full release |
| D11 | 8251 USART area: the unique L trace registers the long hole column as an auxiliary drilled/copper field, not a package row; four component-side position-159 solder locations are photo-registered, while package-local cross-side review finds no unique matching four-hole field | GEOMETRY REGISTERED / ELECTRICAL HOLD — four position-159 solder locations identified; bridge and remote trace endpoints remain obscured | two component views register the L trace and four-landmark topology; validated two-sided package fits exhaust four solder views, so direct continuity is required to assign any D11 pin/net |

## D56 callout-field registration

Three overlapping component photographs identify the same notch-down
`К155АГ3 8901` package beside the right board edge. Held-out-validated
component and reflected local-package fits replace the displaced global
endpoint seeds. The drawing's three leaders register as the separate left
annulus, D56.5, and D56.12 at one physical level. Assembly note 11 says
tubing positions 157 and 150 are fitted at solder locations. Position 150
is therefore not a cut
instruction, and the nearby visible wide-rail gap cannot be promoted as
proof of the D56.12 net partition. Position 159 remains an unexpanded
solder-location callout until its specification identity is recovered.
This callout hold is independent of the package trigger inputs: both
overlapping solder views show D56.1 and D56.9 on the same uninterrupted
wide perimeter conductor as ground pin D56.8, so the source model now
grounds both active-low A inputs.

| Solder view | Left-landing error | D56.5 error | D56.12 error | Result |
| --- | ---: | ---: | ---: | --- |
| PXL_20260710_200530933.MP.jpg | 0.000 px | 0.000 px | 0.000 px | package-local reference |
| PXL_20260710_200522685.jpg | 0.585 px | 11.514 px | 9.684 px | independent overlap |

Both solder views show small bare-board gaps between the D56.5/D56.12
pads and the adjacent horizontal rail; the separate left annulus belongs
to that rail. This closes the three-location geometry, not the installed
assembly conductor. Direct continuity or the complete position-159
specification is required before changing the clean source net partition.

| Ground-rail view | D56.1 registration error | D56.8 registration error | D56.9 registration error | Result |
| --- | ---: | ---: | ---: | --- |
| PXL_20260710_200530933.MP.jpg | 0.000 px | 7.878 px | 0.000 px | accepted uninterrupted GND perimeter |
| PXL_20260710_200522685.jpg | 0.001 px | 0.000 px | 0.000 px | accepted uninterrupted GND perimeter |

The primary view exposes the complete upper rail and left-edge return;
the overlap independently repeats both pin levels. D56.1 and D56.9 are
therefore closed to `GND` with D56.8 without inferring any position-159
conductor or changing the D56.5/D56.12 callout-row partition.

## D15 cut registration

The enlarged factory detail draws four holes on the auxiliary trace and
places `Разрезать` between the final pair, aligned between D15 pad levels
8 and 9. The same pair is visible with removed intervening copper in two
independent component photographs. Reflected solder copper connects the
upper landing to D15.8 (`A2`) and the lower landing to D15.9 (`A1`).
No replacement conductor is drawn in the D15 detail: the operation removes
an unwanted A2/A1 bridge, which is exactly the net partition already present
in the clean source PCB.

| Landing | Board centre (mm) | Component-view agreement | Solder-view error | Resulting source net |
| --- | --- | ---: | ---: | --- |
| upper | (14.129, 73.247) | 0.018 mm | 0.016 mm | D15.8 / `A2` |
| lower | (14.350, 75.515) | 0.030 mm | 0.023 mm | D15.9 / `A1` |

These centres prove local identity and topology, not fabrication-ready drill
placement. The source board therefore keeps its clean A2/A1 separation and
does not invent the two auxiliary holes until a direct dimension or
fabrication-grade local scale is available.

## D14 position-159 registration

Both component photographs fix D14 and D32 notch-up. This maps the
factory detail's four-hole right row to D14.8 through D14.5 and the
first four holes of the five-hole left row to D14.1 through D14.4.
The position-159 leader reaches the D14.1-side stub. In both views, one
uninterrupted copper strip joins that landing directly to D32.4, already
a guarded `GND` pin. The clean source model therefore assigns D14.1 to
`GND` and preserves the executed factory topology without adding an
unmeasured auxiliary drill.

| Component view | D32.4 fit error | D14.1 fit error | Link-length error | Result |
| --- | ---: | ---: | ---: | --- |
| PXL_20260710_200358952.jpg | 0.002 mm | 0.002 mm | 0.003 mm | continuous D32.4/GND-to-D14.1 copper |
| PXL_20260710_200402344.jpg | 0.010 mm | 0.001 mm | 0.010 mm | continuous D32.4/GND-to-D14.1 copper |

The open fifth left-field annulus below D14.4 is also reproducible in
both component views.

| Landing | Provisional board centre (mm) | Component-view agreement | Disposition |
| --- | --- | ---: | --- |
| fifth auxiliary landing | (207.887, 49.900) | 0.011 mm | geometry registered; conductor and fabrication drill held |

The landing's conductor, the three long drawn traces, and the right-row
dogleg are not electrically closed by these views. Reflected registration
into `200506061` and `200509593` places the same locality inside a heavily
scraped/reworked two-row solder field; the component face hides the immediate
dogleg under the package body. The available photographs are therefore
exhausted for D14.7 rather than evidence for a guessed path. D14.2 and D14.7
require direct continuity, and no remote net or fabrication geometry is
inferred from the drawing alone.

## D11 position-159 field registration

The component photographs correct the earlier interpretation of the
factory detail. Its long hole column and unique L-shaped trace are the
auxiliary drilled/copper field beside D11, not a drawn 14-pad package
column. The four-landmark subfield is reproducible in two independent
component views: a long vertical trace joins the upper landing to the
position-159 junction, a left landing approaches that junction through
the obscured bridge, and a lower landing departs on a separate trace.

| Landing | Provisional board centre (mm) | Component-view agreement | Disposition |
| --- | --- | ---: | --- |
| upper_rail | (190.816, 59.870) | 0.001 mm | registered topology; fabrication drill held |
| bridge_left | (188.358, 74.323) | 0.001 mm | registered topology; fabrication drill held |
| position159_junction | (190.863, 73.201) | 0.001 mm | registered topology; fabrication drill held |
| lower_exit | (189.622, 76.661) | 0.000 mm | registered topology; fabrication drill held |

These board centres use the panorama's coarse component-grid fit and are
topology locators, not pin- or fabrication-grade coordinates. In
particular, the validated D11 solder overlay localizes a conspicuous scar
beside pins 4 through 6, but cross-registration shows that scar is a
different feature and cannot identify the factory position-159 bridge.
The nearest provisional field centre is 12.946 mm
from the nominal D11.4-.6 column, more than twice the component-grid
held-out error ceiling (5.464 mm); the exclusion
therefore survives the coarse global-fit uncertainty.
A newly validated D11 component package fit now pairs with that reflected
solder fit. Their package-local transform projects the upper landing under
the wide tinned rail and the lower three landmarks among repeated joints
and parallel traces without a unique four-hole match. All four overlapping
solder photos repeat the lower-field ambiguity; the second complete view
also repeats the upper rail obstruction. The available photographs are
therefore exhausted for through-hole identity rather than evidence for a
guessed snap. D11 pin/net and both remote endpoints require direct
continuity, and no source net or auxiliary drill is changed.

## Guarded evidence

- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.
- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.
- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.
- `PXL_20260711_114649169.jpg`: assembly note 11 identifies position 150 as tubing at solder locations.
- `factory-modification-registration.json`: D56 field registration, D15/D14 closures, and two-view D11 registration.
- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.

## Release rule

Do not release or reroute the board on netlist equivalence alone. For each
of the D56 three-callout field, the obscured D11 bridge, and the remaining
D14 detail, identify the pad/via pair(s) and conductor topology; then
prove the final source-PCB net partition matches the factory result.
D15 and the D14.1 ground link are electrically closed; their unmeasured
auxiliary-hole geometry remains
held only for an original-artwork replica.
