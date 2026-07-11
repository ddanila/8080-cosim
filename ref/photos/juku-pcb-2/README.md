# Juku processor-board owner photos

This directory contains 50 owner-supplied photographs of processor module
`7.102.158`. They are retained as routing, placement, connector, socket, and
package-identification evidence.

The first batch contains 22 photographs from 2026-05-19. The second batch
contains 21 higher-coverage photographs from 2026-07-10:

- 12 component-side tiles, photographed left-to-right and then top-to-bottom
  as a 4-row by 3-column sequence (`200354648` through `200455512`);
- 9 solder-side tiles in the same acquisition order as a 3-row by 3-column
  sequence (`200506061` through `200537608`).

The third batch contains 7 component-side photographs from later on
2026-07-10 (`202708344` through `202753536`) with the КР1818ВГ93 temporarily
removed. `PXL_20260710_202708344.jpg` is the close footprint view; the other six
retain wider placement context. “VG93 removed” describes the photographed
maintenance state, not a non-FDC board population.

The solder-side view reverses the component-side left/right coordinate. The
registration manifest preserves that mirror relationship. Reviewed two-sided
paths have promoted five D2 address inputs and three D94-to-D93 FDC controls;
all other seeded observations remain measurement requests.

The JPEGs are Git LFS objects. Run `git lfs pull` after cloning; pointer stubs
do not count as available visual evidence, and `sync/reference_artifact_check.sh`
rejects them.

- `SURVEY.md` is the concise photo-only observation list.
- `BODGE-TRIAGE.md` is the settled cross-source physical-evidence summary. Its
  legacy filename is kept for stable generated-report references.
- `registration.json` and `endpoints.csv` are the machine-checked registration
  inventory and reviewed endpoint table; see `docs/photo-registration.md`.

The July component-side tiles clearly show the КР1818ВГ93 FDC and one populated
eight-chip КР565РУ5 bank, consistent with D84-D91. Empty D60-D83 expansion
positions are not evidence of missing production RAM. Some capacitor positions
are empty and the photographs do not yet establish a complete per-refdes value
map, so capacitor-value fidelity remains open.
