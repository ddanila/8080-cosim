# juku_top uninterrupted JBASIC READY probe

Status: **HDL JUKU_TOP JBASIC READY REACHED**

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
- `JUKU_TOP_FDC_JBASICKEYS` default `0`; set to `1` to type
  `JBASIC` + Enter after the EKDOS `A>` bitmap is observed
- `JUKU_TOP_FDC_STOPJBASICCMD` default `0`; set to `1` to stop when
  the `A>JBASIC` command line bitmap appears
- `JUKU_TOP_FDC_STOPJBASICREADY` default `0`; set to `1` to stop when
  the BASIC `READY` bitmap appears
- `JUKU_TOP_FDC_COMMAND_KEY_MCYC` default `0`; optional minimum machine
  cycle before post-prompt command-key injection
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=10000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=0 TRACEFDC=0 STOPIO=0 MAXVRAM=85000 TIMECAP=30000000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 JBASICKEYS=1 STOPJBASICCMD=0 STOPJBASICREADY=1 COMMAND_KEY_MCYC=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=900`.

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
| EKDOS `A>JBASIC` command bitmap observed | YES |
| BASIC `READY` prompt bitmap observed | YES |
| keyboard trace lines | `20` |
| VRAM progress trace lines | `7` |
| PIC trace lines | `376` |
| PPI key-read trace lines | `0` |
| PPI trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `0` |
| FDC trace lines | `0` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKPROG2.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 16.387 s (elab=0.025, cvt=0.249, bld=16.049); cpu 0.338 s on 1 threads; alloced 23.672 MB`
- Verilator walltime line: `- Verilator: $finish at 709ms; walltime 78.890 s; speed 8.990 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=70000 mcyc=2381003`
- VRAM stop line: `none`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=1029164 vram=42000`
- Last keyboard line: `[KBD] release key=3 mcyc=4379044 vram=73506`
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
- EKDOS prompt line: `[PROMPT] EKDOS A> prompt reached x=0 y=70 mcyc=2733010 vram=73405 pc=0x097a`
- EKDOS JBASIC command line: `[JBASIC-CMD] A>JBASIC command line reached mcyc=4062390 vram=73485 pc=0x097a`
- BASIC READY line: `[JBASIC] READY prompt reached mcyc=4765627 vram=73885 pc=0x097a`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0x097a sp=0xd2e8 instr=0x77 ba=0xec04 db=0xff mcyc=4765627 vram=73885 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=0`
- Visible state line: `[STATE] pc=097a sp=d2e8 a=00 b=02 c=28 d=d4 e=97 h=ec l=04 sf=0 zf=0 hf=1 pf=0 cf=0 iff=1 mode=0 portc=04 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=14 fdc_sector=09 fdc_data=00 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=78383 raw_reads=49275 raw_writes=29108 pic_ios=376 pic_reads=0 pic_writes=376 ppi_ios=57276 ppi_reads=28984 ppi_writes=28292 ppi_key_reads=1198 fdc_ios=20279 fdc_reads=20151 fdc_writes=128 frame_ticks=93 intr_edges=70 inta_edges=210`
- FDC state line: `[FDCSTATE] data_reads=19968 buffer_pos=0 buffer_len=0`

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
  `+stopfdc=N`, plus `+stopprompt=1` for the EKDOS `A>` bitmap,
  `+jbasickeys=1` with `+stopjbasiccmd=1` / `+stopjbasicready=1` for
  the EKDOS `JBASIC` path, and `+stoppc=HEX` / `+stoppc_skip=N` for
  CPU address stops.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- `docs/ekdos-timing-reference.md` shows the fast cosim target for this same
  vendored `TDD` path: first PIC/PPI setup around 30,520 VRAM writes, first
  frame IRQ at 33,812 VRAM writes, and first FDC command at 63,085 VRAM writes.
- With `STOPPROMPT=1`, this same harness can prove the full `juku_top`
  ROMBIOS `TDD` path to an EKDOS `A>` prompt.
- With `JBASICKEYS=1` and `STOPJBASICREADY=1`, the same reset-driven path
  continues through `JUKPROG2.CPM` to the visible BASIC `READY` prompt.
