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

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=200000 TRACEPROGRESS=5000 TRACEIO=0 TRACECHK=0 STOPIO=0 MAXVRAM=90000 TIMECAP=2400000000 STOPFDC=80 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=300`.

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
| PIC trace lines | `37` |
| PPI key-read trace lines | `0` |
| IRQ trace lines | `40` |
| raw I/O trace lines | `0` |
| FDC trace lines | `81` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 15.785 s (elab=0.020, cvt=0.163, bld=15.553); cpu 0.232 s on 1 threads; alloced 17.359 MB`
- Verilator walltime line: `- Verilator: $finish at 160ms; walltime 20.356 s; speed 7.883 ms/s`
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
- FDC stop line: `[FDC] stop ios=80 reads=77 writes=3 mcyc=1014893`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0xe5aa sp=0xd436 instr=0xdb ba=0x1f1f db=0xff mcyc=1014893 vram=30524 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- Visible state line: `[STATE] pc=e5aa sp=d436 a=00 b=01 c=35 d=08 e=aa h=aa l=f3 sf=0 zf=0 hf=0 pf=0 cf=0 iff=0 mode=1 portc=75 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=ff pic_expect_icw2=0 fdc_motor_on=1 fdc_status=10 fdc_track=00 fdc_sector=aa fdc_data=00 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=845 raw_reads=508 raw_writes=337 pic_ios=37 pic_reads=0 pic_writes=37 ppi_ios=647 ppi_reads=411 ppi_writes=236 ppi_key_reads=0 fdc_ios=80 fdc_reads=77 fdc_writes=3 frame_ticks=40 intr_edges=10 inta_edges=30`

## Checksum Trace

```text

```

## FDC Trace

```text
[FDC] IN  port=0x1c reg=0 data=0x80 mcyc=1012756 ios=1
[FDC] IN  port=0x1c reg=0 data=0x00 mcyc=1013448 ios=2
[FDC] OUT port=0x1f reg=3 data=0x00 mcyc=1013681 ios=3
[FDC] OUT port=0x1e reg=2 data=0xaa mcyc=1013696 ios=4
[FDC] IN  port=0x1d reg=1 data=0x00 mcyc=1013704 ios=5
[FDC] OUT port=0x1c reg=0 data=0x80 mcyc=1013928 ios=6
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1013944 ios=7
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1013957 ios=8
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1013970 ios=9
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1013983 ios=10
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1013996 ios=11
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014009 ios=12
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014022 ios=13
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014035 ios=14
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014048 ios=15
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014061 ios=16
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014074 ios=17
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014087 ios=18
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014100 ios=19
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014113 ios=20
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014126 ios=21
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014139 ios=22
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014152 ios=23
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014165 ios=24
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014178 ios=25
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014191 ios=26
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014204 ios=27
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014217 ios=28
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014230 ios=29
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014243 ios=30
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014256 ios=31
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014269 ios=32
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014282 ios=33
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014295 ios=34
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014308 ios=35
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014321 ios=36
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014334 ios=37
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014347 ios=38
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014360 ios=39
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014373 ios=40
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014386 ios=41
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014399 ios=42
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014412 ios=43
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014425 ios=44
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014438 ios=45
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014451 ios=46
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014464 ios=47
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014477 ios=48
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014490 ios=49
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014503 ios=50
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014516 ios=51
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014529 ios=52
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014542 ios=53
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014555 ios=54
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014568 ios=55
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014581 ios=56
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014594 ios=57
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014607 ios=58
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014620 ios=59
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014633 ios=60
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014646 ios=61
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014659 ios=62
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014672 ios=63
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014685 ios=64
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014698 ios=65
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014711 ios=66
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014724 ios=67
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014737 ios=68
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014750 ios=69
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014763 ios=70
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014776 ios=71
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014789 ios=72
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014802 ios=73
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014815 ios=74
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014828 ios=75
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014841 ios=76
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014854 ios=77
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014867 ios=78
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014880 ios=79
[FDC] IN  port=0x1f reg=3 data=0x00 mcyc=1014893 ios=80
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
