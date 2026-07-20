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
- Captured I/O events: `106325`
- D93 register accesses: `18489`
- Port-C values at D93 accesses: `0x05, 0x25`
- D95-selected D93 clocks at those accesses: `1 MHz`

| Event | Access | Value | Cycle | PC | VRAM writes |
| --- | --- | ---: | ---: | ---: | ---: |
| PIC ICW1 | OUT 0x00 | 0xD6 | 3061541 | 02B9 | 30520 |
| PIC ICW2 | OUT 0x01 | 0xFE | 3061556 | 02BC | 30520 |
| PIC unmask IR5 | OUT 0x01 | 0xDF | 3064051 | 02D6 | 30524 |
| First keyboard read | IN 0x05 | 0xCF | 3062006 | 1213 | 30520 |
| Shifted T keyboard read | IN 0x05 | 0x88 | 4201870 | 1463 | 42543 |
| FDC motor on | OUT 0x06 | 0x04 | 6668323 | D7EF | 63085 |
| First FDC command | OUT 0x1C | 0x02 | 6666400 | E5DE | 63085 |

## D95 controller-clock selection

Recovered `.009` sheet 3 proves D95 select A1 is D26 Port-C bit 3:
A1=0 selects the 1 MHz D40.11 rail and A1=1 selects the 2 MHz D40.12
rail. Replaying every direct Port-C write, mode-set reset, and BSR command
in this exact ROM trace proves the selected clock at each D93 register
access instead of inferring it from the final latch value.

| First/last access | Direction/port | Value | Cycle | PC | Port C | D93 clock |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| First | OUT 0x1C | 0x02 | 6666400 | E5DE | 0x25 | 1 MHz |
| Last | IN 0x1C | 0x00 | 11007574 | E771 | 0x05 | 1 MHz |

## Boundary

- This is a cosim reference, not an HDL prompt proof.
- `docs/juku-top-periph-bus-check.md` proves the corresponding top-level
  keyboard/PIC/PPI/FDC hardware path works when driven directly.
- Uninterrupted HDL CPU execution now reaches decoded FDC I/O and the EKDOS
  prompt; this reference remains the fast event-sequence oracle for regressions.
