# PHI2TTL and D29 command-buffer route

Status: **SOURCE MODEL CORRECTED / PHYSICAL RC PLACEMENT AND CONTINUITY PENDING**

The full-sheet `.009` electrical schematic and continuity on the CS00015
processor board establish D29.1 as the clock input whose buffered output,
D29.19, is `CCLCK`.

## Primary evidence

- Exact-revision source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101754468.jpg`
  (`ДГШ5.109.009 Э3`, sheet 1), SHA-256
  `effc98746807ef28dab97051ceba293f4433c0f3b39b86cbb55ddcaad24aeca4`.
- Owner continuity on CS00015, 2026-08-04, confirms that the D35.13 clock
  path reaches D29.1.

On sheet 1, `(2) Ф2 TTL` enters D30 CLK1/pin 3.  The junction immediately
before D30.3 branches downward; the conductor can be followed across the full
sheet to D29 physical pin 1.  D29.1 is the A1 command-buffer channel and its
paired output D29.19 is explicitly labelled `CCLCK`.

Sheet 2 places R35 (330 ohms) between the `Ф2TTL` trunk and the local D35.13
RC-shaped input node, with C29 marked `56` and R106 unambiguously marked `910`
to ground at original-resolution sheet-2 crop `(0,2200)`–`(600,2750)` on
the D35 side (`PXL_20260718_101911242.jpg`). The capacitor's unit is not
printed in this view. Therefore D35.13 must
not be collapsed onto the zero-ohm `PHI2TTL` copper net in the replica model.

## R35/R106/C29 owner placement and value limits

Factory assembly `PXL_20260711_114611058.jpg` identifies C29 as the left
callout and R106 as the right callout of the close pair below R35, between
D38 and D92. A wider comparison to owner component `PXL_20260710_200418174.jpg`
shows the upper body marked `330R` as
R35, matching the source 330 Ω value. The lower axial body is in the R106
position. A crop of original owner pixels `(2270,2480)`–`(2390,2740)`,
rotated upright, reads `510R`: the first glyph has the flat upper stroke
and lower curve of `5`. This conflicts with schematic `910`, so the physical
resistance still needs measurement before adopting a value. No separate
capacitor body is exposed at the C29 position.
The adjacent July overlap `PXL_20260710_200415237.jpg` ends above this
resistor pair. The earlier May image `PXL_20260519_201907078.jpg` does
show the same two bodies: original crop `(2140,250)`–`(2320,720)` rotated
180° reads `510R` on R106 and `330R` on R35. See
`ref/photos/juku-pcb-2/r106-cross-date-review.json`. This independently
confirms the owner-board marking on two dates, while resistance and pad
connectivity still require measurement. Both owner dates also show no
separate component body at the visible C29 position; this is owner
population evidence only, since the candidate annuli remain unpaired.

The upper and middle front joints beside R106 are the stronger C29 pad-pair
candidates. Cross-face geometry and visible copper support the upper joint
joining R35's lower lead and R106's upper lead on the post-R35 node; the
middle candidate reaches the D56.8-grounded rail. The lower open annulus
may be a downstream via. These findings do not establish C29's population
or its physical value. Native coordinates, fit residuals, and the May
cross-check are retained in
[the C29 landing review](../ref/photos/juku-pcb-2/c29-landing-pair-review.json).

The assembly and marked owner package agree on D35's notch-up orientation,
but neither face exposes an uninterrupted route from D35.13 to the post-R35
node. Registered probe sites and the cross-face fit limits are in
[the D35 pin-13 review](../ref/photos/juku-pcb-2/d35-pin13-photo-review.json).
Measure that continuation, R106's resistance and both lead connections,
and inspect C29 on both faces before assigning physical values or DNP status.

### C29 source nominal

Full-resolution `.009` sheet-2 photo `PXL_20260718_101908284.jpg` prints
only `56` beside C29, with no unit glyph; the neighboring C6 also uses bare
`56` and is modeled as 56 pF. With the drawing's 910 Ω R106, 56 pF gives
about 51 ns whereas 56 nF gives about 51 µs in this MHz clock section.
With the owner body's `510R` marking, the same hypothetical 56 pF gives
28.6 ns. This makes the photographed resistor discrepancy material to the
clock-shaping branch, although the simple RC product does not establish an
actual edge delay or C29's presence.
The native-sheet convention reads bare values below 1000 as pF, making
**56 pF the source nominal**. The unit is not explicitly printed beside C29.
A BOM or direct part reading is still needed to establish the owner-board
component and its actual value.

## R36/R37 phase-output pull-ups

The same exact sheet-2 detail resolves the two 360-ohm output branches:
R37 joins the printed `B` rail to D35.10 / `Ф1` (factory wire А:7), while
R36 joins `B` separately to D35.12 / `Ф2` (А:14). The `B` conductor crosses
the `Ф1` line without a junction before reaching R36. The sheet-2 power
table in `PXL_20260718_101924004.jpg` explicitly defines `B (+12)`.
Thus these are two +12 V pull-ups, not a resistor between the phase outputs.
The factory placement view `PXL_20260711_114604420.jpg` puts R37 left of
R36 immediately beside D1; owner component views `PXL_20260710_200411500.jpg`
and `PXL_20260710_200439607.jpg` show the corresponding populated pair.
In `200411500`, a visible front-copper spur runs from R37's lower lead joint
to the white-wire A:7 start below it. That independently supports the
R37-to-Ф1 side of the schematic at the photographed landing. The R36-to-А:14
path is not comparably exposed. In `200439607`, a vertical front trace leaves
R36's lower joint, is briefly hidden by the white-wire crossing, then
reappears and bends toward the upper lug of a nearby vertical metal can. Its
assembly position makes C1 a candidate for that can, yet exact sheet 1 puts
C1 on the separate reset RC node. The short occlusion and unregistered can
identity leave the apparent route unproved; see
`ref/photos/juku-pcb-2/r36-r37-body-marking-review.json`.

The four visible component-side lead joints can be placed approximately with
the registered D1 pin-1/pin-20/pin-21 affine frame in `200411500`. These are
inspection coordinates (about ±1 mm), not promoted pad or net assignments:

| Body lead | Approx. `200411500` pixel | Approx. board mm | Connection status |
| --- | --- | --- | --- |
| R37 upper | (645,2575) | (16.346,169.862) | +12 V per schematic; physical copper untraced |
| R37 lower | (645,2855) | (16.346,182.538) | front-copper spur to A:7 visible |
| R36 upper | (735,2575) | (20.490,169.862) | +12 V per schematic; physical copper untraced |
| R36 lower | (735,2855) | (20.490,182.538) | phase-side path passes under wire; continuity pending |

Both +12 V joins and the R36 phase join still require physical verification
before these estimated positions can become PCB footprint landings.

## Clock-input topology and resistance checks

The diagram uses schematic nominal values; R106's owner marking is `510R`,
and C29's population remains unconfirmed.

```text
                         +--> D30.3
