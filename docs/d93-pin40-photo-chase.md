# D93 pin-40 power-trace chase

Status: **OWNER CONTINUITY CLOSED / D93.40 ON P12V**

The physical D93 is the populated КР1818ВГ93. The maintenance close-up
temporarily removes it from its socket and provides the clearest pin-40
registration; this is not evidence that the design omits the controller.

## Reproduction

Run from the repository root using Python with KiCad's `pcbnew` module.
The command overwrites this report; it reads the board and text records,
so materialized photograph bytes are not required.

```sh
/usr/bin/python3 kicad/report_d93_pin40_photo_chase.py
```

The guard checks D93 identity/pin role, JSON/source-PCB net assignment,
the two observation IDs, and geometric distances to P12V pads. It does
not check photo hashes, inspect copper continuity, or repeat the owner
measurement. Nearby modeled anchors are optional corroboration targets.

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

## Optional corroboration

The nearest modeled +12 V anchors are D14.8 and D32.8. For an independent
board comparison, meter D93.40 to either anchor and to A60.1 or X8.3.
Their proximity in source-PCB geometry does not establish owner-board copper.

D93.40 is already closed to P12V by owner continuity; these are optional
cross-checks rather than outstanding release probes.
