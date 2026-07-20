# D93 controller reset and static-pin map

Status: **OWNER-CLOSED CONNECTIVITY / SOURCE-MODEL CORRECTION PENDING**

The recovered `ДГШ5.109.009 Э3` sheets close three formerly isolated
КР1818ВГ93 pins from primary evidence.

| D93 pin | Sheet and measurement evidence | Measured net |
| ---: | --- | --- |
| 19 `MR_N` | With D93 removed, owner continuity on 2026-07-20 proves D93.19 -> D13.8 and the outer-bus rightmost middle-row contact (top view). D13.9 -> D1.12 `RESET`. | `FDC_RESET_N` |
| 22 `TEST` | Sheet-3 detail draws a local U-shaped conductor directly to pin 33 | `D93_TEST_WF_VFOE` |
| 33 `WF/VFOE` | Same two-endpoint local conductor to pin 22; no third junction is drawn | `D93_TEST_WF_VFOE` |

Primary frames are
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101801729.jpg` for the sheet-1
reset source and `PXL_20260718_101637906.jpg` for the sheet-3 destinations.
The overview independently preserves the same paths.

The measurement resolves the former drawing ambiguity: active-high `RESET`
from D13.6/D1.12 enters the otherwise unaccounted D13 Schmitt section at pin 9;
D13.8 drives D93's active-low master reset. D93.19 also reaches the physical
outer-bus contact at the rightmost position of the middle row when the board is
viewed from the top. The exact X1 contact code is deliberately not assigned:
the provisional footprint orientation currently conflicts with that physical
description and must be reconciled separately.

Model disposition:

The current board JSON, KiCad source, HDL, and `check_d93_static_paths.py` still
encode the superseded direct `RESET -> D93.19` interpretation. They must be
changed as one routed-refresh transaction to
`RESET -> D13.9 -> D13.8 -> FDC_RESET_N -> D93.19`; until then this measured
map, not the generated net name, is authoritative for physical reconstruction.
