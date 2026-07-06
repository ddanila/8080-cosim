# EKDOS/FDC boot-path probe

Status: **READY FOR FDC MODEL**

This probe exercises the factory boot sequence mined from Baltijets doc 003:
`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` from `JUKU-1` toward the
`A>` EKDOS prompt. The current cosim intentionally has no WD1793 disk
engine or `.juk` image loader yet, so success here means the BIOS reaches
the FDC path and stalls at the known missing model boundary.

## Command

```sh
JUKU_KEYS=TDD cosim/trace roms/ekta37.bin 250000000 0 200000
```

## Summary

- Trace exit code: 0
- Stop PC: FED4
- Cycles: 250000008
- Mode switches: 8795
- WD1793 status/command writes (`0x1C`): 6
- WD1793 status reads (`0x1C`): 8403330
- WD1793 data reads (`0x1F`): 512
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
- The first hard stop is now the expected one: a real WD1793 model plus JUKU/EKDOS disk image loader.
- The exact target remains the factory acceptance result `A>` after `<T>, <D>, <D>`.
