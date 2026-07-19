# D93 HLT and RG source map

The exact-revision `ДГШ5.109.009 Э3` sheet 3 closes the last two anonymous
controller pins. The full-resolution source is
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101637906.jpg`; the factory placement
corroboration is
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg`.

| D93 pin | Sheet-3 disposition | Replica net |
| --- | --- | --- |
| 23 HLT | E11 is drawn in position 2-3, joining HLT to pin 32 READY; E11 post 1 is the alternate `MOTOR EN.` source | `FDC_READY` |
| 25 RG | omitted from the D93 symbol between the explicitly drawn CLK/24 and RCLK/26 paths | `D93_RG_NC` |

The E11 placement legend independently shows its three numbered selector posts
immediately above D93. It establishes the physical option, but the current PCB
model does not invent post geometry from label centres: it implements the
source-selected 2-3 electrical state directly. A future registered drill-centre
measurement may replace that direct strap with an explicit three-pad footprint
without changing connectivity.

RG is not treated as an unread line. The exact sheet explicitly numbers and
routes the adjacent pins while leaving 25 absent from the drawn package; that
is positive unused-pin evidence for this revision.
