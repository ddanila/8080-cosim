# D14 exact-source boundary

The exact `.009 Э3` sheet-1 serial/control detail photographs
`PXL_20260718_101817644.jpg`, `101820818.MP.jpg`, and
`101824181.MP.jpg` show the D11 USART, D12, D3, and D32 serial gates and
their drawn external lines. A native visual pass over those overlaps and
the sheet overview `101754468.jpg` does not identify a D14 section or a
wire attached to physical D14.2 or D14.7. This is a limit of the archived
source read, not proof that those pins were unconnected on the board.

The factory IC census identifies D14 as К170АП2, and the `.009 СБ`
factory modification detail and owner photos identify its physical
package. The modeled I2/pin2 and O7/pin7 roles follow that package model;
neither remote endpoint is read from an exact `.009 Э3` wire. The owner
photo review in [factory-modification-disposition.md](factory-modification-disposition.md)
rejects the old geometry-only D14 solder seeds. A D11-local cross-face fit
instead identifies actual D14.2 solder near `(2426,1376)`, D14.7 near
`(2288,1376)`, and the fifth auxiliary hole near `(2424,1513)` in
`PXL_20260710_200506061.jpg`; see
`ref/photos/juku-pcb-2/d14-cross-face-contact-fit.json`.
The fifth hole's wide solder strip is matched into overlapping
`PXL_20260710_200509593.jpg`, where it visibly joins registered D29.10.
The exact sheet-1 power table names D29.10 `GND`; owner electrical
continuity across that photo path remains unmeasured.

Keep `D14_I2_BOUNDARY` and `D14_O7_BOUNDARY` as separate unassigned nets.
With power removed, confirm the registered D14.2 and D14.7 same-hole pairs,
meter the fifth hole to D29.10, then trace the two signal pins to measured
remote endpoints. The factory Вид В detail
alone does not supply those nets.
