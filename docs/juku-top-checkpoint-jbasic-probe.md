# juku_top checkpoint JBASIC probe

Status: **HDL EKDOS JBASIC FDC DATA READ READY**

This diagnostic starts from a generated cosim EKDOS `A>` prompt
checkpoint on `media/disks/JUKPROG2.CPM`, loads that RAM/state into
`juku_top`, and injects the fixed `JBASIC` + Enter command through the
checkpoint-resume keyboard path. It is the first HDL-side bridge from
the now-pinned cosim `JBASIC` READY oracle toward a full HDL BASIC
prompt proof.

## Command

```sh
sync/juku_top_checkpoint_jbasic_probe.py
```

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `14200002`
- Cosim checkpoint VRAM writes: `73446`
- Cosim checkpoint PC: `0xFED4`
- HDL checkpoint PC bias: `-1`
- Cosim checkpoint keyboard position/phase: `4` / `0`
- HDL resume exit code: `0`
- Timed out: `no`
- JBASIC key presses: `7`
- JBASIC key releases: `7`
- First key press: `[RESUME-KBD-STIM] press key=0 col=7 bit=5 shift=1 mcyc=250 vram=73446`
- Last key release: `[RESUME-KBD-STIM] release key=6 mcyc=360249 vram=73526`
- Keyboard hit lines: `444`
- Active-read key indices: `[0, 1, 2, 3, 4, 5, 6]`
- Non-`0xCF` key indices: `[0, 1, 2, 3, 4, 5, 6]`
- First keyboard hit: `[RESUME-KBD-HIT] active key=0 col=7 bit=5 shift=1 data=0x8f mcyc=298 vram=73446 pc=0x1463`
- Last keyboard hit: `[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349812 vram=73526 pc=0x128c`
- PPI0 non-keyboard trace lines: `9884`
- Keyboard column writes: `695`
- Keyboard Port B reads: `714`
- HDL M-cycle trace lines: `0`
- First HDL M-cycle trace: `none`
- Last HDL M-cycle trace: `none`
- READY stop line: `none`
- FDC trace lines: `4152`
- FDC stop line: `[RESUME-FDC] stop reason=data-read-count target=4096 ios=4151 reads=4127 data_reads=4096 writes=24 data=0xe5 mcyc=538973 vram=73536`
- HDL VRAM dump size: `9640` (ok)
- Command echo line: `[RESUME-JBASIC-CMD] A>JBASIC command line reached mcyc=295243 vram=73525 pc=0x097a`
- Final visible `A>JBASIC` command line at scanline 71: `no`
- Checkpoint command row bytes y=71 x=0..9: `08 10 00 00 00 00 00 00 00 00`
- HDL final command row bytes y=71 x=0..9: `f7 10 0e 3c 08 1c 1c 1c 00 00`
- First changed VRAM cells: `x=0 y=70 00->ff, x=0 y=71 08->f7, x=2 y=71 00->0e, x=3 y=71 00->3c, x=4 y=71 00->08, x=5 y=71 00->1c, x=6 y=71 00->1c, x=7 y=71 00->1c, x=0 y=72 14->eb, x=2 y=72 00->04, x=3 y=72 00->12, x=4 y=72 00->14, x=5 y=72 00->22, x=6 y=72 00->08, x=7 y=72 00->22, x=0 y=73 22->dd, x=2 y=73 00->04, x=3 y=73 00->12, x=4 y=73 00->22, x=5 y=73 00->20, x=6 y=73 00->08, x=7 y=73 00->20, x=0 y=74 22->dd, x=2 y=74 00->04`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xd9d4 vram=73456 ios=787 pic_seen=0 kbd_seen=1 fdc_ios=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=525000 pc=0xc349 vram=73536 ios=15255 pic_seen=0 kbd_seen=1 fdc_ios=3633 frame_ticks=47 intr_edges=40 inta_edges=120 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Stop/fail line: `none`

## Boundary

- The testbench now has opt-in `+jbasickeys=1` support for the exact
  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).
- The same bench also has `+stopjbasicready=1`, which checks the final
  `READY` prompt with exact fixed-`0xD800` glyph bytes.
