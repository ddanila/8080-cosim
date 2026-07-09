# juku_top Verilator FDC probe

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
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_STOPPC_SKIP` default `0`; matching PC entries to skip
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=5000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=1 STOPIO=0 MAXVRAM=90000 TIMECAP=1800000000 STOPFDC=20 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=180`.

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
| IRQ trace observed | PASS |
| decoded FDC I/O observed | YES |
| EKDOS `A>` prompt bitmap observed | NO |
| keyboard trace lines | `6` |
| VRAM progress trace lines | `12` |
| PIC trace lines | `93` |
| PPI key-read trace lines | `0` |
| PPI trace lines | `0` |
| IRQ trace lines | `108` |
| raw I/O trace lines | `0` |
| FDC trace lines | `21` |
| checksum trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 17.279 s (elab=0.021, cvt=0.170, bld=17.037); cpu 0.241 s on 1 threads; alloced 17.438 MB`
- Verilator walltime line: `- Verilator: $finish at 330ms; walltime 45.879 s; speed 7.204 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=60000 mcyc=1396952`
- VRAM stop line: `none`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=1029164 vram=42000`
- Last keyboard line: `[KBD] release key=2 mcyc=1629480 vram=63085`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- PIC stop line: `none`
- First PPI key-read line: `none`
- First PPI line: `none`
- PPI stop line: `none`
- First IRQ line: `[IRQ] intr rise count=1 pc=0x0e24 sp=0xd434 osc=6400051 mcyc=811306 vram=33812`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First checksum line: `none`
- Last checksum line: `none`
- First FDC line: `[FDC] OUT port=0x1c reg=0 data=0x02 pc=0xe5de sp=0xd6de a=0x02 b=0x00 c=0xea d=0xd9 e=0x44 h=0x01 l=0xe5 mcyc=1590617 vram=63085 ios=1`
- FDC stop line: `[FDC] stop ios=20 reads=12 writes=8 mcyc=2159597`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0xe64d sp=0xd6dc instr=0xd3 ba=0xe64d db=0xff mcyc=2159597 vram=63095 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=1 intr=0 xchg_dh=0`
- Visible state line: `[STATE] pc=e64d sp=d6dc a=1a b=18 c=00 d=02 e=50 h=01 l=e5 sf=0 zf=0 hf=0 pf=0 cf=0 iff=1 mode=1 portc=05 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=00 fdc_sector=03 fdc_data=00 fdc_command=1a fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=10795 raw_reads=5358 raw_writes=5437 pic_ios=93 pic_reads=0 pic_writes=93 ppi_ios=10495 ppi_reads=5292 ppi_writes=5203 ppi_key_reads=467 fdc_ios=20 fdc_reads=12 fdc_writes=8 frame_ticks=42 intr_edges=27 inta_edges=81`

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
[IRQ] intr rise count=1 pc=0x0e24 sp=0xd434 osc=6400051 mcyc=811306 vram=33812
[IRQ] inta fall count=1 pc=0x0e24 sp=0xd434 db=0xcd osc=6400061 mcyc=811307 vram=33812
[IRQ] inta fall count=2 pc=0x0e24 sp=0xd433 db=0xd4 osc=6400071 mcyc=811308 vram=33812
[IRQ] inta fall count=3 pc=0x0e24 sp=0xd433 db=0xfe osc=6400077 mcyc=811309 vram=33812
[IRQ] intr rise count=2 pc=0x0e29 sp=0xd434 osc=6805375 mcyc=862067 vram=38798
[IRQ] inta fall count=4 pc=0x0e21 sp=0xd434 db=0xcd osc=6805387 mcyc=862069 vram=38798
[IRQ] inta fall count=5 pc=0x0e21 sp=0xd433 db=0xd4 osc=6805397 mcyc=862070 vram=38798
[IRQ] inta fall count=6 pc=0x0e21 sp=0xd433 db=0xfe osc=6805403 mcyc=862071 vram=38798
[IRQ] intr rise count=3 pc=0x0976 sp=0xd436 osc=7190245 mcyc=912828 vram=40619
[IRQ] inta fall count=7 pc=0x0976 sp=0xd436 db=0xcd osc=7190251 mcyc=912829 vram=40619
[IRQ] inta fall count=8 pc=0x0976 sp=0xd435 db=0xd4 osc=7190261 mcyc=912830 vram=40619
[IRQ] inta fall count=9 pc=0x0976 sp=0xd435 db=0xfe osc=7190267 mcyc=912831 vram=40619
[IRQ] intr rise count=4 pc=0xdce8 sp=0xd43e osc=7566247 mcyc=963589 vram=41223
[IRQ] inta fall count=10 pc=0xdce8 sp=0xd43e db=0xcd osc=7566253 mcyc=963590 vram=41223
[IRQ] inta fall count=11 pc=0xdce8 sp=0xd43d db=0xd4 osc=7566263 mcyc=963591 vram=41223
[IRQ] inta fall count=12 pc=0xdce8 sp=0xd43d db=0xfe osc=7566269 mcyc=963592 vram=41223
[IRQ] intr rise count=5 pc=0xff80 sp=0xd437 osc=7942381 mcyc=1014350 vram=41833
[IRQ] inta fall count=13 pc=0xd85b sp=0xd436 db=0xcd osc=7942393 mcyc=1014352 vram=41833
[IRQ] inta fall count=14 pc=0xd85b sp=0xd435 db=0xd4 osc=7942403 mcyc=1014353 vram=41833
[IRQ] inta fall count=15 pc=0xd85b sp=0xd435 db=0xfe osc=7942409 mcyc=1014354 vram=41833
[IRQ] intr rise count=6 pc=0x0977 sp=0xd436 osc=8318489 mcyc=1065111 vram=42441
[IRQ] inta fall count=16 pc=0xd48b sp=0xd434 db=0xcd osc=8318523 mcyc=1065116 vram=42441
[IRQ] inta fall count=17 pc=0xd48b sp=0xd433 db=0xd4 osc=8318533 mcyc=1065117 vram=42441
[IRQ] inta fall count=18 pc=0xd48b sp=0xd433 db=0xfe osc=8318539 mcyc=1065118 vram=42441
[IRQ] intr rise count=7 pc=0xd866 sp=0xd6da osc=8684599 mcyc=1115872 vram=42623
[IRQ] inta fall count=19 pc=0xd866 sp=0xd6da db=0xcd osc=8684605 mcyc=1115873 vram=42623
[IRQ] inta fall count=20 pc=0xd866 sp=0xd6d9 db=0xd4 osc=8684615 mcyc=1115874 vram=42623
[IRQ] inta fall count=21 pc=0xd866 sp=0xd6d9 db=0xfe osc=8684621 mcyc=1115875 vram=42623
[IRQ] intr rise count=8 pc=0x0e29 sp=0xd6cc osc=9088441 mcyc=1166633 vram=47390
[IRQ] inta fall count=22 pc=0x0e21 sp=0xd6cc db=0xcd osc=9088453 mcyc=1166635 vram=47390
[IRQ] inta fall count=23 pc=0x0e21 sp=0xd6cb db=0xd4 osc=9088463 mcyc=1166636 vram=47390
[IRQ] inta fall count=24 pc=0x0e21 sp=0xd6cb db=0xfe osc=9088469 mcyc=1166637 vram=47390
[IRQ] intr rise count=9 pc=0x0e2a sp=0xd6cc osc=9493747 mcyc=1217394 vram=52274
[IRQ] inta fall count=25 pc=0x0e2a sp=0xd6cc db=0xcd osc=9493753 mcyc=1217395 vram=52274
[IRQ] inta fall count=26 pc=0x0e2a sp=0xd6cb db=0xd4 osc=9493763 mcyc=1217396 vram=52274
[IRQ] inta fall count=27 pc=0x0e2a sp=0xd6cb db=0xfe osc=9493769 mcyc=1217397 vram=52274
[IRQ] intr rise count=10 pc=0xd7ec sp=0xd6d6 osc=9861831 mcyc=1268155 vram=52584
[IRQ] inta fall count=28 pc=0xd7ec sp=0xd6d6 db=0xcd osc=9861837 mcyc=1268156 vram=52584
[IRQ] inta fall count=29 pc=0xd7ec sp=0xd6d5 db=0xd4 osc=9861847 mcyc=1268157 vram=52584
[IRQ] inta fall count=30 pc=0xd7ec sp=0xd6d5 db=0xfe osc=9861853 mcyc=1268158 vram=52584
[IRQ] intr rise count=11 pc=0xd871 sp=0xd6dc osc=10221767 mcyc=1318916 vram=52584
[IRQ] inta fall count=31 pc=0xd871 sp=0xd6da db=0xcd osc=10221789 mcyc=1318919 vram=52584
[IRQ] inta fall count=32 pc=0xd871 sp=0xd6d9 db=0xd4 osc=10221799 mcyc=1318920 vram=52584
[IRQ] inta fall count=33 pc=0xd871 sp=0xd6d9 db=0xfe osc=10221805 mcyc=1318921 vram=52584
[IRQ] intr rise count=12 pc=0x0e26 sp=0xd6cc osc=10625621 mcyc=1369677 vram=57363
[IRQ] inta fall count=34 pc=0x0e26 sp=0xd6cc db=0xcd osc=10625629 mcyc=1369678 vram=57363
[IRQ] inta fall count=35 pc=0x0e26 sp=0xd6cb db=0xd4 osc=10625639 mcyc=1369679 vram=57363
[IRQ] inta fall count=36 pc=0x0e26 sp=0xd6cb db=0xfe osc=10625645 mcyc=1369680 vram=57363
[IRQ] intr rise count=13 pc=0x0e2d sp=0xd6cc osc=11030947 mcyc=1420438 vram=62242
[IRQ] inta fall count=37 pc=0x0e2d sp=0xd6cc db=0xcd osc=11030957 mcyc=1420439 vram=62242
[IRQ] inta fall count=38 pc=0x0e2d sp=0xd6cb db=0xd4 osc=11030967 mcyc=1420440 vram=62242
[IRQ] inta fall count=39 pc=0x0e2d sp=0xd6cb db=0xfe osc=11030973 mcyc=1420441 vram=62242
[IRQ] intr rise count=14 pc=0xd7f1 sp=0xd6e3 osc=11408285 mcyc=1471199 vram=62885
[IRQ] inta fall count=40 pc=0xd9d0 sp=0xd6e4 db=0xcd osc=11408297 mcyc=1471201 vram=62885
[IRQ] inta fall count=41 pc=0xd9d0 sp=0xd6e3 db=0xd4 osc=11408307 mcyc=1471202 vram=62885
[IRQ] inta fall count=42 pc=0xd9d0 sp=0xd6e3 db=0xfe osc=11408313 mcyc=1471203 vram=62885
[IRQ] intr rise count=15 pc=0xd861 sp=0xd6de osc=11768181 mcyc=1521960 vram=62885
[IRQ] inta fall count=43 pc=0xd861 sp=0xd6de db=0xcd osc=11768187 mcyc=1521961 vram=62885
[IRQ] inta fall count=44 pc=0xd861 sp=0xd6dd db=0xd4 osc=11768197 mcyc=1521962 vram=62885
[IRQ] inta fall count=45 pc=0xd861 sp=0xd6dd db=0xfe osc=11768203 mcyc=1521963 vram=62885
[IRQ] intr rise count=16 pc=0xd9dc sp=0xd6e7 osc=12128121 mcyc=1572721 vram=62885
[IRQ] inta fall count=46 pc=0xd9cc sp=0xd6e6 db=0xcd osc=12128133 mcyc=1572723 vram=62885
[IRQ] inta fall count=47 pc=0xd9cc sp=0xd6e5 db=0xd4 osc=12128143 mcyc=1572724 vram=62885
[IRQ] inta fall count=48 pc=0xd9cc sp=0xd6e5 db=0xfe osc=12128149 mcyc=1572725 vram=62885
[IRQ] intr rise count=17 pc=0xe5f2 sp=0xd6e0 osc=12507287 mcyc=1623482 vram=63085
[IRQ] inta fall count=49 pc=0xe5ef sp=0xd6e0 db=0xcd osc=12507299 mcyc=1623484 vram=63085
[IRQ] inta fall count=50 pc=0xe5ef sp=0xd6df db=0xd4 osc=12507309 mcyc=1623485 vram=63085
[IRQ] inta fall count=51 pc=0xe5ef sp=0xd6df db=0xfe osc=12507315 mcyc=1623486 vram=63085
[IRQ] intr rise count=18 pc=0xe5f3 sp=0xd6e0 osc=12887685 mcyc=1674243 vram=63085
[IRQ] inta fall count=52 pc=0xe5ef sp=0xd6e0 db=0xcd osc=12887691 mcyc=1674244 vram=63085
[IRQ] inta fall count=53 pc=0xe5ef sp=0xd6df db=0xd4 osc=12887701 mcyc=1674245 vram=63085
[IRQ] inta fall count=54 pc=0xe5ef sp=0xd6df db=0xfe osc=12887707 mcyc=1674246 vram=63085
[IRQ] intr rise count=19 pc=0xe5f3 sp=0xd6e0 osc=13268063 mcyc=1725004 vram=63085
[IRQ] inta fall count=55 pc=0xe5ef sp=0xd6e0 db=0xcd osc=13268069 mcyc=1725005 vram=63085
[IRQ] inta fall count=56 pc=0xe5ef sp=0xd6df db=0xd4 osc=13268079 mcyc=1725006 vram=63085
[IRQ] inta fall count=57 pc=0xe5ef sp=0xd6df db=0xfe osc=13268085 mcyc=1725007 vram=63085
[IRQ] intr rise count=20 pc=0xe5f2 sp=0xd6e0 osc=13648397 mcyc=1775765 vram=63085
[IRQ] inta fall count=58 pc=0xe5ef sp=0xd6e0 db=0xcd osc=13648409 mcyc=1775767 vram=63085
[IRQ] inta fall count=59 pc=0xe5ef sp=0xd6df db=0xd4 osc=13648419 mcyc=1775768 vram=63085
[IRQ] inta fall count=60 pc=0xe5ef sp=0xd6df db=0xfe osc=13648425 mcyc=1775769 vram=63085
[IRQ] intr rise count=21 pc=0xe5f1 sp=0xd6e0 osc=14028791 mcyc=1826526 vram=63085
[IRQ] inta fall count=61 pc=0xe5ef sp=0xd6e0 db=0xcd osc=14028811 mcyc=1826529 vram=63085
[IRQ] inta fall count=62 pc=0xe5ef sp=0xd6df db=0xd4 osc=14028821 mcyc=1826530 vram=63085
[IRQ] inta fall count=63 pc=0xe5ef sp=0xd6df db=0xfe osc=14028827 mcyc=1826531 vram=63085
[IRQ] intr rise count=22 pc=0xe5f3 sp=0xd6e0 osc=14409187 mcyc=1877287 vram=63085
[IRQ] inta fall count=64 pc=0xe5ef sp=0xd6e0 db=0xcd osc=14409193 mcyc=1877288 vram=63085
[IRQ] inta fall count=65 pc=0xe5ef sp=0xd6df db=0xd4 osc=14409203 mcyc=1877289 vram=63085
[IRQ] inta fall count=66 pc=0xe5ef sp=0xd6df db=0xfe osc=14409209 mcyc=1877290 vram=63085
[IRQ] intr rise count=23 pc=0xe5f2 sp=0xd6e0 osc=14789583 mcyc=1928048 vram=63085
[IRQ] inta fall count=67 pc=0xe5ef sp=0xd6e0 db=0xcd osc=14789595 mcyc=1928050 vram=63085
[IRQ] inta fall count=68 pc=0xe5ef sp=0xd6df db=0xd4 osc=14789605 mcyc=1928051 vram=63085
[IRQ] inta fall count=69 pc=0xe5ef sp=0xd6df db=0xfe osc=14789611 mcyc=1928052 vram=63085
[IRQ] intr rise count=24 pc=0xe5f0 sp=0xd6e0 osc=15169977 mcyc=1978809 vram=63085
[IRQ] inta fall count=70 pc=0xe5f0 sp=0xd6e0 db=0xcd osc=15169987 mcyc=1978810 vram=63085
[IRQ] inta fall count=71 pc=0xe5f0 sp=0xd6df db=0xd4 osc=15169997 mcyc=1978811 vram=63085
[IRQ] inta fall count=72 pc=0xe5f0 sp=0xd6df db=0xfe osc=15170003 mcyc=1978812 vram=63085
[IRQ] intr rise count=25 pc=0xe5f3 sp=0xd6e0 osc=15550373 mcyc=2029570 vram=63085
[IRQ] inta fall count=73 pc=0xe5ef sp=0xd6e0 db=0xcd osc=15550379 mcyc=2029571 vram=63085
[IRQ] inta fall count=74 pc=0xe5ef sp=0xd6df db=0xd4 osc=15550389 mcyc=2029572 vram=63085
[IRQ] inta fall count=75 pc=0xe5ef sp=0xd6df db=0xfe osc=15550395 mcyc=2029573 vram=63085
[IRQ] intr rise count=26 pc=0xe5f1 sp=0xd6e0 osc=15930771 mcyc=2080331 vram=63085
[IRQ] inta fall count=76 pc=0xe5ef sp=0xd6e0 db=0xcd osc=15930791 mcyc=2080334 vram=63085
[IRQ] inta fall count=77 pc=0xe5ef sp=0xd6df db=0xd4 osc=15930801 mcyc=2080335 vram=63085
[IRQ] inta fall count=78 pc=0xe5ef sp=0xd6df db=0xfe osc=15930807 mcyc=2080336 vram=63085
[IRQ] intr rise count=27 pc=0xe5f1 sp=0xd6e0 osc=16311235 mcyc=2131092 vram=63095
[IRQ] inta fall count=79 pc=0xe5ef sp=0xd6e0 db=0xcd osc=16311255 mcyc=2131095 vram=63095
[IRQ] inta fall count=80 pc=0xe5ef sp=0xd6df db=0xd4 osc=16311265 mcyc=2131096 vram=63095
[IRQ] inta fall count=81 pc=0xe5ef sp=0xd6df db=0xfe osc=16311271 mcyc=2131097 vram=63095
```

