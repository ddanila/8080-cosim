# July 2026 photo registration

The source-of-truth inventory is
`ref/photos/juku-pcb-2/registration.json`; electrical observations are recorded
in `ref/photos/juku-pcb-2/endpoints.csv`. The manifest fixes acquisition order,
side/mirror state, dimensions, and SHA256 before any trace interpretation.

Run:

```sh
python3 scripts/photo_registration.py validate
python3 scripts/photo_registration.py solve
python3 scripts/photo_registration.py contact-sheets
```

The overlapping component and solder grids can also be feature-stitched into
single navigation surfaces with OpenCV installed in the active environment:

```sh
python3 scripts/photo_registration.py panoramas
```

This writes `component_grid-panorama.jpg` and `solder_grid-panorama.jpg` beside
the contact sheets, plus `panorama-registration.json` with each original
image-to-panorama homography. The grid-aware matcher requires every declared source tile
to join the homography graph; unlike a generic panorama stitcher, it fails
rather than silently dropping a peripheral tile. Panoramas are still lossy
navigation aids: seams and exposure blending mean that endpoint evidence must
be projected back through the recorded homography and cite an original JPEG
coordinate.

To project a panorama review point back into every original image that covers
it, run:

```sh
python3 scripts/photo_registration.py project --group solder_grid --x 506 --y 338
```

The output is CSV-shaped `image,x_px,y_px` data suitable for locating the
full-resolution crop and then recording the observation in `endpoints.csv`.

The manually reviewed board corners and independent D94-centre checks live in
`ref/photos/juku-pcb-2/panorama-board-fiducials.json`. Generate common 5 px/mm,
component-side-coordinate views with:

```sh
python3 scripts/photo_registration.py rectify
```

The solder view is mirrored during this transformation, so both rectified
images share the same 310 × 266 mm coordinate frame. The derived held-out
errors are recorded in `docs/photo-registration/board-registration.json`.
These transforms are suitable for overlays and navigation, not by themselves
for electrical promotion.

Overlay the current ERC endpoint inventory on both rectified photographs with:

```sh
/usr/bin/python3 kicad/render_photo_endpoint_overlay.py
```

Red circles mark unresolved pads and carry their pin numbers; white labels mark
refdes centres. The generated component/solder overlay JPEGs are alignment and
trace-review aids. A pad circle landing on the photograph does not prove its
net without following the original-resolution copper to another identified
endpoint.

Seed the two-sided review queue from those registered pad locations with:

```sh
/usr/bin/python3 kicad/seed_photo_endpoints.py
```

This writes one component-side and one solder-side `candidate` row for every
unresolved pad. Each row points into the best-covered original JPEG and is
marked `registration-only`; a reviewer must follow its copper before changing
the state or using it as netlist evidence.

With OpenCV available, refine only geometrically unique solder-side candidates:

```sh
python3 kicad/snap_solder_endpoint_candidates.py
```

The snap pass requires a circular-hole candidate within 30 source pixels and
at least 10 pixels of separation from the next candidate. It retains the
projected coordinate in the note and still leaves the row in `candidate`
state; circular appearance alone is not electrical evidence.

Summarize coherent multi-pin placement residuals with:

```sh
/usr/bin/python3 kicad/report_photo_placement_residuals.py
```

The report flags only translation-shaped candidate groups. High-scatter groups
remain ambiguous, and no placement is changed automatically.

Render review atlases directly from those original-image coordinates with:

```sh
/usr/bin/python3 kicad/render_endpoint_crop_atlas.py
```

The outputs under `docs/photo-registration/crops/` are grouped by priority,
side, and refdes. Every tile names its original JPEG and coordinate and marks
the projected pad centre in red. They are navigation aids; reviewers should
still zoom the cited source when a trace leaves the crop or crosses a seam.

For packages whose global board projection misses the photographed pad rows,
record direct original-photo anchors in
`ref/photos/juku-pcb-2/local-package-registration.json` and run:

```sh
/usr/bin/python3 kicad/local_package_registration.py
/usr/bin/python3 kicad/apply_local_package_registration.py D94
```

