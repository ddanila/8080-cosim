# Juku processor-board owner photos

This directory contains 52 owner-supplied photographs of processor module
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

Two supplemental photographs from 2026-07-22 show the X3 connector face
and rear harness. Their identification evidence is recorded in `SURVEY.md`.

The solder-side view reverses the component-side left/right coordinate. The
registration manifest preserves that mirror relationship. Reviewed paths and
continuity results are recorded individually in `endpoints.csv`; use
[photo registration](../../../docs/photo-registration.md) for current dispositions
and the distinction between accepted evidence and measurement requests.

The JPEGs are Git LFS objects. Materialize this directory with
`git lfs pull --include="ref/photos/juku-pcb-2/*.jpg" --exclude=""`; pointer stubs
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

The May overview `PXL_20260519_201900001.jpg` also resolves both populated,
socketed ROM-row devices as windowed ST `M2764AF1` EPROMs. Their windows have
no content-identifying labels, so the photograph proves package/population but
not a firmware version or programmed-drawing identity. The checksum-pinned
comparison in `docs/d15-d16-firmware-lineage.md` keeps that boundary separate
from the archival `JUKUROM0/1` byte identity.

The factory assembly drawing for this module (`ДГШ5.109.009 СБ`) is
photographed in `ref/photos/dgsh5-109-009-sb/`.
