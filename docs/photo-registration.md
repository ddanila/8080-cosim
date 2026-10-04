# July 2026 photo registration

The durable source records are:

- `ref/photos/juku-pcb-2/registration.json` — image hashes, acquisition order,
  side/mirror state, dimensions, and global transforms;
- `ref/photos/juku-pcb-2/panorama-board-fiducials.json` — reviewed board
  landmarks;
- `ref/photos/juku-pcb-2/local-package-registration.json` — direct package
  anchors and independent checks;
- `ref/photos/juku-pcb-2/d42-d43-orientation-audit.json` — two owner close-ups
  establish right-facing notches for both fitted К555ИР16 packages; mirrored
  2x7 fields trace their common pin7 strip to marked GND and pin14 strip
  through D58.20 to D26.26/+5 V. The routed copper refresh remains open;
- `ref/photos/juku-pcb-2/d26-d58-plus5-strip-review.json` — native-resolution
  screw-area copper chase connects D26.26/+5 V to D58.20, D43.14 and D42.14;
- `ref/photos/juku-pcb-2/d58-orientation-placement-review.json` — the adjacent
  КР580ИР82 also has a right-facing notch; its same-row photo placement
  conflicts with modeled A56-A58/X9 landing positions;
- `ref/photos/juku-pcb-2/x9-d58-local-row-review.json` — the wider owner
  view puts the X9 cable termination band beneath D26, well right of D58;
  individual A45-A58 solder-hole numbering remains open;
- `ref/photos/juku-pcb-2/x9-fifteen-site-band-review.json` — a full 15-site
  mirrored solder band matches D26 lead pitch. Full site10 reaches an
  intermediate via. A front pin count favors D26.27/DB7 through its likely
  counterpart, but the across-face join and cable membership need meter proof;
  a fourteen-site subtraction remains provisional (see
  `ref/photos/juku-pcb-2/x9-site10-via-review.json`);
- `ref/photos/juku-pcb-2/x9-solder-row-registration.json` — both faces place
  the mixed band below D26; A-number order and exact board coordinates remain
  open;
- `ref/photos/juku-pcb-2/x9-plus5-rail-site-review.json` — full-band sites
  9 and 12 share the registered D26.26 copper traced to marked +5 V. They
  are plausible A53/A54 contacts, with cable membership still open;
- `ref/photos/juku-pcb-2/d59-orientation-audit.json` — two owner close-ups
  establish the right-facing notch of marked КР531ЛН1; a four-corner solder
  fit locates its supply contacts without closing their rail routes. The source
  footprint is corrected and routed copper needs a pin-aware refresh;
- `ref/photos/juku-pcb-2/top-bus-buffer-population-audit.json` — D25/D23/D24
  are marked КР580ВА87 and D29 КР580ВА86; D23/D24/D29 left notches are
  photo-closed, while D25's molded notch is indistinct;
- `ref/photos/juku-pcb-2/d25-ground-strip-orientation-review.json` — common
  lower solder copper with left-notched D23 strongly supports D25's modeled
  left-facing pin sequence; direct rail continuity remains unmeasured;
- `ref/photos/juku-pcb-2/d105-h-registration.json` — native-sheet, `.009`
  placement, and owner-photo closure of X1.107B/-BLOCK/H and R1;
- `ref/photos/juku-pcb-2/endpoints.csv` — original-image endpoint coordinates,
  confidence, reviewer, and disposition.
- `ref/photos/juku-pcb-2/x6-cable-registration.json` — factory wire-table and
  two-angle owner-photo closure of bracket X6 through PCB points A:3/A:4.

Panoramas, overlays, and crop atlases are navigation aids. Electrical evidence
always cites an original JPEG coordinate and a reviewed path.

## Current result

All 28 July grid images are registered into a common 310 x 266 mm
component-side coordinate frame, with the solder side mirrored explicitly. The
endpoint table contains 641 reviewed rows:

| State | Rows | Meaning |
| --- | ---: | --- |
| `accepted` | 39 | reviewed pad/path evidence adopted into the board model or preserved as an explicit test landing |
| `measurement` | 596 | pad/path review is inconclusive; continuity or better local evidence is required |
| `rejected` | 6 | two former D94.5-D93.1 claims and four former R94 endpoint assignments disproved by owner continuity/photo review |

The table's `candidate_net` names the current model net for a registered pad;
on a `measurement` row it does not assert that the owner board follows that
net. All 81 nonblank candidate labels now resolve to their stated pad in
`kicad/juku.board.json`. R102.1 and R108.1, for example, carry the sheet-3
RC net names while their remote owner-board paths remain unproved.

