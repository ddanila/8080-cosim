# Invalid result placement

This first READY-class run stored its result at `5000h`, where A12 is high.
Its result-writing pointer was itself corrupted by the D1 increment fault, so
the returned bytes are not probe evidence. The raw transport capture is kept
to preserve the failed setup.

The corrected run stores at low-A12 `4F00h` and is retained in
`../t32-ram-a12-ready-classes-low-result-physical/`.
