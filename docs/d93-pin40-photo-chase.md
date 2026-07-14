# D93 pin-40 power-trace chase

Status: **OWNER CONTINUITY CLOSED / D93.40 ON P12V**

The physical D93 is the populated КР1818ВГ93. The maintenance close-up
temporarily removes it from its socket and provides the clearest pin-40
registration; this is not evidence that the design omits the controller.

## Registered evidence

- Component observation: `ref/photos/juku-pcb-2/PXL_20260710_202708344.jpg` at `(2206.000, 2201.000)` px.
- Solder observation: `ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg` at `(1559.500, 1479.800)` px.
- Source-PCB D93.40 pad centre: `(243.561, 49.210)` mm on `P12V`.
- The photographs register the pad but do not prove its far copper.
- Direct owner continuity on 2026-07-15 proves the P12V merge.

## Guard checks

| Check | Result |
| --- | --- |
| D93 is the physical КР1818ВГ93 | PASS |
| D93 pin 40 has the VDD_12V role | PASS |
| Source model assigns D93.40 to P12V | PASS |
| Source PCB assigns D93.40 to P12V | PASS |
| Component and solder observations are preserved | PASS |
| Nearest P12V anchors are D14.8 and D32.8 | PASS |

## Ranked continuity anchors

These distances are retained as source-PCB geometry and useful independent
cross-check points; the electrical closure comes from the owner measurement.

| Rank | P12V contact | Board centre (mm) | Distance from D93.40 |
| ---: | --- | --- | ---: |
| 1 | `D14.8` | `(215.615, 37.190)` | `30.421 mm` |
| 2 | `D32.8` | `(215.615, 25.690)` | `36.526 mm` |
| 3 | `R66.1` | `(302.690, 132.270)` | `101.957 mm` |
| 4 | `X1.132A` | `(99.750, 6.600)` | `149.991 mm` |
| 5 | `X1.131A` | `(97.250, 6.600)` | `152.389 mm` |
| 6 | `D1.28` | `(39.920, 163.355)` | `233.450 mm` |

The closest modeled +12 V anchors are D14.8 and D32.8, roughly 30.4
and 36.5 mm from D93.40 in the source geometry. They are preferable first
meter probes to the much more distant A60/X8 harness anchor. Confirm against
A60.1 or X8.3 as a second independent reference if practical.

## Closure

D93.40 is promoted to P12V from direct owner continuity. No further
power-safety probe is required unless an independent board comparison is desired.
