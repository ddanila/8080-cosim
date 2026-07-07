# WD1772 / VG93 reverse-engineering reference

This directory vendors the local WD1772 transistor/gate schematic and PLA/PLM
table that were provided as project reference material.

| File | SHA256 | Notes |
| --- | --- | --- |
| `wd1772.pdf` | `d3601f97751b029d7effa493aa5094cd4726759eed0f4f34aa290cdf3305f0ef` | One-page KiCad-generated searchable schematic titled `WD1772`, created 2019-07-13. |
| `wd1772pla.txt` | `687a62103ae5a89a3daf4c1decb8968d730802522fa142e458031545b7a34b10` | ASCII PLA/PLM table with 120 product rows, 19 input columns, and 20 output columns. |

Use these files as reference evidence for the WD1772 / FD1773 / WD1793 /
КР1818ВГ93 controller lineage, especially if the current boot/media FDC shim
needs to be replaced with a fuller controller model.

Do not mechanically translate the schematic or PLA table into HDL without an
explicit implementation decision. The immediate M2 target remains getting the
existing `juku_top` ROMBIOS `TDD` path to the vendored `JUKU1.CPM` EKDOS prompt.
