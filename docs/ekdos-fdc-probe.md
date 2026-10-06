# EKDOS/FDC boot-path probe

Status: **EKDOS A> PROMPT REACHED**

This probe exercises the factory boot sequence documented in Baltijets doc 003.
It uses archive-37 `ekta37.bin` (RomBios 3.43m) to exercise
`*` -> `<T>, <D>, <D>` from `JUKU-1` toward the
`A>` EKDOS prompt. By default it uses the vendored `media/disks/JUKU1.CPM`
image, so this guard stays reproducible without network access. Set
`EKDOS_PROBE_DISK=/path/to/image` to run the same path through another
raw Juku disk image, or set `EKDOS_PROBE_DISK=none` for the legacy
no-image boundary. If the default disk is absent and no override is set,
the script also selects that no-image probe.

## Command

```sh
EKDOS_PROBE_MAX_CYCLES=250000000 EKDOS_PROBE_FRAME_CYCLES=200000 \
  EKDOS_PROBE_DISK=media/disks/JUKU1.CPM sync/ekdos_fdc_probe.py
```

Run this command from the repository root. Disk paths are resolved from
the caller's working directory before starting the trace in `cosim/`.
Python 3 and a C compiler (`CC`, default `cc`) are required; the trace
executable is compiled in a temporary directory for each run.

The probe forces `JUKU_KEYS=TDD` and selects or clears `JUKU_DISK`.
Other `JUKU_*` trace settings are inherited, including keyboard timing,
fault injection and early-stop controls. Unset them for the default
baseline; retain intentional overrides with candidate results.

The run overwrites `cosim/vram.bin` and writes the report even when its
oracle fails. Save any capture you need before running it. The optional
first argument selects the report path (default `docs/ekdos-fdc-probe.md`);
its parent directories are created automatically.

## Summary

- Trace exit code: 0
- Disk image: media/disks/JUKU1.CPM
- Disk image loaded by cosim: yes
- Stop PC: FED4
- Cycles: 250000006
- Mode switches: 924570
- WD1793 status/command writes (`0x1C`): 27
- WD1793 status reads (`0x1C`): 7644
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
| IN | 0x1C | 7644 | - |
| IN | 0x1D | 22 | - |
| IN | 0x1E | 0 | - |
| IN | 0x1F | 10752 | - |

## Disposition

- The keyboard/frame-interrupt path is sufficient to drive ROMBIOS into the documented disk boot path.
- The no-image run checks a command write, at least 1000 status reads, and exactly 512 data reads; it does not check the prompt.
- A disk-backed run is selected with `EKDOS_PROBE_DISK=/path/to/image`; invalid paths or unsupported raw image sizes fail this report explicitly.
- The disk-backed oracle is the `A>` bitmap near the left edge after the cycle budget; it does not exercise subsequent EKDOS commands or physical hardware.
