# Photo placement residual audit

Status: **NO REPRODUCIBLE PLACEMENT RESIDUALS**

The endpoint registry contains `14` unique-hole snaps, but only rows whose notes retain an explicit `projected (x,y)` baseline can produce a residual. Current calculable rows: `0`.
These residuals do not establish electrical connectivity, and no placement is changed automatically.

Regenerate with `python3 kicad/report_photo_placement_residuals.py`.

| Ref | Pins | dx px | dy px | Offset px | RMS px | Posture | Pin list |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |

`review-translation` requires at least three endpoint rows, >=20 px median displacement, and <=12 px RMS scatter. The script groups by reference only: it does not deduplicate pins or separate source images. Confirm distinct pins and a common image coordinate frame before interpreting a displacement, then review both-side source crops before editing KiCad.

Use the [package-local fitting workflow](photo-registration.md#local-package-fitting) for placement review. Missing residual baselines do not establish that the current footprints match the owner board.
