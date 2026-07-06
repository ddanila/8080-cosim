# EKDOS/FDC boot-path probe

Status: **READY FOR EXTERNAL EKDOS IMAGE**

This probe exercises the factory boot sequence mined from Baltijets doc 003:
`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` from `JUKU-1` toward the
`A>` EKDOS prompt. The default no-image run preserves the legacy
register-echo FDC boundary so this guard stays reproducible without
vendoring copyrighted media. Set `EKDOS_PROBE_DISK=/path/to/JUKU-1.juk`
to run the same path through the disk-backed WD1793 model.

## Command

```sh
JUKU_KEYS=TDD cosim/trace roms/ekta37.bin 250000000 0 200000
```

## Summary

- Trace exit code: 0
- External disk image: not selected
- Disk image loaded by cosim: no
- Stop PC: FED4
- Cycles: 250000008
- Mode switches: 8795
- WD1793 status/command writes (`0x1C`): 6
- WD1793 status reads (`0x1C`): 8403330
- WD1793 data reads (`0x1F`): 512
- EKDOS `A>` prompt bitmap: not checked
- Probe failures: 0

## FDC I/O Ports

| Direction | Port | Count | Last write |
| --- | ---: | ---: | --- |
| OUT | 0x1C | 6 | 0x80 |
| OUT | 0x1D | 0 | - |
| OUT | 0x1E | 2 | 0x03 |
| OUT | 0x1F | 2 | 0x00 |
| IN | 0x1C | 8403330 | - |
| IN | 0x1D | 2 | - |
| IN | 0x1E | 0 | - |
| IN | 0x1F | 512 | - |

## Disposition

- The keyboard/frame-interrupt path is sufficient to drive ROMBIOS into the documented disk boot path.
- The no-image run proves the BIOS/FDC boundary and keeps the repo self-testable without shipping EKDOS media.
- A disk-backed run is selected with `EKDOS_PROBE_DISK=/path/to/JUKU-1.juk`; invalid paths or non-`.juk` sizes fail this report explicitly.
- The exact target remains the factory acceptance result `A>` after `<T>, <D>, <D>`.
