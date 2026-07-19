# D99 one-shot timing and control map

The exact-revision `ДГШ5.109.009 Э3` sheet-3 detail
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` draws both halves of
D99 (К155АГ3). The target assembly drawing
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg` independently places
the four timing parts.

| D99 endpoint | Exact connection |
| --- | --- |
| 1 `A_N`, 3 `CLR_N` | GND |
| 10 `B2` | its own continuation to sheet 1; remote endpoint unresolved |
| 6 `C2`, 7 `RC2` | polarized C17 `120,0`; RC junction pulled to +5 V by R97 `47к` |
| 14 `C1`, 15 `RC1` | polarized C18 `47,0`; RC junction pulled to +5 V by R103 `47к` |
| 13 `Q` | omitted/unused; the complementary pin 4 output is drawn |

Both capacitor symbols carry polarity marks. The target component view directly
shows axial electrolytics and reads C18 as `47 мкФ / 6.3 V`; the sheet value
closes C17 as `120 мкФ`. Their factory body centres are corrected locally
against D98/D99 and the owner-board view because the folded sheet's global
lower-FDC affine drifts at the right edge. D99 pins 4, 5, 11, and 12 remain remote-route
boundaries; E12 and its selected input path require a separate trace.

The parenthesized/quoted `1` beside this conductor denotes the destination
sheet, not a logic level or a shared net name. D99.10 and the separately joined
D100.9/.11 pair therefore remain distinct sheet-1 boundaries. Structural HDL
keeps both boundaries visible rather than tying either one high.

Guard:

```sh
python3 kicad/check_d99_source_paths.py
```