The fitter supports ordinary component-side and reflected solder-side
similarities, requires at least two fit anchors, checks independent anchors,
and renders every package pad under
`docs/photo-registration/local-packages/`. Applying a validated two-sided fit
updates only image coordinates and confidence; it preserves `measurement`
state and explicitly records that pad identity is not connectivity. D94 is the
first complete local fit: the enlarged notch-left socket view establishes pin
1 at the bottom-left contact, with component pin 4 held out at 0.01 px and
solder pin 5 at 0.32 px. Its 18 reviewed observations are marked
`local-package-fit`. D2 is the second complete
fit: its component pin-4 check is 0.43 px and its reflected solder pin-4 check
is 1.86 px. This corrects all ten unresolved D2 observation coordinates to the
physical vertical socket while leaving their copper destinations unaccepted.
That posture is now applied to both the authoritative PCB generator and source
PCB: D2 pin 1 is above pin 8 on the left package row. An extended solder-side
crop follows each unresolved input along a separate trace to a remote
populated-row landing; destination package pin identities still require local
registration before electrical promotion. The routed snapshot remains at its
pre-correction geometry until those nets can be rerouted together.
An independent reflected D4 solder-row fit uses pins 1/10 and holds out pin 5
at 2.14 px. It lands across the full package row and proves that D2
pins 1/3/5/6/7 route to D4 pins 1/3/5/6/7 (`A10/A14/A12/A15/A9`), so the ten
paired D2 observations are now accepted.
The same workflow locally fits the D93 component-side top-left row. Together
with continuous visible copper, this accepts the matching component/solder
observation pairs for D94.1->D93.4 (`FDC_RE_N`), D94.2->D93.3 (`FDC_CS_N`),
and D94.3->D93.2 (`FDC_WE_N`). No visible branch joins those local nets to the
formerly assumed global I/O rails. Together with the D2 pairs, the current
table contains 16 accepted rows; the remaining 480 observations stay
measurements.

The D93 similarity is valid along the full straight package row, so D93.19 and
D93.24 now use its original-image coordinates rather than their coarse
overlapping-tile projections. An exact lower-left crop separates D93.19's
upper fanout via from D94.4's lower terminal via; their visual proximity is not
a junction and neither net is promoted.

The first overlay audit found that the prior replica placed D94 vertically and
D100 through the wrong physical region. D94 is the horizontal, notch-left blue
socket; the horizontal package immediately to its right is the marked D100,
followed by the marked D98 `К155ЛП11`. A corrected package-local fit reads the
actual horizontal `КР580ВА87`
marking immediately right of D94; the earlier global D100 projections landed
on unrelated CPU/PPI-area packages. The fit holds out pin 5 at 0.22 px and
places D100.9/OE and D100.11/T exactly. The generator/source PCB now use pin 1
`(257.65,37.40)` and the photographed notch-left posture.
An independent D98 component fit uses visible pins 2/7 and holds out pin 5 at
0.20 px. It projects the wire-obscured outer contacts, updates all 14 D98
component observations without electrical promotion, and moves source D98 pin
1 to `(290.00,37.40)` with pin 8 safely inside the board edge.
These corrected placements are now encoded in
`kicad/gen_kicad_pcb.py`; the released routed snapshot remains unchanged
until the surrounding bus traces can be removed and rerouted without DRC
regression.

`kicad/ripup_d94_d100_cluster.py` now produces that local rip-up fixture while
preserving the verified board outside the top-right cluster. A bounded
Freerouting trial exposed 29 KiCad ratsnest edges after correction but did not
finish within 180 seconds; no session was imported. The generic `gap` mode in
`kicad/repair_fdc_route_gaps.py` successfully closes short single-layer gaps,
but the surviving BA13/BA14 bus paths require a deliberate multi-layer escape.
Consequently the tracked routed board and manufacturing ZIP remain the last
clean snapshot, not a partially routed placement experiment.

For each source, add four spread-out manual fiducials with `use: fit` and at
least one independent landmark with `use: check`. Each object contains
`image_px: [x,y]`, `board_mm: [x,y]`, `landmark`, and `use`. The `solve`
command calculates the board-to-image 3x3 homography and maximum held-out pixel
error; do not hand-edit those derived fields. Solder images remain mirrored to
the component-side X axis as declared by their group.

Endpoint rows retain the original image coordinate even after registration.
Use `candidate` for a visible but unreviewed landing, `measurement` when a
continuity reading is still needed, and `rejected` for a disproved read. Only
`accepted` records with a named reviewer, refdes, and pin may support a change
to `kicad/juku.board.json`; acceptance still requires the matching opposite-side
landing/path specified in `PLAN.md`.

The generated contact sheets under `docs/photo-registration/` are navigation
aids, not endpoint provenance. Always cite the original JPEG and pixel
coordinate in the CSV.
