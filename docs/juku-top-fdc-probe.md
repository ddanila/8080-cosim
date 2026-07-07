# juku_top FDC probe

Status: **HDL JUKU_TOP FDC PROBE TIMED OUT BEFORE FDC I/O**

This bounded diagnostic runs the LVS-checked `juku_top` with the vendored
Juku disk image, frame interrupts, and the fixed ROMBIOS `TDD` keyboard
sequence enabled. The testbench stops on decoded WD1793/VG93 I/O so the
remaining EKDOS prompt path can be chased without relying on a manual long
framebuffer run.

## Command

```sh
sync/juku_top_fdc_probe.sh
```

Environment overrides:

- `JUKU_TOP_FDC_DISK` default `media/disks/JUKU1.CPM`
- `JUKU_TOP_FDC_KEYAT` default `42000`
- `JUKU_TOP_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

## Evidence

| Check | Result |
| --- | --- |
| vvp/timeout exit code | `124` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | PASS |
| decoded FDC I/O observed | NO |
| FDC trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- First FDC line: `none`
- FDC stop line: `none`
- Time-cap line: `none`

## Disposition

- The top-level bench now has opt-in `+ekdoskeys=1`, `+tracefdc=1`, and
  `+stopfdc=N` hooks.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- The remaining M2 target is still the full `juku_top` ROMBIOS `TDD` path to
  an EKDOS `A>` prompt.
