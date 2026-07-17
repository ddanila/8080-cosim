# EKDOS/FDC boot-path probe

Status: **EKDOS A> PROMPT REACHED**

This probe exercises the factory boot sequence mined from Baltijets doc 003:
`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` from `JUKU-1` toward the
`A>` EKDOS prompt. By default it uses the vendored `media/disks/JUKU1.CPM`
image, so this guard stays reproducible without network access. Set
`EKDOS_PROBE_DISK=/path/to/image` to run the same path through another
raw Juku disk image, or set `EKDOS_PROBE_DISK=none` for the legacy
no-image boundary.

## Command

```sh
EKDOS_PROBE_DISK=media/disks/JUKU1.CPM JUKU_KEYS=TDD cosim/trace roms/ekta37.bin 250000000 0 200000
```

## Summary

- Trace exit code: 0
- Disk image: media/disks/JUKU1.CPM
- Disk image loaded by cosim: yes
- Stop PC: FED4
- Cycles: 250000015
- Mode switches: 924993
- WD1793 status/command writes (`0x1C`): 27
- WD1793 status reads (`0x1C`): 3860
- WD1793 data reads (`0x1F`): 10752
- EKDOS `A>` prompt bitmap: found at x=0, y=70
- Probe failures: 0

## FDC I/O Ports

| Direction | Port | Count | Last write |
| --- | ---: | ---: | --- |
| OUT | 0x1C | 27 | 0x80 |
| OUT | 0x1D | 0 | - |
| OUT | 0x1E | 22 | 0x06 |
| OUT | 0x1F | 22 | 0x02 |
| IN | 0x1C | 3860 | - |
| IN | 0x1D | 22 | - |
| IN | 0x1E | 0 | - |
| IN | 0x1F | 10752 | - |

## Disposition

- The keyboard/frame-interrupt path is sufficient to drive ROMBIOS into the documented disk boot path.
- The no-image run proves the BIOS/FDC boundary without depending on disk contents.
- A disk-backed run is selected with `EKDOS_PROBE_DISK=/path/to/image`; invalid paths or unsupported raw image sizes fail this report explicitly.
- The exact target remains the factory acceptance result `A>` after `<T>, <D>, <D>`.
