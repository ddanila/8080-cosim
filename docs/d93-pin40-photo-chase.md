# D93 pin-40 power-trace chase

Status: **PAD GUARDED / NEAREST P12V ANCHORS RANKED / CONTINUITY REQUIRED**

The physical D93 is the populated КР1818ВГ93. The maintenance close-up
temporarily removes it from its socket and provides the clearest pin-40
registration; this is not evidence that the design omits the controller.

## Registered evidence

- Component observation: `ref/photos/juku-pcb-2/PXL_20260710_202708344.jpg` at `(2206.000, 2201.000)` px.
- Solder observation: `ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg` at `(1559.500, 1479.800)` px.
- Source-PCB D93.40 pad centre: `(243.561, 49.210)` mm on `D93_VDD12_BOUNDARY`.
- The solder joint has no accepted same-layer departure. Component copper
  enters the adjacent clip/cable-obscured region, so no P12V merge is made.

## Guard checks

| Check | Result |
| --- | --- |
| D93 is the physical КР1818ВГ93 | PASS |
| D93 pin 40 has the VDD_12V role | PASS |
| Source model keeps D93.40 off P12V pending continuity | PASS |
| Source model exposes exactly one D93.40 boundary | PASS |
| Source PCB assigns D93.40 to the boundary | PASS |
| Component and solder observations are preserved | PASS |
| Nearest P12V anchors are D14.8 and D32.8 | PASS |

## Ranked continuity anchors

These distances are source-PCB geometry only; they do not prove copper.
They rank convenient already-proved P12V contacts for a meter test.

| Rank | P12V contact | Board centre (mm) | Distance from D93.40 |
| ---: | --- | --- | ---: |
| 1 | `D14.8` | `(215.615, 37.190)` | `30.421 mm` |
| 2 | `D32.8` | `(215.615, 25.690)` | `36.526 mm` |
| 3 | `R66.1` | `(293.800, 131.010)` | `95.996 mm` |
| 4 | `X1.132A` | `(99.750, 6.600)` | `149.991 mm` |
| 5 | `X1.131A` | `(97.250, 6.600)` | `152.389 mm` |
| 6 | `D1.28` | `(39.920, 163.355)` | `233.450 mm` |

The closest modeled +12 V anchors are D14.8 and D32.8, roughly 30.4
and 36.5 mm from D93.40 in the source geometry. They are preferable first
meter probes to the much more distant A60/X8 harness anchor. Confirm against
A60.1 or X8.3 as a second independent reference if practical.

## Closure requirement

With power removed and the ВГ93 removed from its socket, continuity-test
D93.40 against D14.8 and D32.8, then against A60.1 or X8.3. Record both
positive and negative readings. Promote D93.40 to P12V only after direct
continuity or an unobscured, uniquely traceable component-side image.