Confidence categories and individual fit methods are recorded in
`ref/photos/juku-pcb-2/endpoints.csv`. Projected regions and hole snaps retain
their evidence limits even when the coordinates match the model.
A hole snap or accurate pad projection is not electrical evidence by itself.

## Reproduce the registration aids

Run from the repository root with the original JPEGs materialized through
[Git LFS](git-lfs-policy.md#local-use). Contact sheets and endpoint overlays
require ImageMagick's `magick` command. Panorama generation and rectification
require OpenCV and NumPy; the crop and detail renderers require Pillow, with
NumPy also used by the cross-registration and layer-handoff renderers.
The `/usr/bin/python3` commands below assume that interpreter has those
packages and KiCad's `pcbnew` module for the board-based tools.

```sh
python3 scripts/photo_registration.py validate
python3 scripts/photo_registration.py solve
python3 scripts/photo_registration.py contact-sheets
python3 scripts/photo_registration.py panoramas
python3 scripts/photo_registration.py rectify
/usr/bin/python3 kicad/render_photo_endpoint_overlay.py
/usr/bin/python3 kicad/report_photo_placement_residuals.py
/usr/bin/python3 kicad/render_endpoint_crop_atlas.py
/usr/bin/python3 kicad/render_d96_d99_cross_registration.py
/usr/bin/python3 kicad/render_d93_clock_isolation.py
/usr/bin/python3 kicad/render_d94_d5_layer_handoff.py
/usr/bin/python3 kicad/check_serial_photo_placement.py
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

`validate` checks the declared image hashes and endpoint records. `solve`
rewrites the transforms in `registration.json`; panorama generation also
writes derived registration metadata. Review those changes before committing.
These commands recompute registration aids, not the electrical observations
recorded in the reviewed JSON files.

## Local package fitting

When global board projection misses a physical pad row, add direct anchors to
`local-package-registration.json` and run:

```sh
/usr/bin/python3 kicad/local_package_registration.py
/usr/bin/python3 kicad/apply_local_package_registration.py REF
```

Similarity fits need at least two anchors; affine fits need exactly three.
Include an independent held-out check for either model. The script checks
errors for declared check anchors but does not reject their absence.
Regenerate the local fit report
before applying it: the application script consumes that report without
recomputing its fit or checking input freshness.

Applying a fit rewrites matching seed observations in `endpoints.csv`, including
coordinates, confidence, and selected review notes. It can also change the
source image for eligible seeds; the default requires fits for both faces,
with `--side component` or `--side solder` available for one face. Review state
and candidate nets are preserved. A separate electrical review must establish
a destination before promoting a `measurement` row.

## Electrical evidence and remaining work

Physical observations, original-image coordinates and discarded interpretations
belong to the reviewed JSON records and `endpoints.csv`, rather than a second
chronological narrative here. Important cross-checks include:

| Boundary | Canonical record |
| --- | --- |
| D2/D4 corrected contact fields and open route ends | [Column/row audit](../ref/photos/juku-pcb-2/d2-d4-column-row-audit.json) |
| D9, DRAM rows and historical capacitor-grid projection | [D9 footprint audit](d9-owner-footprint-photo-audit.md) |
| D11 placement across views | [Cross-view audit](../ref/photos/juku-pcb-2/d11-placement-crossview-audit.json) |
| C84 candidate pairs and rejected timer-pin routes | [Region review](../ref/photos/juku-pcb-2/c84-region-review.json) |
| FDC remote continuations and conflicting layer observations | [Hardware handoff](fdc-hardware-handoff.md) |
| D94 adopted connections, source-closed chip select, and unresolved hidden branch | [Reconstruction constraints](d94-reconstruction-constraints.md) |
| Physical versus source/routed placement | [Placement residuals](photo-placement-residuals.md) |

A good local fit does not establish absolute board registration across regions.
The broad component-grid projection is unsafe as a D9/DRAM coordinate bridge;
its regular historical 4×8 grid identified DRAM contacts, not capacitor holes.
Distinct capacitor landings require their own evidence.

Use `measurement` for an unproved destination, `rejected` for a disproved read,
and `accepted` only with a named reviewer, identified reference/pin and unique
reviewed path or direct continuity. Candidate model nets and hole snaps alone
are not electrical proof. Preserve contradictory faces and hidden-layer gaps;
do not promote a projection because it agrees with the runnable twin.

The broad seed/review queue is complete. Use the generated
[owner measurement shortlist](owner-measurement-shortlist.md) for targeted
continuity or better local evidence, and [PLAN.md](../PLAN.md) for priority.
The [fidelity ledger](board-fidelity-gap-ledger.md) records source-model closure;
[routed refresh](routed-refresh-audit.md) records the separate copper boundary.
