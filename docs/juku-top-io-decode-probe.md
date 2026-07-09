# juku_top I/O decode probe

Status: **HDL JUKU_TOP RAW I/O DECODE OBSERVED**

This fast diagnostic runs the LVS-checked `juku_top` only far enough to
sample the first settled raw I/O cycles and D7/D9 chip-select decode. It is
not the EKDOS milestone gate; the full disk-backed prompt proof is tracked
separately in `docs/juku-top-fdc-verilator-probe.md`.

## Command

```sh
sync/juku_top_io_decode_probe.sh
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

Current values: `SIM=icarus KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=80000 FRAMEPHASE=0 FRAMEMCYC=0 TRACEPROGRESS=5000 VRAMSTOP_SYNC=0 TRACEIO=1 TRACECHK=0 TRACEPPI=1 TRACEIRQ=1 TRACEFDC=1 STOPIO=20 MAXVRAM=88000 TIMECAP=900000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 JBASICKEYS=0 STOPJBASICCMD=0 STOPJBASICREADY=0 COMMAND_KEY_MCYC=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=60`.

## Evidence

| Check | Result |
| --- | --- |
| simulator | `icarus` |
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
| EKDOS `A>` prompt bitmap observed | NO |
| EKDOS `A>JBASIC` command bitmap observed | NO |
| BASIC `READY` prompt bitmap observed | NO |
| keyboard trace lines | `0` |
| VRAM progress trace lines | `0` |
| PIC trace lines | `0` |
| PPI key-read trace lines | `0` |
| PPI trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `21` |
| FDC trace lines | `0` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `none`
- Verilator walltime line: `none`
- First VRAM line: `none`
- Last VRAM progress line: `none`
- VRAM stop line: `none`
- First keyboard line: `none`
- Last keyboard line: `none`
- First PIC line: `none`
- PIC stop line: `none`
- First PPI key-read line: `none`
- First PPI line: `none`
- PPI stop line: `none`
- First IRQ line: `none`
- First raw I/O line: `[RAWIO] OUT ba=0x0f0f port=0x0f data=0x9b mcyc=29 vram=0 ios=1 pic=0 ppi0=0 sio0=0 ppi1=1 pit0=0 pit1=0 pit2=0 fdc=0`
- Raw I/O stop line: `[RAWIO] stop ios=20 reads=0 writes=20 mcyc=153 vram=0`
- First checksum line: `none`
- Last checksum line: `none`
- First FDC line: `none`
- FDC stop line: `none`
- FDC data-stop line: `none`
- EKDOS prompt line: `none`
- EKDOS JBASIC command line: `none`
- BASIC READY line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0x020e sp=0xd44e instr=0xd3 ba=0x020e db=0xff mcyc=153 vram=0 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=1 intr=0 xchg_dh=0`
- Visible state line: `[STATE] pc=020e sp=d44e a=ff b=d7 c=e7 d=xx e=00 h=d7 l=5d sf=0 zf=0 hf=1 pf=0 cf=0 iff=0 mode=0 portc=80 kbd_col=07 pic_icw1=00 pic_icw2=00 pic_mask=ff pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=20 raw_reads=0 raw_writes=20 pic_ios=0 pic_reads=0 pic_writes=0 ppi_ios=4 ppi_reads=0 ppi_writes=4 ppi_key_reads=0 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=0 intr_edges=0 inta_edges=0`
- FDC state line: `[FDCSTATE] data_reads=0 buffer_pos=0 buffer_len=0`

## Checksum Trace

```text

```

## PPI0 Trace

```text

```

## Raw I/O Trace

```text
[RAWIO] OUT ba=0x0f0f port=0x0f data=0x9b mcyc=29 vram=0 ios=1 pic=0 ppi0=0 sio0=0 ppi1=1 pit0=0 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x0707 port=0x07 data=0x82 mcyc=34 vram=0 ios=2 pic=0 ppi0=1 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x0707 port=0x07 data=0x0f mcyc=39 vram=0 ios=3 pic=0 ppi0=1 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x0404 port=0x04 data=0x27 mcyc=44 vram=0 ios=4 pic=0 ppi0=1 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x0404 port=0x04 data=0x07 mcyc=49 vram=0 ios=5 pic=0 ppi0=1 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x1313 port=0x13 data=0x15 mcyc=85 vram=0 ios=6 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=1 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x1313 port=0x13 data=0x53 mcyc=90 vram=0 ios=7 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=1 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x1313 port=0x13 data=0x93 mcyc=95 vram=0 ios=8 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=1 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x1717 port=0x17 data=0x73 mcyc=100 vram=0 ios=9 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=1 pit2=0 fdc=0
[RAWIO] OUT ba=0x1717 port=0x17 data=0x93 mcyc=105 vram=0 ios=10 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=1 pit2=0 fdc=0
[RAWIO] OUT ba=0x1717 port=0x17 data=0x34 mcyc=110 vram=0 ios=11 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=1 pit2=0 fdc=0
[RAWIO] OUT ba=0x1414 port=0x14 data=0x39 mcyc=115 vram=0 ios=12 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=1 pit2=0 fdc=0
[RAWIO] OUT ba=0x1414 port=0x14 data=0x01 mcyc=120 vram=0 ios=13 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=1 pit2=0 fdc=0
[RAWIO] OUT ba=0x1b1b port=0x1b data=0x1f mcyc=125 vram=0 ios=14 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] OUT ba=0x1b1b port=0x1b data=0x76 mcyc=130 vram=0 ios=15 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] OUT ba=0x1b1b port=0x1b data=0xb0 mcyc=135 vram=0 ios=16 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] OUT ba=0x1010 port=0x10 data=0x64 mcyc=140 vram=0 ios=17 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=1 pit1=0 pit2=0 fdc=0
[RAWIO] OUT ba=0x1818 port=0x18 data=0x32 mcyc=145 vram=0 ios=18 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] OUT ba=0x1a1a port=0x1a data=0xff mcyc=150 vram=0 ios=19 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] OUT ba=0x1a1a port=0x1a data=0xff mcyc=153 vram=0 ios=20 pic=0 ppi0=0 sio0=0 ppi1=0 pit0=0 pit1=0 pit2=1 fdc=0
[RAWIO] stop ios=20 reads=0 writes=20 mcyc=153 vram=0
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
