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
- `JUKU_TOP_FDC_KHOLD` default `900000`
- `JUKU_TOP_FDC_KGAP` default `900000`
- `JUKU_TOP_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_FDC_TRACEPROGRESS` default `5000`
- `JUKU_TOP_FDC_TRACEIO` default `0`
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=80000 TRACEPROGRESS=5000 TRACEIO=0 STOPIO=0 MAXVRAM=88000 TIMECAP=900000000 STOPFDC=1 STOPPIC=0 STOPPPI=0 STOPPROMPT=1 STOPPC=none STOPPC_SKIP=0 TIMEOUT=60`.

## Evidence

| Check | Result |
| --- | --- |
| vvp/timeout exit code | `124` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | PASS |
| VRAM progress trace observed | PASS |
| keyboard trace observed | NO |
| raw I/O trace observed | NO |
| PIC setup trace observed | NO |
| PPI key-read trace observed | NO |
| IRQ trace observed | NO |
| decoded FDC I/O observed | NO |
| EKDOS `A>` prompt bitmap observed | NO |
| keyboard trace lines | `0` |
| VRAM progress trace lines | `1` |
| PIC trace lines | `0` |
| PPI key-read trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `0` |
| FDC trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=5000 mcyc=75001`
- VRAM stop line: `none`
- First keyboard line: `none`
- Last keyboard line: `none`
- First PIC line: `none`
- PIC stop line: `none`
- First PPI key-read line: `none`
- PPI stop line: `none`
- First IRQ line: `none`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First FDC line: `none`
- FDC stop line: `none`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `none`
- Visible state line: `none`
- I/O summary line: `none`

## Disposition

- The top-level bench now has opt-in `+ekdoskeys=1`, `+traceio=1`,
  `+stopio=N`, `+tracepic=1`, `+stoppic=N`, `+tracefdc=1`, and
  `+stopfdc=N`, plus `+stopprompt=1` for the EKDOS `A>` bitmap and
  `+stoppc=HEX` / `+stoppc_skip=N` for CPU address stops.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- `docs/ekdos-timing-reference.md` shows the fast cosim target for this same
  vendored `TDD` path: first PIC/PPI setup around 30,520 VRAM writes, first
  frame IRQ at 33,812 VRAM writes, and first FDC command at 63,085 VRAM writes.
- The remaining M2 target is still the full `juku_top` ROMBIOS `TDD` path to
  an EKDOS `A>` prompt.
