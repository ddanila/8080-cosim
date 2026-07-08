# juku_top checkpoint JBASIC probe

Status: **HDL EKDOS JBASIC POST-COMMAND FDC READY**

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
- JBASIC key releases: `6`
- First key press: `[RESUME-KBD-STIM] press key=0 col=7 bit=5 shift=1 mcyc=250 vram=73446`
- Last key release: `[RESUME-KBD-STIM] release key=5 mcyc=304322 vram=73526`
- Keyboard hit lines: `444`
- Active-read key indices: `[0, 1, 2, 3, 4, 5, 6]`
- Non-`0xCF` key indices: `[0, 1, 2, 3, 4, 5, 6]`
- First keyboard hit: `[RESUME-KBD-HIT] active key=0 col=7 bit=5 shift=1 data=0x8f mcyc=298 vram=73446 pc=0x1463`
- Last keyboard hit: `[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349812 vram=73526 pc=0x128c`
- PPI0 non-keyboard trace lines: `9484`
- Keyboard column writes: `519`
- Keyboard Port B reads: `544`
- HDL M-cycle trace lines: `0`
- First HDL M-cycle trace: `none`
- Last HDL M-cycle trace: `none`
- READY stop line: `none`
- FDC trace lines: `2`
- FDC stop line: `[RESUME-FDC] stop ios=1 reads=1 writes=0 mcyc=353942 vram=73526`
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
- The default run now uses frame-scale key holds/gaps and `+stopfdc=1`
  so post-command disk traffic becomes a bounded HDL stop condition.
- This report claims the checkpoint-resumed HDL post-command FDC
  boundary: frame-scale command stimulus is read through PPI0 Port B,
  the full `A>JBASIC` command line is visible, and decoded FDC I/O starts.
- The report also preserves the HDL framebuffer dump before restoring
  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`
  command glyphs at scanline 71.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first
  `N` resumed HDL M-cycle trace lines in this report.
- Next work is to continue from first post-command FDC I/O through FDC
  data reads and finally stop on `[RESUME-JBASIC]`.
- This run reached post-command HDL FDC I/O; next work is to continue through FDC data reads and the `READY` oracle.

## HDL stdout tail

```
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349567 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349567 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x0b mcyc=349579 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0xa data=0x0a mcyc=349584 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349587 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349587 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x0a mcyc=349599 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x9 data=0x09 mcyc=349604 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349607 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349607 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x09 mcyc=349619 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x8 data=0x08 mcyc=349624 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xc4 mcyc=349627 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xc4 mcyc=349627 vram=73526 pc=0x1463
[RESUME-KBD-HIT] noncf key=6 col=8 bit=5 shift=0 data=0xc4 mcyc=349627 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x08 mcyc=349650 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x7 data=0x07 mcyc=349655 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349658 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349658 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x07 mcyc=349670 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x6 data=0x06 mcyc=349675 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349678 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349678 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x06 mcyc=349690 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x5 data=0x05 mcyc=349695 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349698 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349698 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x05 mcyc=349710 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x4 data=0x04 mcyc=349715 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349718 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349718 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x04 mcyc=349730 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x3 data=0x03 mcyc=349735 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349738 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349738 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x03 mcyc=349750 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x2 data=0x02 mcyc=349755 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349758 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349758 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x02 mcyc=349770 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x1 data=0x01 mcyc=349775 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349778 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349778 vram=73526 pc=0x1463
[RESUME-PPI0] IN port=0x04 data=0x01 mcyc=349790 vram=73526 pc=0x145d
[RESUME-KBD] OUT port=0x04 col=0x0 data=0x00 mcyc=349795 vram=73526 pc=0x1461
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349798 vram=73526 pc=0x1463
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349798 vram=73526 pc=0x1463
[RESUME-KBD] IN port=0x05 data=0xcf mcyc=349812 vram=73526 pc=0x128c
[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=349812 vram=73526 pc=0x128c
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=349875 vram=73526 pc=0x0520
[RESUME-PPI0] OUT port=0x07 data=0x0e mcyc=349881 vram=73526 pc=0x0525
[RESUME-PROGRESS] mcyc=350000 pc=0x13f9 vram=73526 ios=10811 pic_seen=0 kbd_seen=1 fdc_ios=0 frame_ticks=31 intr_edges=31 inta_edges=93 intr=0 pending=0 inta_idx=0 mask=0xff inte=1
[RESUME-PPI0] IN port=0x04 data=0x00 mcyc=350060 vram=73526 pc=0x126c
[RESUME-KBD] OUT port=0x04 col=0x0 data=0x00 mcyc=350065 vram=73526 pc=0x1270
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=350266 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=350272 vram=73526 pc=0xd7ef
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=350310 vram=73526 pc=0xd820
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=350340 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=350346 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=350388 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=350394 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=350430 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=350436 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=350512 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=350518 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=350592 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=350598 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=350801 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=350807 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=350847 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=350853 vram=73526 pc=0xd7ef
[RESUME-PPI0] OUT port=0x07 data=0x0e mcyc=350983 vram=73526 pc=0xdcd5
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=351093 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=351099 vram=73526 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=351287 vram=73526 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=351293 vram=73526 pc=0xd7ef
[RESUME-FDC] IN  port=0x1c reg=0 data=0x00 mcyc=353942 vram=73526 ios=1
[RESUME-FDC] stop ios=1 reads=1 writes=0 mcyc=353942 vram=73526
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:637: $finish called at 502935410 (100ps)
```