## FDC Trace

```text
[FDC] OUT port=0x1c reg=0 data=0x02 pc=0xe5de sp=0xd6de a=0x02 b=0x00 c=0xea d=0xd9 e=0x44 h=0x01 l=0xe5 mcyc=1590617 vram=63085 ios=1
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6dc a=0x02 b=0x00 c=0xea d=0xd9 e=0x44 h=0x01 l=0xe5 mcyc=1590635 vram=63085 ios=2
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6de a=0x05 b=0x00 c=0xea d=0xd9 e=0x44 h=0x01 l=0xe5 mcyc=1591253 vram=63085 ios=3
[FDC] OUT port=0x1c reg=0 data=0x02 pc=0xe604 sp=0xd6e0 a=0x02 b=0x00 c=0xea d=0x00 e=0x00 h=0x01 l=0xe5 mcyc=2136168 vram=63095 ios=4
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6de a=0x02 b=0x00 c=0xea d=0x00 e=0x00 h=0x01 l=0xe5 mcyc=2136186 vram=63095 ios=5
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6e6 a=0x02 b=0xe3 c=0xea d=0xd9 e=0x44 h=0x50 l=0x50 mcyc=2136463 vram=63095 ios=6
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe75e sp=0xd6e6 a=0x05 b=0x04 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137136 vram=63095 ios=7
[FDC] OUT port=0x1f reg=3 data=0x02 pc=0xe62d sp=0xd6e8 a=0x02 b=0x40 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137369 vram=63095 ios=8
[FDC] OUT port=0x1e reg=2 data=0x02 pc=0xe639 sp=0xd6e8 a=0x02 b=0x40 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137384 vram=63095 ios=9
[FDC] IN  port=0x1d reg=1 data=0x00 pc=0xe63f sp=0xd6e8 a=0x02 b=0x02 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137392 vram=63095 ios=10
[FDC] OUT port=0x1c reg=0 data=0x1a pc=0xe64d sp=0xd6e8 a=0x1a b=0x18 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137408 vram=63095 ios=11
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6e6 a=0x1a b=0x18 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137426 vram=63095 ios=12
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe75e sp=0xd6e6 a=0x02 b=0x18 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137678 vram=63095 ios=13
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6e6 a=0x00 b=0x18 c=0x00 d=0xd9 e=0x50 h=0x01 l=0xe5 mcyc=2137901 vram=63095 ios=14
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe771 sp=0xd6da a=0x11 b=0x00 c=0x02 d=0x02 e=0x14 h=0xb6 l=0x00 mcyc=2158652 vram=63095 ios=15
[FDC] IN  port=0x1c reg=0 data=0x00 pc=0xe75e sp=0xd6da a=0x05 b=0x04 c=0x00 d=0x02 e=0x50 h=0x01 l=0xe5 mcyc=2159325 vram=63095 ios=16
[FDC] OUT port=0x1f reg=3 data=0x00 pc=0xe62d sp=0xd6dc a=0x00 b=0x40 c=0x00 d=0x02 e=0x50 h=0x01 l=0xe5 mcyc=2159558 vram=63095 ios=17
[FDC] OUT port=0x1e reg=2 data=0x03 pc=0xe639 sp=0xd6dc a=0x03 b=0x40 c=0x00 d=0x02 e=0x50 h=0x01 l=0xe5 mcyc=2159573 vram=63095 ios=18
[FDC] IN  port=0x1d reg=1 data=0x02 pc=0xe63f sp=0xd6dc a=0x00 b=0x00 c=0x00 d=0x02 e=0x50 h=0x01 l=0xe5 mcyc=2159581 vram=63095 ios=19
[FDC] OUT port=0x1c reg=0 data=0x1a pc=0xe64d sp=0xd6dc a=0x1a b=0x18 c=0x00 d=0x02 e=0x50 h=0x01 l=0xe5 mcyc=2159597 vram=63095 ios=20
[FDC] stop ios=20 reads=12 writes=8 mcyc=2159597
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
