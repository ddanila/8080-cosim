# 2026-07-18 factory-drawing legibility audit

Status: **COMPLETE / NO RE-SHOOT REQUIRED FOR THE RECORDED SCOPE**

This audit walks every drawing in the owner-photo batch against its overview
and overlapping detail frames.  “Usable” means every circuit/table region is
covered by at least one native-resolution frame closely enough to support the
reviewed extraction; it does not claim that overview frames alone are readable.

| drawing | region audited | closest usable frame(s) | disposition |
| --- | --- | --- | --- |
| `ДГШ5.109.009 Э3`, sheet 1 | CPU, decode, PPI/PIC/USART, connectors and continuations | `_101801729` through `_101827714` (8 overlapping tiles) | Usable. D6, D26, D93 host-bus continuations and sheet boundaries have already survived independent crop/read passes. |
| `ДГШ5.109.009 Э3`, sheet 2 | DRAM, video and timing; faint overview/fold regions | `_101908284` through `_101932581` (8 overlapping tiles) | Usable from tiles. The overview `_101901243` is too faint for pin-level reading but is needed only for layout; tile overlap covers the circuit and fold. |
| `ДГШ5.109.009 Э3`, sheet 3 | complete VG93 controller, separator, precompensation, X4 and title/power table | `_101637906`, `_101641055`, `_101644861`, `_101648508` | Usable. All four tiles have been read in native color and enhanced crops; the resulting D93/D95/D96/D99/D100/D106 maps are guarded separately. |
| `ДГШ3.065.008 Э3` | both ЕС5323 mechanisms, X1/X2, XS3/XS4/XS5, power-block boundary | `_121826539` through `_121851825` (8 overlapping tiles) | Usable. Full hierarchical signal and power fanout is transcribed in `ref/schematics/fdc-x4-ngmd-wire-map.md`. The drawing intentionally treats the PSU as a block, so there is no hidden component-level PSU region to re-shoot. |
| `ДГШ3.031.011 Э6` | complete A1–A5 system/cable block map | `_121246801`, `_121250335` | Usable. The two tiles overlap and close every X1–X6 route shown; this is a general schematic, not a contact-level circuit drawing. |
| `ДГШ5.106.103 Э3` | memory-card logic and complete XP edge table | `_122448921`, `_122451372.MP`, `_122454044`, `_122456943` | Usable for the scoped XP/system-bus extraction. The exact signal core and the A1–A3 power conflict are checksum-guarded. No unresolved XP contact depends on the overview. |
| `ДГШ5.104.015 Э3` | all 15 scan columns, six encoder rows, modifiers, diode/decoder logic and X1 | `_122210592`, `_122213927` | Usable. Overlap covers the center seam; all 70 fitted positions and every shown X1 contact are transcribed and photo-hash guarded. |
| `ДГШ5.106.106 Д1`, sheets 1–3 | printed bytes `0000–07FF`, headings and row addresses | `sheet1_...122548761`, `sheet2_...122557171`, `sheet3_...122601894` | Usable. The only archive/image disagreement, byte `021A`, is visibly resolved as `21`; all other bytes match independent binary evidence. |

## Re-shoot shortlist

None for the planned extraction scope.  A flatter, higher-contrast sheet-2
overview would be cosmetically better, but it would not close a current
electrical boundary: the eight detail tiles already cover that sheet.  Any
future re-shoot request should therefore name a newly discovered ambiguous
pin or continuation rather than repeat the whole batch.

Original photos remain the evidence.  Enhanced/rotated crops are disposable
reading aids and are not substituted for or committed beside them.
