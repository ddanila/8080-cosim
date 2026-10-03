# Photo placement residual audit

Status: **NO REPRODUCIBLE PLACEMENT RESIDUALS**

The endpoint registry contains `14` unique-hole snaps, but only rows whose notes retain an explicit `projected (x,y)` baseline can produce a residual. Current calculable rows: `0`.
No row is electrical evidence and no placement is changed automatically.

Regenerate with `python3 kicad/report_photo_placement_residuals.py`.

| Ref | Pins | dx px | dy px | Offset px | RMS px | Posture | Pin list |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |

`review-translation` requires at least three pins, >=20 px median displacement, and <=12 px RMS scatter. Review both-side source crops before editing KiCad.

Use the [package-local fitting workflow](photo-registration.md#local-package-fitting) for placement review. Missing residual baselines do not establish that the current footprints match the owner board.
