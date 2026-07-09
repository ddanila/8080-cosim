# juku_top Verilator FDC prompt probe

Status: **HDL JUKU_TOP EKDOS PROMPT REACHED**

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
- `JUKU_TOP_FDC_FRAMEPHASE` default `0`
- `JUKU_TOP_FDC_FRAMEMCYC` default `0`; when nonzero, overrides
  `JUKU_TOP_FDC_FRAMEIRQ` and schedules frame ticks on machine-cycle boundaries;
  in this mode `JUKU_TOP_FDC_FRAMEPHASE` is the absolute first machine-cycle tick
- `JUKU_TOP_FDC_TRACEPROGRESS` default `5000`
- `JUKU_TOP_FDC_VRAMSTOP_SYNC` default `0`; when nonzero, stops at the next
  CPU SYNC after `JUKU_TOP_FDC_MAXVRAM` for architectural state comparison
- `JUKU_TOP_FDC_TRACEIO` default `0`
- `JUKU_TOP_FDC_TRACECHK` default `0`
- `JUKU_TOP_FDC_TRACEPPI` default `1`
- `JUKU_TOP_FDC_TRACEIRQ` default `1`
- `JUKU_TOP_FDC_TRACEFDC` default `1`
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPFDCDATA` default `0`; when nonzero, stops after N
  decoded FDC data-register reads
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=10000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=0 TRACEFDC=0 STOPIO=0 MAXVRAM=100000 TIMECAP=12000000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=1 STOPPC=none STOPPC_SKIP=0 TIMEOUT=420`.

## Evidence

| Check | Result |
| --- | --- |
| simulator | `verilator` |
| vvp/timeout exit code | `0` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | PASS |
| VRAM progress trace observed | PASS |
| keyboard trace observed | PASS |
| raw I/O trace observed | NO |
| PIC setup trace observed | PASS |
| PPI key-read trace observed | NO |
| IRQ trace observed | NO |
| decoded FDC I/O observed | YES |
| EKDOS `A>` prompt bitmap observed | YES |
| keyboard trace lines | `6` |
| VRAM progress trace lines | `7` |
| PIC trace lines | `190` |
| PPI key-read trace lines | `0` |
| PPI trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `0` |
| FDC trace lines | `0` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 20.945 s (elab=0.023, cvt=0.186, bld=20.685); cpu 0.261 s on 1 threads; alloced 17.598 MB`
- Verilator walltime line: `- Verilator: $finish at 413ms; walltime 37.755 s; speed 10.929 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=70000 mcyc=2381003`
- VRAM stop line: `none`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=1029164 vram=42000`
- Last keyboard line: `[KBD] release key=2 mcyc=1629480 vram=63085`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- PIC stop line: `none`
- First PPI key-read line: `none`
- First PPI line: `none`
- PPI stop line: `none`
- First IRQ line: `none`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First checksum line: `none`
- Last checksum line: `none`
- First FDC line: `none`
- FDC stop line: `none`
- FDC data-stop line: `none`
- EKDOS prompt line: `[PROMPT] EKDOS A> prompt reached x=0 y=70 mcyc=2701313 vram=73405 pc=0x097a`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0x097a sp=0xd2e8 instr=0x77 ba=0xe431 db=0xff mcyc=2701313 vram=73405 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- Visible state line: `[STATE] pc=097a sp=d2e8 a=00 b=02 c=28 d=d4 e=97 h=e4 l=31 sf=0 zf=0 hf=1 pf=0 cf=0 iff=1 mode=0 portc=04 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=02 fdc_sector=06 fdc_data=e5 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=22945 raw_reads=16765 raw_writes=6180 pic_ios=190 pic_reads=0 pic_writes=190 ppi_ios=11613 ppi_reads=5847 ppi_writes=5766 ppi_key_reads=552 fdc_ios=10925 fdc_reads=10854 fdc_writes=71 frame_ticks=53 intr_edges=32 inta_edges=96`
- FDC state line: `[FDCSTATE] data_reads=10752 buffer_pos=0 buffer_len=0`

## Checksum Trace

```text

```

## PPI0 Trace

```text

```

## Raw I/O Trace

```text

```

## IRQ Trace

```text

```

## FDC Trace

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
- With `STOPPROMPT=1`, this same harness proves the full `juku_top` ROMBIOS
  `TDD` path to an EKDOS `A>` prompt.
