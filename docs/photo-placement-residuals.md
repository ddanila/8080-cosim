# Photo placement residual audit

Status: **NO REPRODUCIBLE PLACEMENT RESIDUALS**

The endpoint registry contains `14` unique-hole snaps, but only rows whose notes retain an explicit `projected (x,y)` baseline can produce a residual. Current calculable rows: `0`.
These residuals do not establish electrical connectivity, and no placement is changed automatically.

Run from the repository root with Python 3 (standard library only):

```sh
python3 kicad/report_photo_placement_residuals.py
```

The writer reads `ref/photos/juku-pcb-2/endpoints.csv` and overwrites this
report and [the residual CSV](photo-placement-residuals.csv). It does not
change endpoints or PCB files.

`review-translation` requires at least three endpoint rows, >=20 px median displacement, and <=12 px RMS scatter. The script groups by reference only: it does not deduplicate pins or separate source images. Confirm distinct pins and a common image coordinate frame before interpreting a displacement, then review both-side source crops before editing KiCad.

Use the [package-local fitting workflow](photo-registration.md#local-package-fitting) for placement review. Missing residual baselines do not establish that the current footprints match the owner board.
