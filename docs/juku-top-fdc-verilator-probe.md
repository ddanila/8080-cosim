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
- `JUKU_TOP_FDC_FRAMEPHASE` default `0`
- `JUKU_TOP_FDC_TRACEPROGRESS` default `5000`
- `JUKU_TOP_FDC_TRACEIO` default `0`
- `JUKU_TOP_FDC_TRACECHK` default `0`
- `JUKU_TOP_FDC_TRACEPPI` default `1`
- `JUKU_TOP_FDC_TRACEIRQ` default `1`
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=200000 FRAMEPHASE=0 TRACEPROGRESS=5000 TRACEIO=0 TRACECHK=0 TRACEPPI=1 TRACEIRQ=1 STOPIO=0 MAXVRAM=90000 TIMECAP=2400000000 STOPFDC=80 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=300`.

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
| PPI key-read trace observed | PASS |
| IRQ trace observed | PASS |
| decoded FDC I/O observed | YES |
| EKDOS `A>` prompt bitmap observed | NO |
| keyboard trace lines | `0` |
| VRAM progress trace lines | `6` |
| PIC trace lines | `37` |
| PPI key-read trace lines | `178` |
| PPI trace lines | `178` |
| IRQ trace lines | `40` |
| raw I/O trace lines | `0` |
| FDC trace lines | `81` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 15.171 s (elab=0.020, cvt=0.167, bld=14.935); cpu 0.237 s on 1 threads; alloced 17.348 MB`
- Verilator walltime line: `- Verilator: $finish at 160ms; walltime 12.368 s; speed 12.975 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=30000 mcyc=522138`
- VRAM stop line: `none`
- First keyboard line: `none`
- Last keyboard line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- PIC stop line: `none`
- First PPI key-read line: `[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776367 vram=30520 key_reads=1`
- First PPI line: `[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776367 vram=30520 key_reads=1`
- PPI stop line: `none`
- First IRQ line: `[IRQ] intr rise count=1 pc=0xdb02 sp=0xd440 osc=6200001 mcyc=785934 vram=30524`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First checksum line: `none`
- Last checksum line: `none`
- First FDC line: `[FDC] IN  port=0x1c reg=0 data=0x80 pc=0xe771 sp=0xd432 a=0x11 b=0x00 c=0xd7 d=0x0d e=0x47 h=0x01 l=0xd9 mcyc=1012756 vram=30524 ios=1`
- FDC stop line: `[FDC] stop ios=80 reads=77 writes=3 mcyc=1014893`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0xe5aa sp=0xd436 instr=0xdb ba=0x1f1f db=0xff mcyc=1014893 vram=30524 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- Visible state line: `[STATE] pc=e5aa sp=d436 a=00 b=01 c=35 d=08 e=aa h=aa l=f3 sf=0 zf=0 hf=0 pf=0 cf=0 iff=0 mode=1 portc=75 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=ff pic_expect_icw2=0 fdc_motor_on=1 fdc_status=10 fdc_track=00 fdc_sector=aa fdc_data=00 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=845 raw_reads=508 raw_writes=337 pic_ios=37 pic_reads=0 pic_writes=37 ppi_ios=647 ppi_reads=411 ppi_writes=236 ppi_key_reads=178 fdc_ios=80 fdc_reads=77 fdc_writes=3 frame_ticks=40 intr_edges=10 inta_edges=30`

## Checksum Trace

```text

```

## PPI0 Trace

