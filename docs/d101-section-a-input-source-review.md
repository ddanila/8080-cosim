# D101 section-A input junction: source and physical evidence

The native `.009 Э3` sheet-3 frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101648508.jpg`
(SHA256 `ef04482bdd7f15a20e132034709bb7b6dfab54d6ac9d4efe2f6510575b4aa641`)
draws D101 К555КП12 A0, A1, A2, and A3 at physical pins 6, 5, 4, and 3.
Their four horizontal inputs meet the same vertical conductor at filled junction
dots. This closes the four inputs together **in the drawing**.

The conductor leaves A0/pin 6 to the left, then turns upward and exits the
top of this detail frame. The full sheet-3 overview
`PXL_20260718_101633062.jpg` (SHA256
`5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047`)
retains the missing span: D96 section-2 Q/pin 9 turns downward, runs left
below the D93 interrupt pull-ups, then descends to D101 A0/pin 6. Its
crossings with the D100 control lines have no junction dots. The source
model therefore joins D96.9 to the four D101 section-A inputs. This is a
drawing closure, not a board continuity result.

The calibrated owner component view
`ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows target copper
joining D101.4 to R92.1 and R99.2. That visible copper establishes the
physical identity of the modeled `D101_D02_R92_R99` island, but the archived
views do not independently establish that D101.3, D101.5, or D101.6 reach it.
The model assigns these three pins to the island from the sheet-3 junctions;
this remains a physical verification item. The sheet's use of `R99` at the
D101 output is a separate known annotation conflict and supplies no evidence
about these input joins.

A native solder crop of `PXL_20260710_200522685.jpg` at `(1700,1150)`–`(2280,1450)` places pins 3–6 near x≈1897/1951/2005/2059, y≈1262. Pin 3 has a narrow northbound B.Cu departure that reaches an open annulus near `(2280,1213)` in a wider native crop; pin 4 enters a separate broad southbound strip, and pins 5–6 have no visible local B.Cu departure. The crowns and the exposed pin-3/pin-4 routes remain separated. This bounds the photographed evidence; a front-side or remote join still needs continuity. See `ref/photos/juku-pcb-2/d101-section-a-input-solder-review.json`.

With D96 and D101 removed and power off, check D96.9 and each of D101.3,
D101.5, and D101.6 against D101.4, R92.1, and R99.2. Record the meter
readings separately.
Until then, the section-A input topology is source-closed and physically
unconfirmed; the runnable HDL keeps this half of D101 outside active precomp
behavior. The independent D101.7/.9 output-tie conflict also remains open.
