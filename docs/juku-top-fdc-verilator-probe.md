# juku_top FDC Verilator probe

Status: **HDL JUKU_TOP FDC PATH OBSERVED**

This bounded diagnostic runs the LVS-checked `juku_top` with the vendored
Juku disk image, frame interrupts, and the fixed ROMBIOS `TDD` keyboard
sequence enabled. The default simulator is Icarus Verilog, matching the CI
toolchain. Set `JUKU_TOP_FDC_SIM=verilator` for a faster local/deep reset
run through the same testbench and stop hooks.

## Command

```sh
sync/juku_top_fdc_probe.sh
```

Environment overrides:

- `JUKU_TOP_FDC_DISK` default `media/disks/JUKU1.CPM`
- `JUKU_TOP_FDC_SIM` default `icarus`; optional `verilator`
- `JUKU_TOP_FDC_KEYAT` default `42000`
- `JUKU_TOP_FDC_KHOLD` default `900000`
- `JUKU_TOP_FDC_KGAP` default `900000`
- `JUKU_TOP_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_FDC_TRACEPROGRESS` default `5000`
- `JUKU_TOP_FDC_TRACEIO` default `0`
- `JUKU_TOP_FDC_TRACECHK` default `0`
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=200000 TRACEPROGRESS=5000 TRACEIO=0 TRACECHK=0 STOPIO=0 MAXVRAM=40000 TIMECAP=1200000000 STOPFDC=1 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=180`.

## Evidence

| Check | Result |
| --- | --- |
| simulator | `verilator` |
| vvp/timeout exit code | `0` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | PASS |
| VRAM progress trace observed | PASS |
| keyboard trace observed | NO |
| raw I/O trace observed | NO |
| PIC setup trace observed | PASS |
| PPI key-read trace observed | NO |
| IRQ trace observed | PASS |
| decoded FDC I/O observed | YES |
| EKDOS `A>` prompt bitmap observed | NO |
| keyboard trace lines | `0` |
| VRAM progress trace lines | `6` |
| PIC trace lines | `34` |
| PPI key-read trace lines | `0` |
| IRQ trace lines | `40` |
| raw I/O trace lines | `0` |
| FDC trace lines | `2` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 15.487 s (elab=0.020, cvt=0.174, bld=15.245); cpu 0.242 s on 1 threads; alloced 17.348 MB`
- Verilator walltime line: `- Verilator: $finish at 160ms; walltime 12.491 s; speed 12.824 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=30000 mcyc=522138`
- VRAM stop line: `none`
- First keyboard line: `none`
- Last keyboard line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- PIC stop line: `none`
- First PPI key-read line: `none`
- PPI stop line: `none`
- First IRQ line: `[IRQ] intr rise count=1 mcyc=785934 vram=30524`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First checksum line: `none`
- Last checksum line: `none`
- First FDC line: `[FDC] IN  port=0x1c reg=0 data=0x80 mcyc=1012756 ios=1`
- FDC stop line: `[FDC] stop ios=1 reads=1 writes=0 mcyc=1012756`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0xe771 sp=0xd432 instr=0xdb ba=0x1c1c db=0xff mcyc=1012756 vram=30524 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- Visible state line: `[STATE] pc=e771 sp=d432 a=80 b=00 c=d7 d=0d e=47 h=01 l=d9 sf=0 zf=1 hf=1 pf=1 cf=0 iff=1 mode=1 portc=01 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=746 raw_reads=424 raw_writes=322 pic_ios=34 pic_reads=0 pic_writes=34 ppi_ios=630 ppi_reads=403 ppi_writes=227 ppi_key_reads=0 fdc_ios=1 fdc_reads=1 fdc_writes=0 frame_ticks=40 intr_edges=10 inta_edges=30`

## Checksum Trace

```text

```

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