```text
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776367 vram=30520 key_reads=1
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776392 vram=30520 key_reads=2
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776417 vram=30520 key_reads=3
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776442 vram=30520 key_reads=4
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776467 vram=30520 key_reads=5
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776492 vram=30520 key_reads=6
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776517 vram=30520 key_reads=7
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776542 vram=30520 key_reads=8
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786237 vram=30524 key_reads=9
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786257 vram=30524 key_reads=10
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786277 vram=30524 key_reads=11
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786297 vram=30524 key_reads=12
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786317 vram=30524 key_reads=13
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786337 vram=30524 key_reads=14
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786357 vram=30524 key_reads=15
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786377 vram=30524 key_reads=16
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786397 vram=30524 key_reads=17
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786417 vram=30524 key_reads=18
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786437 vram=30524 key_reads=19
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786457 vram=30524 key_reads=20
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786477 vram=30524 key_reads=21
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786497 vram=30524 key_reads=22
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786517 vram=30524 key_reads=23
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=786537 vram=30524 key_reads=24
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=786551 vram=30524 key_reads=25
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811334 vram=30524 key_reads=26
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811354 vram=30524 key_reads=27
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811374 vram=30524 key_reads=28
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811394 vram=30524 key_reads=29
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811414 vram=30524 key_reads=30
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811434 vram=30524 key_reads=31
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811454 vram=30524 key_reads=32
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811474 vram=30524 key_reads=33
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811494 vram=30524 key_reads=34
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811514 vram=30524 key_reads=35
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811534 vram=30524 key_reads=36
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811554 vram=30524 key_reads=37
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811574 vram=30524 key_reads=38
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811594 vram=30524 key_reads=39
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811614 vram=30524 key_reads=40
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=811634 vram=30524 key_reads=41
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=811648 vram=30524 key_reads=42
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836443 vram=30524 key_reads=43
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836463 vram=30524 key_reads=44
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836483 vram=30524 key_reads=45
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836503 vram=30524 key_reads=46
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836523 vram=30524 key_reads=47
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836543 vram=30524 key_reads=48
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836563 vram=30524 key_reads=49
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836583 vram=30524 key_reads=50
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836603 vram=30524 key_reads=51
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836623 vram=30524 key_reads=52
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836643 vram=30524 key_reads=53
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836663 vram=30524 key_reads=54
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836683 vram=30524 key_reads=55
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836703 vram=30524 key_reads=56
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836723 vram=30524 key_reads=57
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=836743 vram=30524 key_reads=58
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=836757 vram=30524 key_reads=59
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861537 vram=30524 key_reads=60
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861557 vram=30524 key_reads=61
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861577 vram=30524 key_reads=62
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861597 vram=30524 key_reads=63
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861617 vram=30524 key_reads=64
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861637 vram=30524 key_reads=65
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861657 vram=30524 key_reads=66
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861677 vram=30524 key_reads=67
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861697 vram=30524 key_reads=68
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861717 vram=30524 key_reads=69
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861737 vram=30524 key_reads=70
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861757 vram=30524 key_reads=71
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861777 vram=30524 key_reads=72
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861797 vram=30524 key_reads=73
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861817 vram=30524 key_reads=74
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=861837 vram=30524 key_reads=75
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=861851 vram=30524 key_reads=76
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886632 vram=30524 key_reads=77
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886652 vram=30524 key_reads=78
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886672 vram=30524 key_reads=79
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886692 vram=30524 key_reads=80
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886712 vram=30524 key_reads=81
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886732 vram=30524 key_reads=82
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886752 vram=30524 key_reads=83
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886772 vram=30524 key_reads=84
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886792 vram=30524 key_reads=85
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886812 vram=30524 key_reads=86
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886832 vram=30524 key_reads=87
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886852 vram=30524 key_reads=88
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886872 vram=30524 key_reads=89
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886892 vram=30524 key_reads=90
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886912 vram=30524 key_reads=91
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=886932 vram=30524 key_reads=92
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=886946 vram=30524 key_reads=93
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911726 vram=30524 key_reads=94
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911746 vram=30524 key_reads=95
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911766 vram=30524 key_reads=96
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911786 vram=30524 key_reads=97
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911806 vram=30524 key_reads=98
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911826 vram=30524 key_reads=99
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911846 vram=30524 key_reads=100
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911866 vram=30524 key_reads=101
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911886 vram=30524 key_reads=102
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911906 vram=30524 key_reads=103
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911926 vram=30524 key_reads=104
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911946 vram=30524 key_reads=105
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911966 vram=30524 key_reads=106
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=911986 vram=30524 key_reads=107
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=912006 vram=30524 key_reads=108
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=912026 vram=30524 key_reads=109
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=912040 vram=30524 key_reads=110
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936821 vram=30524 key_reads=111
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936841 vram=30524 key_reads=112
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936861 vram=30524 key_reads=113
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936881 vram=30524 key_reads=114
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936901 vram=30524 key_reads=115
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936921 vram=30524 key_reads=116
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936941 vram=30524 key_reads=117
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936961 vram=30524 key_reads=118
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=936981 vram=30524 key_reads=119
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937001 vram=30524 key_reads=120
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937021 vram=30524 key_reads=121
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937041 vram=30524 key_reads=122
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937061 vram=30524 key_reads=123
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937081 vram=30524 key_reads=124
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937101 vram=30524 key_reads=125
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=937121 vram=30524 key_reads=126
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=937135 vram=30524 key_reads=127
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=961915 vram=30524 key_reads=128
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=961935 vram=30524 key_reads=129
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=961955 vram=30524 key_reads=130
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=961975 vram=30524 key_reads=131
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=961995 vram=30524 key_reads=132
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962015 vram=30524 key_reads=133
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962035 vram=30524 key_reads=134
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962055 vram=30524 key_reads=135
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962075 vram=30524 key_reads=136
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962095 vram=30524 key_reads=137
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962115 vram=30524 key_reads=138
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962135 vram=30524 key_reads=139
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962155 vram=30524 key_reads=140
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962175 vram=30524 key_reads=141
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962195 vram=30524 key_reads=142
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=962215 vram=30524 key_reads=143
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=962229 vram=30524 key_reads=144
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987010 vram=30524 key_reads=145
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987030 vram=30524 key_reads=146
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987050 vram=30524 key_reads=147
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987070 vram=30524 key_reads=148
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987090 vram=30524 key_reads=149
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987110 vram=30524 key_reads=150
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987130 vram=30524 key_reads=151
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987150 vram=30524 key_reads=152
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987170 vram=30524 key_reads=153
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987190 vram=30524 key_reads=154
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987210 vram=30524 key_reads=155
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987230 vram=30524 key_reads=156
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987250 vram=30524 key_reads=157
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987270 vram=30524 key_reads=158
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987290 vram=30524 key_reads=159
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=987310 vram=30524 key_reads=160
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=987324 vram=30524 key_reads=161
[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012121 vram=30524 key_reads=162
[PPI0] IN  port=0x05 reg=1 data=0xcf col=14 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012141 vram=30524 key_reads=163
[PPI0] IN  port=0x05 reg=1 data=0xcf col=13 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012161 vram=30524 key_reads=164
[PPI0] IN  port=0x05 reg=1 data=0xcf col=12 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012181 vram=30524 key_reads=165
[PPI0] IN  port=0x05 reg=1 data=0xcf col=11 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012201 vram=30524 key_reads=166
[PPI0] IN  port=0x05 reg=1 data=0xcf col=10 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012221 vram=30524 key_reads=167
[PPI0] IN  port=0x05 reg=1 data=0xcf col=9 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012241 vram=30524 key_reads=168
[PPI0] IN  port=0x05 reg=1 data=0xcf col=8 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012261 vram=30524 key_reads=169
[PPI0] IN  port=0x05 reg=1 data=0xcf col=7 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012281 vram=30524 key_reads=170
[PPI0] IN  port=0x05 reg=1 data=0xcf col=6 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012301 vram=30524 key_reads=171
[PPI0] IN  port=0x05 reg=1 data=0xcf col=5 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012321 vram=30524 key_reads=172
[PPI0] IN  port=0x05 reg=1 data=0xcf col=4 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012341 vram=30524 key_reads=173
[PPI0] IN  port=0x05 reg=1 data=0xcf col=3 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012361 vram=30524 key_reads=174
[PPI0] IN  port=0x05 reg=1 data=0xcf col=2 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012381 vram=30524 key_reads=175
[PPI0] IN  port=0x05 reg=1 data=0xcf col=1 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012401 vram=30524 key_reads=176
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x1463 mcyc=1012421 vram=30524 key_reads=177
[PPI0] IN  port=0x05 reg=1 data=0xcf col=0 key_col=0 key_bit=0 pressed=0 pc=0x128c mcyc=1012435 vram=30524 key_reads=178
```

