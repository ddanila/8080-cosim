# EKDOS timing reference

Status: **PASS**

This is the fast cosim timing reference for the factory `TDD` path with
vendored `media/disks/JUKU1.CPM`. It records where ROMBIOS first touches
the PIC/PPI/FDC ports relative to CPU cycles and framebuffer writes, so
`juku_top` diagnostics can target the right post-banner window.

## Command

```sh
sync/ekdos_timing_reference.py
```

## First I/O Accesses

| Direction | Port | First value | Cycle | PC | VRAM writes |
| --- | ---: | ---: | ---: | ---: | ---: |
| OUT | 0x00 | D6 | 3061541 | 02B9 | 30520 |
| OUT | 0x01 | FE | 3061556 | 02BC | 30520 |
| OUT | 0x04 | 27 | 157 | 01B0 | 0 |
| IN | 0x04 | - | 638 | 0227 | 0 |
| IN | 0x05 | - | 3062006 | 1213 | 30520 |
| OUT | 0x06 | 01 | 3064197 | D7EF | 30524 |
| IN | 0x06 | - | 3064176 | D7EA | 30524 |
| OUT | 0x07 | 82 | 123 | 01A8 | 0 |
| OUT | 0x1C | 02 | 6666400 | E5DE | 63085 |
| IN | 0x1C | - | 6666463 | E771 | 63085 |
| IN | 0x1D | - | 8711535 | E63F | 63095 |
| OUT | 0x1E | 02 | 8711507 | E639 | 63095 |
| OUT | 0x1F | 02 | 8711454 | E62D | 63095 |
| IN | 0x1F | - | 8876919 | E5AA | 63095 |

## First Frame IRQs

| # | Cycle | PC | Vector | VRAM writes |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3200001 | 0E21 | FED4 | 33812 |
| 2 | 3400004 | 0E25 | FED4 | 38733 |
| 3 | 3600000 | E2E5 | FED4 | 40633 |

## Disposition

- This report is a reference, not a gate for HDL prompt readiness.
- The HDL top-level probe should not expect PPI/FDC activity before the post-banner window shown above.
