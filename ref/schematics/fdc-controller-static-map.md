# D93 controller reset and static-pin map

Status: **RESET OWNER-CLOSED / STATIC RAIL CONNECTION MISSING FROM MODEL**

The recovered `ДГШ5.109.009 Э3` sheets and owner continuity provide
the following КР1818ВГ93 evidence. The static-pin rail connection differs
from the current model.

| D93 pin | Sheet and measurement evidence | Model net |
| ---: | --- | --- |
| 19 `MR_N` | With D93 removed, owner continuity on 2026-07-20 proves D93.19 -> D13.8 and the outer-bus rightmost middle-row contact (top view). D13.9 -> D1.12 `RESET`. | `FDC_RESET_N` |
| 22 `TEST` | Sheet-3 detail joins pin 33 and rail A, shared with the R87–R89 pull-ups | `D93_TEST_WF_VFOE` |
| 33 `WF/VFOE` | Same junction to pin 22 and rail A | `D93_TEST_WF_VFOE` |

Primary frames are
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101801729.jpg` for the sheet-1
reset source and `PXL_20260718_101637906.jpg` for the sheet-3 destinations.
The overview independently preserves the same paths.

The native sheet-3 detail shows the pin-22/pin-33 junction on the horizontal
rail feeding R87–R89, labeled A (+5 V). The canonical JSON instead assigns
only D93.22 and D93.33 to `D93_TEST_WF_VFOE`; its source annotation incorrectly
claims that no other junction is drawn. The HDL likewise connects those pins
to a separate wire. The guard below preserves that model and cannot detect
the omitted rail connection. Reconcile the JSON, HDL and PCB representation
with this source evidence before claiming static-pin alignment; confirm the
installed board by continuity before claiming physical closure.

Owner continuity places active-high `RESET` from D13.6/D1.12 at
D13 Schmitt input pin 9;
D13.8 drives D93's active-low master reset. D93.19 also reaches the physical
outer-bus contact at the rightmost position of the middle row when the board is
viewed from the top. The exact X1 contact code is deliberately not assigned:
the provisional footprint orientation currently conflicts with that physical
description and must be reconciled separately.

## Model guard

Run from the repository root with Python 3 (standard library only):

```sh
python3 kicad/check_d93_static_paths.py
```

The guard checks canonical JSON endpoints and structural HDL markers for
`RESET -> D13.9 -> D13.8 -> FDC_RESET_N -> D93.19` and the pin-22/pin-33 tie.
It does not compile or simulate HDL, check routed copper, measure reset
timing, or establish physical
continuity of the static tie. Current routing holds are recorded in
[factory-wire fidelity](../../docs/factory-wire-route-fidelity.md).