## FDC Trace

```text
[FDC] IN  port=0x1c reg=0 data=0x80 pc=0xe771 sp=0xd432 a=0x11 b=0x00 c=0xd7 d=0x0d e=0x47 h=0x01 l=0xd9 mcyc=1012756 vram=30524 ios=1
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe75e sp=0xd432 a=0x75 b=0x64 c=0x08 d=0x0d e=0xaa h=0x01 l=0xe5 mcyc=1013448 vram=30524 ios=2
[FDC] OUT port=0x1f reg=3 data=0x00 pc=0xe62d sp=0xd434 a=0x00 b=0x40 c=0x08 d=0x0d e=0xaa h=0x01 l=0xe5 mcyc=1013681 vram=30524 ios=3
[FDC] OUT port=0x1e reg=2 data=0xaa pc=0xe639 sp=0xd434 a=0xaa b=0x40 c=0x08 d=0x0d e=0xaa h=0x01 l=0xe5 mcyc=1013696 vram=30524 ios=4
[FDC] IN  port=0x1d reg=1 data=0x00 pc=0xe63f sp=0xd434 a=0x00 b=0x00 c=0x08 d=0x0d e=0xaa h=0x01 l=0xe5 mcyc=1013704 vram=30524 ios=5
[FDC] OUT port=0x1c reg=0 data=0x80 pc=0xe5a3 sp=0xd436 a=0x80 b=0x01 c=0x7e d=0x08 e=0xaa h=0xaa l=0xaa mcyc=1013928 vram=30524 ios=6
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x80 b=0x01 c=0x7e d=0x08 e=0xaa h=0xaa l=0xaa mcyc=1013944 vram=30524 ios=7
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x7d d=0x08 e=0xaa h=0xaa l=0xab mcyc=1013957 vram=30524 ios=8
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x7c d=0x08 e=0xaa h=0xaa l=0xac mcyc=1013970 vram=30524 ios=9
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x7b d=0x08 e=0xaa h=0xaa l=0xad mcyc=1013983 vram=30524 ios=10
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x7a d=0x08 e=0xaa h=0xaa l=0xae mcyc=1013996 vram=30524 ios=11
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x79 d=0x08 e=0xaa h=0xaa l=0xaf mcyc=1014009 vram=30524 ios=12
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x78 d=0x08 e=0xaa h=0xaa l=0xb0 mcyc=1014022 vram=30524 ios=13
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x77 d=0x08 e=0xaa h=0xaa l=0xb1 mcyc=1014035 vram=30524 ios=14
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x76 d=0x08 e=0xaa h=0xaa l=0xb2 mcyc=1014048 vram=30524 ios=15
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x75 d=0x08 e=0xaa h=0xaa l=0xb3 mcyc=1014061 vram=30524 ios=16
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x74 d=0x08 e=0xaa h=0xaa l=0xb4 mcyc=1014074 vram=30524 ios=17
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x73 d=0x08 e=0xaa h=0xaa l=0xb5 mcyc=1014087 vram=30524 ios=18
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x72 d=0x08 e=0xaa h=0xaa l=0xb6 mcyc=1014100 vram=30524 ios=19
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x71 d=0x08 e=0xaa h=0xaa l=0xb7 mcyc=1014113 vram=30524 ios=20
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x70 d=0x08 e=0xaa h=0xaa l=0xb8 mcyc=1014126 vram=30524 ios=21
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6f d=0x08 e=0xaa h=0xaa l=0xb9 mcyc=1014139 vram=30524 ios=22
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6e d=0x08 e=0xaa h=0xaa l=0xba mcyc=1014152 vram=30524 ios=23
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6d d=0x08 e=0xaa h=0xaa l=0xbb mcyc=1014165 vram=30524 ios=24
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6c d=0x08 e=0xaa h=0xaa l=0xbc mcyc=1014178 vram=30524 ios=25
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6b d=0x08 e=0xaa h=0xaa l=0xbd mcyc=1014191 vram=30524 ios=26
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x6a d=0x08 e=0xaa h=0xaa l=0xbe mcyc=1014204 vram=30524 ios=27
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x69 d=0x08 e=0xaa h=0xaa l=0xbf mcyc=1014217 vram=30524 ios=28
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x68 d=0x08 e=0xaa h=0xaa l=0xc0 mcyc=1014230 vram=30524 ios=29
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x67 d=0x08 e=0xaa h=0xaa l=0xc1 mcyc=1014243 vram=30524 ios=30
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x66 d=0x08 e=0xaa h=0xaa l=0xc2 mcyc=1014256 vram=30524 ios=31
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x65 d=0x08 e=0xaa h=0xaa l=0xc3 mcyc=1014269 vram=30524 ios=32
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x64 d=0x08 e=0xaa h=0xaa l=0xc4 mcyc=1014282 vram=30524 ios=33
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x63 d=0x08 e=0xaa h=0xaa l=0xc5 mcyc=1014295 vram=30524 ios=34
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x62 d=0x08 e=0xaa h=0xaa l=0xc6 mcyc=1014308 vram=30524 ios=35
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x61 d=0x08 e=0xaa h=0xaa l=0xc7 mcyc=1014321 vram=30524 ios=36
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x60 d=0x08 e=0xaa h=0xaa l=0xc8 mcyc=1014334 vram=30524 ios=37
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5f d=0x08 e=0xaa h=0xaa l=0xc9 mcyc=1014347 vram=30524 ios=38
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5e d=0x08 e=0xaa h=0xaa l=0xca mcyc=1014360 vram=30524 ios=39
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5d d=0x08 e=0xaa h=0xaa l=0xcb mcyc=1014373 vram=30524 ios=40
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5c d=0x08 e=0xaa h=0xaa l=0xcc mcyc=1014386 vram=30524 ios=41
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5b d=0x08 e=0xaa h=0xaa l=0xcd mcyc=1014399 vram=30524 ios=42
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x5a d=0x08 e=0xaa h=0xaa l=0xce mcyc=1014412 vram=30524 ios=43
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x59 d=0x08 e=0xaa h=0xaa l=0xcf mcyc=1014425 vram=30524 ios=44
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x58 d=0x08 e=0xaa h=0xaa l=0xd0 mcyc=1014438 vram=30524 ios=45
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x57 d=0x08 e=0xaa h=0xaa l=0xd1 mcyc=1014451 vram=30524 ios=46
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x56 d=0x08 e=0xaa h=0xaa l=0xd2 mcyc=1014464 vram=30524 ios=47
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x55 d=0x08 e=0xaa h=0xaa l=0xd3 mcyc=1014477 vram=30524 ios=48
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x54 d=0x08 e=0xaa h=0xaa l=0xd4 mcyc=1014490 vram=30524 ios=49
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x53 d=0x08 e=0xaa h=0xaa l=0xd5 mcyc=1014503 vram=30524 ios=50
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x52 d=0x08 e=0xaa h=0xaa l=0xd6 mcyc=1014516 vram=30524 ios=51
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x51 d=0x08 e=0xaa h=0xaa l=0xd7 mcyc=1014529 vram=30524 ios=52
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x50 d=0x08 e=0xaa h=0xaa l=0xd8 mcyc=1014542 vram=30524 ios=53
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4f d=0x08 e=0xaa h=0xaa l=0xd9 mcyc=1014555 vram=30524 ios=54
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4e d=0x08 e=0xaa h=0xaa l=0xda mcyc=1014568 vram=30524 ios=55
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4d d=0x08 e=0xaa h=0xaa l=0xdb mcyc=1014581 vram=30524 ios=56
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4c d=0x08 e=0xaa h=0xaa l=0xdc mcyc=1014594 vram=30524 ios=57
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4b d=0x08 e=0xaa h=0xaa l=0xdd mcyc=1014607 vram=30524 ios=58
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x4a d=0x08 e=0xaa h=0xaa l=0xde mcyc=1014620 vram=30524 ios=59
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x49 d=0x08 e=0xaa h=0xaa l=0xdf mcyc=1014633 vram=30524 ios=60
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x48 d=0x08 e=0xaa h=0xaa l=0xe0 mcyc=1014646 vram=30524 ios=61
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x47 d=0x08 e=0xaa h=0xaa l=0xe1 mcyc=1014659 vram=30524 ios=62
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x46 d=0x08 e=0xaa h=0xaa l=0xe2 mcyc=1014672 vram=30524 ios=63
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x45 d=0x08 e=0xaa h=0xaa l=0xe3 mcyc=1014685 vram=30524 ios=64
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x44 d=0x08 e=0xaa h=0xaa l=0xe4 mcyc=1014698 vram=30524 ios=65
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x43 d=0x08 e=0xaa h=0xaa l=0xe5 mcyc=1014711 vram=30524 ios=66
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x42 d=0x08 e=0xaa h=0xaa l=0xe6 mcyc=1014724 vram=30524 ios=67
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x41 d=0x08 e=0xaa h=0xaa l=0xe7 mcyc=1014737 vram=30524 ios=68
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x40 d=0x08 e=0xaa h=0xaa l=0xe8 mcyc=1014750 vram=30524 ios=69
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3f d=0x08 e=0xaa h=0xaa l=0xe9 mcyc=1014763 vram=30524 ios=70
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3e d=0x08 e=0xaa h=0xaa l=0xea mcyc=1014776 vram=30524 ios=71
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3d d=0x08 e=0xaa h=0xaa l=0xeb mcyc=1014789 vram=30524 ios=72
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3c d=0x08 e=0xaa h=0xaa l=0xec mcyc=1014802 vram=30524 ios=73
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3b d=0x08 e=0xaa h=0xaa l=0xed mcyc=1014815 vram=30524 ios=74
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x3a d=0x08 e=0xaa h=0xaa l=0xee mcyc=1014828 vram=30524 ios=75
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x39 d=0x08 e=0xaa h=0xaa l=0xef mcyc=1014841 vram=30524 ios=76
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x38 d=0x08 e=0xaa h=0xaa l=0xf0 mcyc=1014854 vram=30524 ios=77
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x37 d=0x08 e=0xaa h=0xaa l=0xf1 mcyc=1014867 vram=30524 ios=78
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x36 d=0x08 e=0xaa h=0xaa l=0xf2 mcyc=1014880 vram=30524 ios=79
[FDC] IN  port=0x1f reg=3 data=0x00 pc=0xe5aa sp=0xd436 a=0x01 b=0x01 c=0x35 d=0x08 e=0xaa h=0xaa l=0xf3 mcyc=1014893 vram=30524 ios=80
[FDC] stop ios=80 reads=77 writes=3 mcyc=1014893
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
