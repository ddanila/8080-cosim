# D99 one-shot timing and control map

The exact-revision `ДГШ5.109.009 Э3` sheet-3 detail
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` draws both halves of
D99 (К155АГ3). The target assembly drawing
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` independently places
the four timing parts.

| D99 endpoint | Exact connection |
| --- | --- |
| 1 `A_N`, 3 `CLR_N` | GND |
| 10 `B2` | marked junction with D96.13 `/CLR2`; shared continuation to sheet 1, remote source unresolved |
| 11 `CLR2_N` | marked junction on the `MOTOR EN (1)` rail across the overlapping sheet-3 detail frames; modeled with D26.16, original-board continuity unmeasured |
| 4 `Q1_N` | full sheet-3 overview shows its westbound rail immediately above the distinct D94.14/D101.7 rail, descending into D93 HLT/pin23; original-board continuity remains unmeasured |
| 2 `B1`, 5 `Q2` | E12 post 2 takes B1; Q2 branches to E12 post 1 and E11 post 1 as alternate sources and descends to D100 A7/pin7; drawn E12 bridge selects posts 2–3, with post 3 on the D93.28/D100.3 HLD line |
| 12 `Q2_N` | descends to D100 `OE_N`/pin9; crosses D100 `T`/pin11 without a junction dot |
| 6 `C2`, 7 `RC2` | polarized C17 `120,0`; RC junction pulled to +5 V by R97 `47к` |
| 14 `C1`, 15 `RC1` | polarized C18 `47,0`; RC junction pulled to +5 V by R103 `47к` |
| 13 `Q` | omitted/unused; the complementary pin 4 output is drawn |

Electrical pairing and physical proximity cross here. In the original-resolution
assembly view `PXL_20260711_114600417.jpg`, R103 is immediately beside the
upper C17 body, while R97 is immediately beside the lower C18 body. Exact
sheet 3 nevertheless connects **R103 to C18/RC1** and **R97 to C17/RC2**.
The board model follows those drawn nets; nearby component bodies alone must
not reverse the two timing networks. The extra owner-visible 220 Ω body
recorded as `RUNK1` between this cluster and D98 is neither of the two 47 kΩ
resistors, and the drawing does not identify it as R96.

Both capacitor symbols carry polarity marks. The target component view directly
shows axial electrolytics and reads C18 as `47 мкФ / 6.3 V`; the sheet value
closes C17 as `120 мкФ`. Their factory body centres are corrected locally
against D98/D99 and the owner-board view because the folded sheet's global
lower-FDC affine drifts at the right edge. E12's physical posts, population,
and continuity remain unconfirmed; see
[the selector review](../../docs/d99-e12-selector-source-review.md).

## Source evidence

The two native sheet-3 frames `PXL_20260718_101637906.jpg` and
`PXL_20260718_101641055.jpg` overlap at D93 and its input rails. Following
the `MOTOR EN (1)` rail rightward in that overlap leads to a filled junction
and D99 pin 11 `/CLR2` in the latter frame. The first frame's SHA256 is
`ba6f618ea610f05617cde668660a767c103116bcd55f46862a36cbe385ee26e4`;
the second frame's SHA256 is
`86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`.

The full sheet-3 overview `PXL_20260718_101633062.jpg`, native crop
`(1850,520)-(3072,1650)`, shows D99.4
turns west at approximately `(2564,689)` on the rail **above** the
D94.14/D101.7 rail near `y≈725`. The same overview draws D101.7/Q0 onto the D94.14
rail, independently agreeing with owner continuity. Following the D99.4
rail west in overview crop `(1230,590)-(1640,1350)` reaches D93 HLT/pin23;
its descent crosses the E11 post-1 vertical without a dot. Keep the
source-joined D99.4/D93.23 island separate from D94.14/D101.7. Original-board
D99.4↔D93.23 continuity remains unmeasured.

Native left-tile crop `(1150,900)-(2300,3000)` sharpens the D94.14 end:
its line runs west from pin 14, turns north around source x≈1560, and meets
the lower upper rail around y≈1380. The northward leg crosses the separately
labeled `-RES`, `CS7`, `A8`, and `A9` lines without a filled junction at any
crossing. This excludes those nearby control rails as alternate readings of
the D94.14 continuation. The separate overview establishes its D101.7
destination without promoting the adjacent D99.4 rail.

## Physical route limits

The registered board-photo points put D99.4 at solder-image
`PXL_20260710_200522685.jpg` `(1124.714,901.429)`, D101.7 in that
image at `(2112.714,1260.286)`, and D94.14 in
`PXL_20260710_200506061.jpg` at `(1945.714,1177.714)`; see
`ref/photos/juku-pcb-2/endpoints.csv`. A native-resolution recheck finds
their plated landings but no uninterrupted visible copper route between
these three points. The component-side D99 package is crossed by the cable,
and a route can change sides through a plated hole. This photo result
therefore neither confirms nor refutes the owner's D94.14-D101.7 continuity
or D99.4's separate remote route.

The original-pixel solder crop `(900,750)-(1350,1100)` of `200522685`
locates D99.4 near `(1125,901)` as a discrete fourth joint in its visible
row. It has no visible local B.Cu departure. The next joint to the right has
a separate upward copper trace; that neighboring trace must not be assigned
to D99.4. A front-face route beneath the installed D99 package remains
possible, so this narrows the probe site but does not settle D99.4's route.

## Unresolved sheet-1 continuations

The parenthesized/quoted `1` beside the D99.10 conductor denotes the destination
sheet, not a logic level. Full-resolution `PXL_20260718_101641055.jpg` shows
D96.13 running directly to the marked junction on D99.10's line. Their shared remote source remains
unread on sheet 1. Native crop `(0,1100)-(1800,2200)` also separates this
pin-10/pin-13 branch from the crossing D96.9 output line: the branch has its
own junction just below D99 and a quoted `1` continuation arrow, while the
output line crosses it without a junction. The arrow gives no unique source
pin, so the two lines must not be merged from their crossing. D100.9 is
connected to D99.12; D100.11 has a separate
sheet-1 boundary; see [the D100 control review](../../docs/d100-control-source-review.md). Structural HDL
keeps the two conductors distinct.

Guard:

```sh
python3 kicad/check_d99_source_paths.py
```