PHI2TTL -----------------+--> D29.1 --> D29.19 CCLCK
                         +--> R35 330R --> D35.13
                                           +-- C29
                                           `-- R106 910R
```

Expected powered-off checks are approximately 0 ohms from D29.1 to D30.3 and
330 ohms from D29.1 to D35.13.  Record the measured resistance rather than
relying only on a continuity beeper because some meters beep through 330 ohms.

## D29 continuation and pin numbering

The cross-sheet identifiers `1 -MRD`, `2 -MWR`, `7 -IOWR`, and `8 -IORD`
are continuation numbers, not D29 package pins. Physical channel order is
recorded in [the exact D29 pin map](d29-exact-command-map-hold.md) and
`ref/schematics/d29-exact-009-pinmap-review.json`.

## Replica-model disposition

The source model, generated schematic, three PCB pad maps, HDL, and pinout
audit now assign D29.1 to PHI2TTL and D35.13 to the separate post-R35 node.
R35, R106, and C29 are modeled as schematic-only parts pending owner pad
registration, population/value checks, and footprint placement. Current routed copper and fabrication holds are recorded in
[factory-wire fidelity](factory-wire-route-fidelity.md) and
[the routed audit](routed-refresh-audit.md). Source-model alignment does not
establish owner-board continuity or a completed RC footprint layout.
