# EKDOS I/O sequence reference

Status: **PASS**

This is the full cosim I/O-sequence reference for the vendored
`media/disks/JUKU1.CPM` factory `TDD` path, captured with
`JUKU_TRACE_IO=1`. It pins the exact ROMBIOS keyboard/PIC/PPI/FDC
events that the `juku_top` direct-bus harness mirrors at the current
post-banner boundary.

## Command

```sh
sync/ekdos_ioseq_reference.py
```

## Evidence

- Trace exit code: `0`
- Captured I/O events: `14334`

| Event | Access | Value | Cycle | PC | VRAM writes |
| --- | --- | ---: | ---: | ---: | ---: |
| PIC ICW1 | OUT 0x00 | 0xD6 | 3061541 | 02B9 | 30520 |
| PIC ICW2 | OUT 0x01 | 0xFE | 3061556 | 02BC | 30520 |
| PIC unmask IR5 | OUT 0x01 | 0xDF | 3064051 | 02D6 | 30524 |
| First keyboard read | IN 0x05 | 0xCF | 3062006 | 1213 | 30520 |
| Shifted T keyboard read | IN 0x05 | 0x88 | 4201870 | 1463 | 42543 |
| FDC motor on | OUT 0x06 | 0x04 | 6668323 | D7EF | 63085 |
| First FDC command | OUT 0x1C | 0x02 | 6666400 | E5DE | 63085 |

## Boundary

- This is a cosim reference, not an HDL prompt proof.
- `docs/juku-top-periph-bus-check.md` proves the corresponding top-level
  keyboard/PIC/PPI/FDC hardware path works when driven directly, including the
  no-key `0xCF` poll, shifted-`T` `0x88` poll, PIC vector, motor latch, and
  first FDC restore command `0x02`.
- The remaining HDL M2 target is still full CPU execution to decoded FDC I/O
  and then EKDOS `A>`.
