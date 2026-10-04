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

A native solder crop of `PXL_20260710_200522685.jpg` at `(1700,1150)`–`(2280,1450)` places pins 3–6 near x≈1897/1951/2005/2059, y≈1262. Pin 3 has a narrow northbound B.Cu departure that reaches an open annulus near `(2280,1213)` in a wider native crop; pin 4 enters a separate broad southbound strip, and pins 5–6 have no visible local B.Cu departure. The crowns and the exposed pin-3/pin-4 routes remain separated. D101-corner reflection projects the solder annulus near front `(1945–1957,1481–1486)`, where the native component crop shows a wide plated strip but no identifiable open drill. The opposite-face hole and any front-side or remote join still need continuity. See `ref/photos/juku-pcb-2/d101-section-a-input-solder-review.json`.

A native front crop `(2100,1350)`–`(2320,1520)` also shows no exposed F.Cu neck from registered pins 5 and 6 at the package edge, while pin 4 has a visible departure to the R99/R92 joint. Their solder crowns likewise lack local B.Cu departures. Hidden copper beneath the package remains possible, so neither pin is classified NC from the archive.

With D96 and D101 removed and power off, check D96.9 and each of D101.3,
D101.5, and D101.6 against D101.4, R92.1, and R99.2. Record the meter
readings separately.
Until then, the section-A input topology is source-closed and physically
unconfirmed. The structural Yosys view instantiates D101 with the joined
inputs and `IMDRG` enable. Runnable HDL omits the D97/D102/D101 precompensation
chain and holds D94 A4 (`d94_a4_d101_q0`) high; it does not simulate that
source-drawn section-A path. The separate section-A enable connection
D26.38/IMDRG↔D101.1 also awaits physical continuity; its source mapping is
recorded in [the precomp map](../ref/schematics/fdc-write-precomp-map.md).

D101.7 and D101.9 are separate in the exact drawing and canonical model;
owner continuity closes D101.7 to D94.14. Physical pin-7-to-pin-9 isolation
remains a useful check. See [the output review](d101-output-tie-photo-review.md).

## Model guard

```sh
python3 kicad/check_fdc_precomp_network.py
```

Run from the repository root with Python's standard library. This is the
[source guard described in the output review](d101-output-tie-photo-review.md#model-guard);
it does not run LVS or simulate the section-A path. Physical continuity and
precompensation timing remain separate checks.
