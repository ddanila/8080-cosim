# juku_top peripheral bus check

Status: **PASS**

This fast harness drives the `juku_top` buffered CPU bus directly
through `BA`, `DB`, `iord_n`, `iowr_n`, and `inta_n`; FDC writes
additionally exercise raw `iowr_raw_n` plus CPU `wr_n`, while leaving the
top-level chip-select decode and peripheral instances in place. It checks
keyboard/PIC/PPI/FDC bus transactions without running ROMBIOS to its banner
or command prompt. LVS is a separate guard; this script does not run it.

## Command

```sh
sync/juku_top_periph_bus_check.sh
```

Requires Bash and Icarus Verilog (`iverilog` and `vvp`). Builds, logs
and writable disk copies are temporary and removed on exit. The report path
is selected by `JUKU_TOP_PERIPH_BUS_REPORT`; its parent must already exist.

## Evidence

| Check | Result |
| --- | --- |
| Vendored `JUKU1.CPM` loaded by top-level FDC | PASS |
| PIC register write/read through decoded ports `0x00/0x01` | PASS |
| Frame tick raises `INTR` and INTA returns `CD D4 FE` for vector `0xFED4` | PASS |
| PPI0 no-key scan reads `0xCF` for the ordinary idle keyboard profile | PASS |
| PPI0 keyboard scan reads shifted `T` as `0x88` through decoded ports `0x04/0x05` | PASS |
| PPI0 Port C motor-on latch through decoded port `0x06` | PASS |
| Physical D94 table produces mutually exclusive FDC `/RE` and `/WE` strobes | PASS |
| Low D101.Q0/A4 steers register 3 from D93 strobes to the pulled-up D94 D0 branch | PASS |
| Chip-select-qualified diagnostic inversion profile stays one-way on the suppressed-`/RE` branch | PASS |
| Always-enabled diagnostic inversion profile stays one-way on the suppressed-`/RE` branch | PASS |
| FDC accepts exact ROMBIOS first command `0x02` as restore and returns track 0 | PASS |
| FDC completion/status acknowledgement plus D0, persistent D8, READY-transition, and repeated-index Force Interrupt lifecycle | PASS |
| Forced-low READY rejects Type-II/III immediately with NOT READY/INTRQ while Type-I seek still executes and READY-high status recovers | PASS |
| Timed Type-I physical-head/update, HLT-gated verify with immediate valid-ID mismatch, and exact 15-idle-index HLD release through decoded ports `0x1C..0x1F` | PASS |
| Forced TR00 proves live TRACK 0 status plus outward Restore stepping and completion when active-low TR00 asserts | PASS |
| Forced-low HLT holds Type-III BUSY/DRQ-low and its rising edge starts media access | PASS |
| One missed read-byte deadline sets LOST DATA and exposes sector 2 byte 1 (`0x5C`) through the top-level bus | PASS |
| A missing Type-II track/sector ID holds BUSY without DRQ for three revolutions and completes RNF on the fourth | PASS |
| Type-II `C/S` mismatch holds BUSY without DRQ for four index pulses and completes RNF on the fifth | PASS |
| E-delayed, index-gated Type-III Read Track drains 6,250 bytes and checks selected gap, sync, ID, CRC and data bytes in all three bus profiles | PASS |
| Type-II multi-read traverses vendored sectors 9/10 and ends at sector 11 with RNF | PASS |
| ROMBIOS `0xA2` write-sector preloads across the 22-byte ID-to-write-gate interval, streams 512 bytes through D94-decoded port `0x1F`, and reads them back from a writable copy | PASS |
| Write Sector `a0=1` records an `F8` deleted-data mark and Read Sector reports RECORD TYPE bit 5 through the decoded bus | PASS |
| Type-II deleted multi-write re-arms the 22-byte preload interval, preserves `F8` marks on sectors 9/10, and ends at sector 11 with RNF | PASS |
| E-delayed, index-gated Type-III Write Track sends sectors 1-10, verifies all data bytes in sectors 1/10 and checks sector 4 for an `F8` mark in all three bus profiles | PASS |
| CMA-profile CPU bytes cross the unmapped inversion adjunct for restore, seek, media read, and write/readback | PASS |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides, read-only)`
- Pass line: `JUKU-TOP-PERIPH-BUS: PASS`
- Writable-copy disk line: `FDC-1793: loaded raw disk <temporary-copy> (2 sides, writable)`
- Writable-copy pass line: `JUKU-TOP-PERIPH-BUS: PASS`
- Qualified-D100 writable pass line: `JUKU-TOP-PERIPH-BUS: PASS`
- Always-enabled-D100 writable pass line: `JUKU-TOP-PERIPH-BUS: PASS`

## Boundary

- This is a direct-bus harness, not the full ROMBIOS `TDD` CPU path.
- The behavioral FDC consumes D94's physical-table strobes. A3 is physically
  closed to D105.3 qualified peripheral `/WR`; FDC write cycles drive raw
  `/IOWR` plus CPU `/WR` and check D105 derives that rail. D94 enable is source-closed
  to D9.7/CS7 at D94.15/D93.3. Runnable A4 is held high instead of
  implementing the D101 precompensation chain; D94.14/D101.7 is the measured
  boundary. See [D94 constraints](d94-reconstruction-constraints.md).
- A separate forced-low A4 check exercises the alternate register-3 D0 branch;
  D0 has only the measured R8 2 kΩ pull-up in the observed hardware scope.
- The script runs logical DB and two diagnostic builds, each with read-only media
  and a writable temporary copy. The diagnostic builds route the behavioral
  controller through an unmapped profile adjunct.
  Their CPU-side FDC bytes are complemented like CMA-profile firmware. Both use
  actual D93 `/RE` for direction, not raw `IORD`; this keeps the adjunct one-way when
  D94's low-A4 branch suppresses the controller read strobe. One build qualifies
  `/OE` with FDC chip-select and the other grounds it like D23-D25. These are
  bus-profile diagnostics; they do not establish physical D100 wiring or copper assignments.
