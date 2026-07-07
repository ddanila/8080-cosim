# juku_top I/O decode probe

Status: **HDL JUKU_TOP FDC PATH NOT YET OBSERVED**

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
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=80000 TRACEPROGRESS=5000 TRACEIO=1 STOPIO=20 MAXVRAM=88000 TIMECAP=900000000 STOPFDC=0 STOPPIC=0 STOPPPI=0 TIMEOUT=60`.

## Evidence

| Check | Result |
| --- | --- |
| vvp/timeout exit code | `0` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | NO |
| VRAM progress trace observed | NO |
| keyboard trace observed | NO |
| raw I/O trace observed | PASS |
| PIC setup trace observed | NO |
| PPI key-read trace observed | NO |
| IRQ trace observed | NO |
| decoded FDC I/O observed | NO |
| keyboard trace lines | `0` |
| VRAM progress trace lines | `0` |
| PIC trace lines | `0` |
| PPI key-read trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `21` |
| FDC trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `none`
- Last VRAM progress line: `none`
- VRAM stop line: `none`
- First keyboard line: `none`
- Last keyboard line: `none`
- First PIC line: `none`
- PIC stop line: `none`
- First PPI key-read line: `none`
- PPI stop line: `none`
- First IRQ line: `none`
- First raw I/O line: `[RAWIO] OUT ba=0x0f0f port=0x0f data=0x9b mcyc=29 vram=0 ios=1 pic=0 ppi0=0 sio0=0 ppi1=1 pit0=0 pit1=0 pit2=0 fdc=0`
- Raw I/O stop line: `[RAWIO] stop ios=20 reads=0 writes=20 mcyc=153 vram=0`
- First FDC line: `none`
- FDC stop line: `none`
- Time-cap line: `none`
- I/O summary line: `[IO] raw_ios=20 raw_reads=0 raw_writes=20 pic_ios=0 pic_reads=0 pic_writes=0 ppi_ios=4 ppi_reads=0 ppi_writes=4 ppi_key_reads=0 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=0 intr_edges=0 inta_edges=0`

## Disposition

- The top-level bench now has opt-in `+ekdoskeys=1`, `+traceio=1`,
  `+stopio=N`, `+tracepic=1`, `+stoppic=N`, `+tracefdc=1`, and
  `+stopfdc=N` hooks.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- `docs/ekdos-timing-reference.md` shows the fast cosim target for this same
  vendored `TDD` path: first PIC/PPI setup around 30,520 VRAM writes, first
  frame IRQ at 33,812 VRAM writes, and first FDC command at 63,085 VRAM writes.
- The remaining M2 target is still the full `juku_top` ROMBIOS `TDD` path to
  an EKDOS `A>` prompt.
