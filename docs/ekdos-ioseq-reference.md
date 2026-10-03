# EKDOS I/O sequence reference

Status: **PASS**

This guard captures a bounded cosim I/O trace for the vendored
`media/disks/JUKU1.CPM` factory `TDD` path with `JUKU_TRACE_IO=1`.
It checks seven selected events by PC, framebuffer-write count, and value,
requires at least 100 events and one FDC access, and checks modeled
1 MHz clock selection at every captured D93 register access.
It does not assert full-sequence equality, exact event counts, cycle
timestamps, or physical clock timing. Counts and cycles below are observed.

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
| First keyboard read | IN 0x05 | 0xEF | 3062006 | 1213 | 30520 |
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
- [Direct-bus HDL checks](juku-top-periph-bus-check.md) separately test
  the modeled keyboard/PIC/PPI/FDC path.
- [Uninterrupted HDL evidence](juku-top-fdc-verilator-probe.md) records
  the reset-to-prompt path and its toolchain requirements.
