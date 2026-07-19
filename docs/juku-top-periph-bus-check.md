# juku_top peripheral bus check

Status: **FAIL**

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
| PIC register write/read through decoded ports `0x00/0x01` | FAIL |
| Frame tick raises `INTR` and INTA returns `CD D4 FE` for vector `0xFED4` | FAIL |
| PPI0 no-key scan reads `0xCF` like the first ROMBIOS keyboard poll | FAIL |
| PPI0 keyboard scan reads shifted `T` as `0x88` through decoded ports `0x04/0x05` | FAIL |
| PPI0 Port C motor-on latch through decoded port `0x06` | FAIL |
| Physical D94 table produces mutually exclusive FDC `/RE` and `/WE` strobes | FAIL |
| Low D101.Q0/A4 steers register 3 from D93 strobes to the pulled-up D94 D0 branch | FAIL |
| Chip-select-qualified diagnostic inversion profile stays one-way on the suppressed-`/RE` branch | FAIL |
| Always-enabled diagnostic inversion profile stays one-way on the suppressed-`/RE` branch | FAIL |
| FDC accepts exact ROMBIOS first command `0x02` as restore and returns track 0 | FAIL |
| FDC completion/status acknowledgement plus D0, persistent D8, READY-transition, and repeated-index Force Interrupt lifecycle | FAIL |
| Forced-low READY rejects Type-II/III immediately with NOT READY/INTRQ while Type-I seek still executes and READY-high status recovers | FAIL |
| Timed Type-I physical-head/update, HLT-gated verify with immediate valid-ID mismatch, and exact 15-idle-index HLD release through decoded ports `0x1C..0x1F` | FAIL |
| Forced TR00 proves live TRACK 0 status plus outward Restore stepping and completion when active-low TR00 asserts | FAIL |
| Forced-low HLT holds Type-III BUSY/DRQ-low and its rising edge starts media access | FAIL |
| One missed read-byte deadline sets LOST DATA and exposes sector 2 byte 1 (`0x5C`) through the top-level bus | FAIL |
| A missing Type-II track/sector ID holds BUSY without DRQ for three revolutions and completes RNF on the fourth | FAIL |
| Type-II `C/S` mismatch holds BUSY without DRQ for four index pulses and completes RNF on the fifth | FAIL |
| E-delayed, index-gated Type-III Read Track reconstructs one MFM revolution through logical DB and both diagnostic profile families | FAIL |
| Type-II multi-read traverses vendored sectors 9/10 and ends at sector 11 with RNF | FAIL |
| ROMBIOS `0xA2` write-sector preloads across the 22-byte ID-to-write-gate interval, streams 512 bytes through D94-decoded port `0x1F`, and reads them back from a writable copy | FAIL |
| Write Sector `a0=1` records an `F8` deleted-data mark and Read Sector reports RECORD TYPE bit 5 through the decoded bus | FAIL |
| Type-II deleted multi-write re-arms the 22-byte preload interval, preserves `F8` marks on sectors 9/10, and ends at sector 11 with RNF | FAIL |
| E-delayed, index-gated Type-III Write Track persists sectors 1-10 and an `F8` mark through logical DB and both diagnostic profile families | FAIL |
| CMA-profile CPU bytes cross the unmapped inversion adjunct for restore, seek, media read, and write/readback | FAIL |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides, read-only)`
- Pass line: `none`
- Writable-copy disk line: `FDC-1793: loaded raw disk <temporary-copy> (2 sides, writable)`
- Writable-copy pass line: `none`
- Qualified-D100 writable pass line: `none`
- Always-enabled-D100 writable pass line: `none`

## Boundary

- This is a direct-bus harness, not the full ROMBIOS `TDD` CPU path.
- The behavioral FDC consumes D94's physical-table strobes. D94 enable,
  A3=active-low `IOWR`, and pulled-high A4 are explicit simulation-only
  functional sources; they preserve, rather than close, the physical probes.
- A separate forced-low A4 check exercises the alternate register-3 D0 branch
  without assigning that physically pulled-up output an unmeasured load.
- Two opt-in builds route the behavioral controller through an unmapped profile adjunct.
  Their CPU-side FDC bytes are complemented like CMA-profile firmware. Both use
  actual D93 `/RE` for direction, not raw `IORD`; this keeps the adjunct one-way when
  D94's low-A4 branch suppresses the controller read strobe. One build qualifies
  `/OE` with FDC chip-select and the other grounds it like D23-D25. These are
  executable firmware diagnostics, not physical D100 or measured copper assignments.
- It remains a fast lower-level guard: the top-level peripheral decode mirrors
  the pinned EKDOS no-key read, shifted-`T` read, PIC vector, motor latch, and
  first FDC restore command when reached. The harness then extends the same path
  to media-backed single/multiple-record and reconstructed whole-track reads,
  plus opt-in temporary-copy single/multiple-record writes and whole-track
  format/readback.
