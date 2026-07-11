# July 2026 photo registration

The durable source records are:

- `ref/photos/juku-pcb-2/registration.json` — image hashes, acquisition order,
  side/mirror state, dimensions, and global transforms;
- `ref/photos/juku-pcb-2/panorama-board-fiducials.json` — reviewed board
  landmarks;
- `ref/photos/juku-pcb-2/local-package-registration.json` — direct package
  anchors and independent checks;
- `ref/photos/juku-pcb-2/endpoints.csv` — original-image endpoint coordinates,
  confidence, reviewer, and disposition.

Panoramas, overlays, and crop atlases are navigation aids. Electrical evidence
always cites an original JPEG coordinate and a reviewed path.

## Current result

All 28 July grid images are registered into a common 310 x 266 mm
component-side coordinate frame, with the solder side mirrored explicitly. The
endpoint table contains 612 reviewed rows:

| State | Rows | Meaning |
| --- | ---: | --- |
| `accepted` | 22 | two-sided evidence adopted into the board model |
| `measurement` | 590 | pad/path review is inconclusive; continuity or better local evidence is required |

Confidence metadata consists of 135 `local-package-fit`, 432
`registration-only`, and 45 `registration+unique-hole-snap` rows. A hole snap
or accurate pad projection is not electrical evidence by itself.

Accepted paths:

- D2.1/.3/.5/.6/.7 -> D4.1/.3/.5/.6/.7 ->
  `A10/A14/A12/A15/A9`;
- D94.1 -> D93.4 / `FDC_RE_N`;
- D94.2 -> D93.3 / `FDC_CS_N`;
- D94.3 -> D93.2 / `FDC_WE_N`.
- А:17 -> S1.1 / `RES_RC` (dedicated numbered wire landing).
- D98.7 -> А:18 -> S1.2 / `D98_Y3_S1_2`.
- D98.3 -> R94.1 / `D98_Y1_R94` (R94.2 remains unresolved).

The reviewed package fits also corrected the source placement/orientation of
D2, D10, D41, D94, D100, and D98. A D11 solder fit corrects endpoint
coordinates without changing its source placement. At D98.7, the component
fit also identifies the visible white wire-18 lead; the factory wire table
independently closes that off-board path as А:18 to S1:2. A new affine solder
fit corrects a roughly 330 px global-projection displacement and shows that no
PCB copper departs D98.7; both observations are accepted. The tracked routed PCB and Gerber ZIP intentionally remain the
last clean pre-correction snapshot until the whole D94/D100 bus cluster can be
rerouted coherently.

The D93 component fit uses `PXL_20260710_202708344.jpg`, a close-up taken with
the known КР1818ВГ93 removed from its socket, rather than the populated-board
panorama. All 40 socket contacts and the printed pin-40 end are visible there,
giving a direct
pin-row orientation and stronger pad landings for the unresolved reset and
clock endpoints. A reflected fit in `PXL_20260710_200506061.jpg` places the
same pins on the actual solder joints. Their far destinations remain
measurement requests; package registration alone is not continuity evidence.

## Reproduce the registration aids

```sh
python3 scripts/photo_registration.py validate
python3 scripts/photo_registration.py solve
python3 scripts/photo_registration.py contact-sheets
python3 scripts/photo_registration.py panoramas
python3 scripts/photo_registration.py rectify
/usr/bin/python3 kicad/render_photo_endpoint_overlay.py
/usr/bin/python3 kicad/report_photo_placement_residuals.py
/usr/bin/python3 kicad/render_endpoint_crop_atlas.py
```

The panorama stitcher requires every declared source tile to join its
homography graph. `rectify` produces common-coordinate review images and a
held-out error record under `docs/photo-registration/`. To map a panorama point
back to every covering original image:

```sh
python3 scripts/photo_registration.py project --group solder_grid --x 506 --y 338
```

Do not cite a panorama seam or rectified pixel as endpoint provenance; use the
projected original-image coordinate.

## Local package fitting

When global board projection misses a physical pad row, add direct anchors to
`local-package-registration.json` and run:

```sh
/usr/bin/python3 kicad/local_package_registration.py
/usr/bin/python3 kicad/apply_local_package_registration.py REF
```

Each fit needs at least two anchors plus an independent held-out check. Applying
a fit updates coordinates and confidence only; it preserves `measurement`
state until visible copper or continuity establishes a destination.

Current held-out errors are sub-2.2 px for the accepted D2/D4/D94 package-row
fits. Direct component and reflected solder fits now replace D106 projections
that landed left of the vertical К555ИЕ7 package, on its body, or between
solder columns. The independent component pin-4 check is exact and the solder
pin-5 check is 0.021 px at the recorded precision; all D106 signals remain
measurements. Separate component and reflected solder fits now land D28 on the
adjacent К155ЛН3, using its unobscured seven-pad column and coherent solder
rows. The component pin-4 check is exact and the solder pin-5 check is 0.010
px; this prevents D28 from being conflated with D106, while the cable-hidden
component fanout remains a continuity boundary. D93, D100, and D98 also have useful local fits, but their unresolved
signals remain measurements where copper is obscured or leaves the visible
layer. The D11 solder fit holds both unused corners out at 2.375 px and
localizes the factory-reworked area beside pins 4-6; it does not establish the
obscured bridge endpoints. The D98 solder fit holds pin 16 out at 0 px on the
complete affine 2x8 row.

The adjacent D96 КМ555ТМ2 now has a separate component fit with an exact
pin-4 held-out check. Together the D106, D28, and D96 fits guard the physical
row spacing rather than preserving the former overlapping placeholder grid;
none of their functional pins is promoted without complete copper continuity.

## Promotion rule and remaining work

Use `measurement` when a path still needs continuity, `rejected` for a
disproved read, and `accepted` only with a named reviewer, identified refdes/pin,
matching opposite-side evidence, and a unique destination. Only accepted rows
may support a change to `kicad/juku.board.json`.

The automated seed/review queue is complete. Further work should be targeted,
not another broad projection pass:

1. D93 pins 19/24/37/38/39 and D100 pins 9/11.
2. Functional pins of D28, D95-D99, D101, D102, and D106.
3. D94 pin 15 and outputs D3-D7, D30 section B, D105 WAIT handoff, and D41
   timing boundaries.

`docs/owner-measurement-shortlist.md` is the generated pin-level session list;
`PLAN.md` owns release priority.