- The default run now uses frame-scale key holds/gaps, `+stopfdc=0`,
  and `+stopfdc_data_reads=4096` so eight full 512-byte data-register
  windows are a bounded HDL stop condition.
- This report claims the checkpoint-resumed HDL FDC data-read
  boundary: frame-scale command stimulus is read through PPI0 Port B,
  the full `A>JBASIC` command line is observed by the bench-side
  oracle, and 4096 decoded FDC data-register reads complete.
- The report also preserves the HDL framebuffer dump before restoring
  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`
  command glyphs at scanline 71.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first
  `N` resumed HDL M-cycle trace lines in this report.
- Next work is to continue from the 4096-byte FDC data-read window
  through the full disk transfer and finally stop on `[RESUME-JBASIC]`.
- This run reached HDL FDC data-register reads; next work is to continue through the disk transfer and the `READY` oracle.

## HDL stdout tail

```
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=537985 vram=73536 ios=4075
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=537998 vram=73536 ios=4076
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538011 vram=73536 ios=4077
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538024 vram=73536 ios=4078
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538037 vram=73536 ios=4079
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538050 vram=73536 ios=4080
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538063 vram=73536 ios=4081
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538076 vram=73536 ios=4082
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538089 vram=73536 ios=4083
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538102 vram=73536 ios=4084
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538115 vram=73536 ios=4085
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538128 vram=73536 ios=4086
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538141 vram=73536 ios=4087
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538154 vram=73536 ios=4088
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538167 vram=73536 ios=4089
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538180 vram=73536 ios=4090
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538193 vram=73536 ios=4091
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538206 vram=73536 ios=4092
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538219 vram=73536 ios=4093
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538232 vram=73536 ios=4094
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538245 vram=73536 ios=4095
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538258 vram=73536 ios=4096
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538271 vram=73536 ios=4097
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538284 vram=73536 ios=4098
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538297 vram=73536 ios=4099
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538310 vram=73536 ios=4100
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538323 vram=73536 ios=4101
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538336 vram=73536 ios=4102
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538349 vram=73536 ios=4103
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538362 vram=73536 ios=4104
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538375 vram=73536 ios=4105
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538388 vram=73536 ios=4106
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538401 vram=73536 ios=4107
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538414 vram=73536 ios=4108
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538427 vram=73536 ios=4109
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538440 vram=73536 ios=4110
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538453 vram=73536 ios=4111
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538466 vram=73536 ios=4112
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538479 vram=73536 ios=4113
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538492 vram=73536 ios=4114
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538505 vram=73536 ios=4115
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538518 vram=73536 ios=4116
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538531 vram=73536 ios=4117
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538544 vram=73536 ios=4118
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538557 vram=73536 ios=4119
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538570 vram=73536 ios=4120
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538583 vram=73536 ios=4121
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538596 vram=73536 ios=4122
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538609 vram=73536 ios=4123
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538622 vram=73536 ios=4124
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538635 vram=73536 ios=4125
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538648 vram=73536 ios=4126
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538661 vram=73536 ios=4127
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538674 vram=73536 ios=4128
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538687 vram=73536 ios=4129
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538700 vram=73536 ios=4130
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538713 vram=73536 ios=4131
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538726 vram=73536 ios=4132
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538739 vram=73536 ios=4133
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538752 vram=73536 ios=4134
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538765 vram=73536 ios=4135
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538778 vram=73536 ios=4136
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538791 vram=73536 ios=4137
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538804 vram=73536 ios=4138
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538817 vram=73536 ios=4139
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538830 vram=73536 ios=4140
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538843 vram=73536 ios=4141
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538856 vram=73536 ios=4142
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538869 vram=73536 ios=4143
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538882 vram=73536 ios=4144
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538895 vram=73536 ios=4145
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538908 vram=73536 ios=4146
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538921 vram=73536 ios=4147
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538934 vram=73536 ios=4148
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538947 vram=73536 ios=4149
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538960 vram=73536 ios=4150
[RESUME-FDC] IN  port=0x1f reg=3 data=0xe5 mcyc=538973 vram=73536 ios=4151
[RESUME-FDC] stop reason=data-read-count target=4096 ios=4151 reads=4127 data_reads=4096 writes=24 data=0xe5 mcyc=538973 vram=73536
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:741: $finish called at 779854210 (100ps)
```
