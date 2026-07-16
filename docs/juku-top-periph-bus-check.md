# juku_top peripheral bus check

Status: **PASS**

This fast harness drives the LVS-checked `juku_top` buffered CPU bus directly
through `BA`, `DB`, `iord_n`, `iowr_n`, and `inta_n`, while leaving the
real top-level chip-select decode and peripheral instances in place. It proves
the post-banner keyboard/PIC/PPI/FDC path without waiting for ROMBIOS to redraw
the screen.

## Command

```sh
sync/juku_top_periph_bus_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Vendored `JUKU1.CPM` loaded by top-level FDC | PASS |
| PIC register write/read through decoded ports `0x00/0x01` | PASS |
| Frame tick raises `INTR` and INTA returns `CD D4 FE` for vector `0xFED4` | PASS |
| PPI0 no-key scan reads `0xCF` like the first ROMBIOS keyboard poll | PASS |
| PPI0 keyboard scan reads shifted `T` as `0x88` through decoded ports `0x04/0x05` | PASS |
| PPI0 Port C motor-on latch through decoded port `0x06` | PASS |
| Physical D94 table produces mutually exclusive FDC `/RE` and `/WE` strobes | PASS |
| FDC accepts exact ROMBIOS first command `0x02` as restore and returns track 0 | PASS |
| FDC seek/status/data through decoded ports `0x1C..0x1F` | PASS |
| First byte of `JUKU1.CPM` track 0 sector 2 read through top-level bus is `0xC3` | PASS |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Pass line: `JUKU-TOP-PERIPH-BUS: PASS`

## Boundary

- This is a direct-bus harness, not the full ROMBIOS `TDD` CPU path.
- The behavioral FDC consumes D94's physical-table strobes. D94 enable,
  A3=active-low `IOWR`, and pulled-high A4 are explicit simulation-only
  functional sources; they preserve, rather than close, the physical probes.
- It remains a fast lower-level guard: the top-level peripheral decode mirrors
  the pinned EKDOS no-key read, shifted-`T` read, PIC vector, motor latch, and
  first FDC restore command when reached. The harness then extends the same path
  to a media-backed sector read.
