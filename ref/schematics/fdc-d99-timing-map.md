# D99 one-shot timing and control map

The exact-revision `ДГШ5.109.009 Э3` sheet-3 detail
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` draws both halves of
D99 (К155АГ3). The target assembly drawing
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` independently places
the four timing parts.

| D99 endpoint | Exact connection |
| --- | --- |
| 1 `A_N`, 3 `CLR_N` | GND |
| 9 `A2_N` | owner continuity joins D94.2/D1 and R89.1; R89.2 reaches +5 V. The drawing extends this island to D96.11 CLK2, whose board continuity remains pending |
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

The registered photos locate D99.4 but show no visible local B.Cu departure.
The upward trace on the neighboring joint must not be assigned to D99.4.
Cable and package obscure the component-side route, so photographs neither
confirm nor refute its remote continuity. Keep D99.4 separate from the
owner-proved D94.14/D101.7 island. Registered probe coordinates and the
power-off continuity check are in
[the D99 route review](../../docs/d99-q1n-a4-conflict-photo-review.md).

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

## Model guard

Run from the repository root with Python 3 (standard library only):

```sh
python3 kicad/check_d99_source_paths.py
```

The guard checks selected board-JSON nets, timing-part values, retired boundary
names, placement-registration target names and literal D99/D100 HDL markers.
It does not verify source-photo hashes, placement geometry, routed copper,
physical continuity or one-shot timing. The unresolved remote clear source
and E12 population still require the evidence described above.
