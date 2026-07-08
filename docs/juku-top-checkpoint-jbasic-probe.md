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
- PPI0 non-keyboard trace lines: `9499`
- Keyboard column writes: `521`
- Keyboard Port B reads: `544`
- HDL M-cycle trace lines: `0`
- First HDL M-cycle trace: `none`
- Last HDL M-cycle trace: `none`
- READY stop line: `none`
- FDC trace lines: `519`
- FDC stop line: `[RESUME-FDC] stop reason=data-read-count target=512 ios=518 reads=515 data_reads=512 writes=3 data=0x00 mcyc=361757 vram=73526`
- HDL VRAM dump size: `9640` (ok)
- Visible `A>JBASIC` command line at scanline 71: `yes`
- Checkpoint command row bytes y=71 x=0..9: `08 10 00 00 00 00 00 00 00 00`
- HDL final command row bytes y=71 x=0..9: `08 10 0e 3c 08 1c 1c 1c 00 00`
- First changed VRAM cells: `x=2 y=71 00->0e, x=3 y=71 00->3c, x=4 y=71 00->08, x=5 y=71 00->1c, x=6 y=71 00->1c, x=7 y=71 00->1c, x=2 y=72 00->04, x=3 y=72 00->12, x=4 y=72 00->14, x=5 y=72 00->22, x=6 y=72 00->08, x=7 y=72 00->22, x=2 y=73 00->04, x=3 y=73 00->12, x=4 y=73 00->22, x=5 y=73 00->20, x=6 y=73 00->08, x=7 y=73 00->20, x=2 y=74 00->04, x=3 y=74 00->1c, x=4 y=74 00->22, x=5 y=74 00->1c, x=6 y=74 00->08, x=7 y=74 00->20`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xd9d4 vram=73456 ios=787 pic_seen=0 kbd_seen=1 fdc_ios=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=350000 pc=0x13f9 vram=73526 ios=10811 pic_seen=0 kbd_seen=1 fdc_ios=0 frame_ticks=31 intr_edges=31 inta_edges=93 intr=0 pending=0 inta_idx=0 mask=0xff inte=1`
- Stop/fail line: `none`

## Boundary

- The testbench now has opt-in `+jbasickeys=1` support for the exact
  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).
- The same bench also has `+stopjbasicready=1`, which checks the final
  `READY` prompt with exact fixed-`0xD800` glyph bytes.
- The default run now uses frame-scale key holds/gaps, `+stopfdc=0`,
  and `+stopfdc_data_reads=512` so a full 512-byte data-register
  window is a bounded HDL stop condition.
- This report claims the checkpoint-resumed HDL FDC data-read
  boundary: frame-scale command stimulus is read through PPI0 Port B,
  the full `A>JBASIC` command line is visible, and 512 decoded FDC
  data-register reads complete.
- The report also preserves the HDL framebuffer dump before restoring
  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`
  command glyphs at scanline 71.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first
  `N` resumed HDL M-cycle trace lines in this report.
- Next work is to continue from the 512-byte FDC data-read window
  through the full disk transfer and finally stop on `[RESUME-JBASIC]`.
- This run reached HDL FDC data-register reads; next work is to continue through the disk transfer and the `READY` oracle.

## HDL stdout tail

```
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360769 vram=73526 ios=442
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360782 vram=73526 ios=443
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360795 vram=73526 ios=444
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360808 vram=73526 ios=445
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360821 vram=73526 ios=446
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360834 vram=73526 ios=447
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360847 vram=73526 ios=448
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360860 vram=73526 ios=449
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360873 vram=73526 ios=450
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360886 vram=73526 ios=451
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360899 vram=73526 ios=452
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360912 vram=73526 ios=453
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360925 vram=73526 ios=454
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360938 vram=73526 ios=455
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360951 vram=73526 ios=456
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360964 vram=73526 ios=457
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360977 vram=73526 ios=458
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=360990 vram=73526 ios=459
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361003 vram=73526 ios=460
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361016 vram=73526 ios=461
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361029 vram=73526 ios=462
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361042 vram=73526 ios=463
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361055 vram=73526 ios=464
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361068 vram=73526 ios=465
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361081 vram=73526 ios=466
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361094 vram=73526 ios=467
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361107 vram=73526 ios=468
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361120 vram=73526 ios=469
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361133 vram=73526 ios=470
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361146 vram=73526 ios=471
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361159 vram=73526 ios=472
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361172 vram=73526 ios=473
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361185 vram=73526 ios=474
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361198 vram=73526 ios=475
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361211 vram=73526 ios=476
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361224 vram=73526 ios=477
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361237 vram=73526 ios=478
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361250 vram=73526 ios=479
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361263 vram=73526 ios=480
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361276 vram=73526 ios=481
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361289 vram=73526 ios=482
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361302 vram=73526 ios=483
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361315 vram=73526 ios=484
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361328 vram=73526 ios=485
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361341 vram=73526 ios=486
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361354 vram=73526 ios=487
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361367 vram=73526 ios=488
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361380 vram=73526 ios=489
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361393 vram=73526 ios=490
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361406 vram=73526 ios=491
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361419 vram=73526 ios=492
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361432 vram=73526 ios=493
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361445 vram=73526 ios=494
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361458 vram=73526 ios=495
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361471 vram=73526 ios=496
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361484 vram=73526 ios=497
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361497 vram=73526 ios=498
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361510 vram=73526 ios=499
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361523 vram=73526 ios=500
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361536 vram=73526 ios=501
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361549 vram=73526 ios=502
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361562 vram=73526 ios=503
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361575 vram=73526 ios=504
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361588 vram=73526 ios=505
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361601 vram=73526 ios=506
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361614 vram=73526 ios=507
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361627 vram=73526 ios=508
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361640 vram=73526 ios=509
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361653 vram=73526 ios=510
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361666 vram=73526 ios=511
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361679 vram=73526 ios=512
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361692 vram=73526 ios=513
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361705 vram=73526 ios=514
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361718 vram=73526 ios=515
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361731 vram=73526 ios=516
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361744 vram=73526 ios=517
[RESUME-FDC] IN  port=0x1f reg=3 data=0x00 mcyc=361757 vram=73526 ios=518
[RESUME-FDC] stop reason=data-read-count target=512 ios=518 reads=515 data_reads=512 writes=3 data=0x00 mcyc=361757 vram=73526
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:625: $finish called at 514655010 (100ps)
```
