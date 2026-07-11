# Photo placement residual audit

Status: **NO REPRODUCIBLE PLACEMENT RESIDUALS**

The endpoint registry contains `45` unique-hole snaps, but only rows whose notes retain an explicit `projected (x,y)` baseline can produce a residual. Current calculable rows: `0`.
No row is electrical evidence and no placement is changed automatically.

| Ref | Pins | dx px | dy px | Offset px | RMS px | Posture | Pin list |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |

`review-translation` requires at least three pins, >=20 px median displacement, and <=12 px RMS scatter. Review both-side source crops before editing KiCad.

The former residual table is intentionally retired: its endpoint notes no longer preserve the projection origins needed to reproduce those offsets. Use validated package-local fits instead of the stale global-placement deltas.
