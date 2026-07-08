# juku_top checkpoint JBASIC probe

Status: **HDL EKDOS JBASIC KEYBOARD SAMPLING READY**

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
- Last key release: `[RESUME-KBD-STIM] release key=6 mcyc=73429 vram=73456`
- Keyboard hit lines: `222`
- Active-read key indices: `[0, 1, 2, 3, 4, 5, 6]`
- Non-`0xCF` key indices: `[0, 1, 2, 3, 4, 5, 6]`
- First keyboard hit: `[RESUME-KBD-HIT] active key=0 col=7 bit=5 shift=1 data=0x8f mcyc=298 vram=73446 pc=0x1463`
- Last keyboard hit: `[RESUME-KBD-HIT] active key=6 col=8 bit=5 shift=0 data=0xcf mcyc=68174 vram=73456 pc=0x128c`
- PPI0 non-keyboard trace lines: `3269`
- Keyboard column writes: `177`
- Keyboard Port B reads: `187`
- HDL M-cycle trace lines: `0`
- First HDL M-cycle trace: `none`
- Last HDL M-cycle trace: `none`
- READY stop line: `none`
- HDL VRAM dump size: `9640` (ok)
- Visible `A>JBASIC` command line at scanline 71: `no`
- Checkpoint command row bytes y=71 x=0..9: `08 10 00 00 00 00 00 00 00 00`
- HDL final command row bytes y=71 x=0..9: `08 10 3c ff 00 00 00 00 00 00`
- First changed VRAM cells: `x=3 y=70 00->ff, x=2 y=71 00->3c, x=3 y=71 00->ff, x=2 y=72 00->12, x=3 y=72 00->ff, x=2 y=73 00->12, x=3 y=73 00->ff, x=2 y=74 00->1c, x=3 y=74 00->ff, x=2 y=75 00->12, x=3 y=75 00->ff, x=2 y=76 00->12, x=3 y=76 00->ff, x=2 y=77 00->3c, x=3 y=77 00->ff, x=3 y=78 00->ff, x=3 y=79 00->ff`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xd7ef vram=73456 ios=786 pic_seen=0 kbd_seen=0 fdc_ios=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=100000 pc=0x0496 vram=73456 ios=3101 pic_seen=0 kbd_seen=1 fdc_ios=0 frame_ticks=8 intr_edges=8 inta_edges=24 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Stop/fail line: `JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0xff9b ios=3733 pic_seen=0 kbd_seen=1 ppi0_reads=1915 ppi0_writes=1718 kbd_col_writes=177 kbd_active_reads=119 kbd_noncf_reads=103 fdc_ios=0`

## Boundary

- The testbench now has opt-in `+jbasickeys=1` support for the exact
  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).
- The same bench also has `+stopjbasicready=1`, which checks the final
  `READY` prompt with exact fixed-`0xD800` glyph bytes.
- This report claims the checkpoint-resumed HDL keyboard-sampling
  boundary: the retimed command stimulus is read through PPI0 Port B
  with non-`0xCF` key data.
- The report also preserves the HDL framebuffer dump before restoring
  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`
  command glyphs at scanline 71.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first
  `N` resumed HDL M-cycle trace lines in this report.
- Next work is to continue from sampled command keys until post-command
  FDC/data traffic begins, then finally stop on `[RESUME-JBASIC]`.

## HDL stdout tail

```
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117208 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=117301 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=117307 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=117347 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117353 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=117446 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=117452 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=117492 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117498 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=117591 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=117597 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=117637 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117643 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=117736 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=117742 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=117782 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117788 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=117881 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=117887 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=117927 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=117933 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118026 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118032 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118072 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118078 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118171 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118177 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118217 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118223 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118316 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118322 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118362 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118368 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118461 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118467 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118507 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118513 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118606 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118612 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118652 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118658 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118751 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118757 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118797 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118803 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=118896 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=118902 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=118942 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=118948 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119041 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119047 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119087 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119093 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119186 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119192 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119232 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119238 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119331 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119337 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119377 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119383 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119476 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119482 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119522 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119528 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119621 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119627 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119667 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119673 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119766 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119772 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119812 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119818 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=119911 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=119917 vram=73466 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=119957 vram=73466 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=119963 vram=73466 pc=0xd7ef
JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0xff9b ios=3733 pic_seen=0 kbd_seen=1 ppi0_reads=1915 ppi0_writes=1718 kbd_col_writes=177 kbd_active_reads=119 kbd_noncf_reads=103 fdc_ios=0
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:414: $finish called at 170478200 (100ps)
```
