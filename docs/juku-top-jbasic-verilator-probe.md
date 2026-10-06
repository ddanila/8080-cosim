# juku_top uninterrupted JBASIC READY probe

Status: **HDL JUKU_TOP JBASIC READY REACHED**

This report records a bounded `juku_top` run with the vendored disk image,
frame interrupts and ROMBIOS `TDD` keyboard sequence. Its status describes
that recorded run; checking the committed report does not rerun current HDL.
The harness defaults to Icarus and also accepts Verilator. See
[simulator compatibility](../sync/README.md#simulator-compatibility) before
attempting a Verilator rerun.

## Harness entry point

```sh
sync/juku_top_fdc_probe.sh
```

Harness defaults and all overrides are defined in
[`sync/juku_top_fdc_probe.sh`](../sync/juku_top_fdc_probe.sh).
The bare command uses the default early-FDC stop; it does not reproduce
this recorded prompt run. Use the recorded settings below for that case,
subject to the simulator compatibility limit above.

Recorded settings: `DISK=media/disks/JUKPROG2.CPM SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=10000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=0 TRACEFDC=0 STOPIO=0 MAXVRAM=85000 TIMECAP=30000000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 JBASICKEYS=1 STOPJBASICCMD=0 STOPJBASICREADY=1 COMMAND_KEY_MCYC=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=900`.

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
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=70000 mcyc=2381003`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=1029164 vram=42000`
- Last keyboard line: `[KBD] release key=3 mcyc=4379044 vram=73506`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- EKDOS prompt line: `[PROMPT] EKDOS A> prompt reached x=0 y=70 mcyc=2733010 vram=73405 pc=0x097a`
- EKDOS JBASIC command line: `[JBASIC-CMD] A>JBASIC command line reached mcyc=4062390 vram=73485 pc=0x097a`
- BASIC READY line: `[JBASIC] READY prompt reached mcyc=4765627 vram=73885 pc=0x097a`
- CPU state line: `[CPU] pc=0x097a sp=0xd2e8 instr=0x77 ba=0xec04 db=0xff mcyc=4765627 vram=73885 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=0`
- Visible state line: `[STATE] pc=097a sp=d2e8 a=00 b=02 c=28 d=d4 e=97 h=ec l=04 sf=0 zf=0 hf=1 pf=0 cf=0 iff=1 mode=0 portc=04 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=14 fdc_sector=09 fdc_data=00 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=78383 raw_reads=49275 raw_writes=29108 pic_ios=376 pic_reads=0 pic_writes=376 ppi_ios=57276 ppi_reads=28984 ppi_writes=28292 ppi_key_reads=1198 fdc_ios=20279 fdc_reads=20151 fdc_writes=128 frame_ticks=93 intr_edges=70 inta_edges=210`
- FDC state line: `[FDCSTATE] data_reads=19968 buffer_pos=0 buffer_len=0`

## Scope

- `STOPPROMPT=1` stops on the EKDOS `A>` bitmap. `JBASICKEYS=1` with
  `STOPJBASICREADY=1` targets disk BASIC `READY`; use `JUKPROG2.CPM` for
  the preserved live-load BASIC candidate.
- The status and markers describe the recorded stop. A zero runner exit
  also permits a timeout (`124`); it does not by itself prove either prompt.
- [Timing reference](ekdos-timing-reference.md) pins the C-model anchors.
  This diagnostic does not establish physical FDC behavior.
