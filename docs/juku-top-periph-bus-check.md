# juku_top peripheral bus check

Status: **PASS**

This fast harness drives the LVS-checked `juku_top` buffered CPU bus directly
through `BA`, `DB`, `iord_n`, and `iowr_n`, while leaving the real
top-level chip-select decode and peripheral instances in place. It proves the
post-banner PIC/PPI/FDC path without waiting for ROMBIOS to redraw the screen.

## Command

```sh
sync/juku_top_periph_bus_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Vendored `JUKU1.CPM` loaded by top-level FDC | PASS |
| PIC register write/read through decoded ports `0x00/0x01` | PASS |
| PPI0 Port C motor-on latch through decoded port `0x06` | PASS |
| FDC seek/status/data through decoded ports `0x1C..0x1F` | PASS |
| First byte of `JUKU1.CPM` track 0 sector 2 read through top-level bus is `0xC3` | PASS |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Pass line: `JUKU-TOP-PERIPH-BUS: PASS`

## Boundary

- This is a direct-bus harness, not proof that the full ROMBIOS `TDD` path has
  reached decoded FDC I/O.
- It narrows the remaining M2 blocker: the top-level peripheral decode and
  media-backed FDC path work when reached; the open problem is still getting the
  full CPU run through the slow post-banner path efficiently.
