# juku_top checkpoint JBASIC probe

Status: **HDL EKDOS JBASIC READY**

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
- Keyboard/PPI tracing enabled: `no`
- JBASIC key presses: `0`
- JBASIC key releases: `0`
- First key press: `none`
- Last key release: `none`
- Keyboard hit lines: `0`
- Active-read key indices: `[]`
- Non-`0xCF` key indices: `[]`
- First keyboard hit: `none`
- Last keyboard hit: `none`
- PPI0 non-keyboard trace lines: `0`
- Keyboard column writes: `0`
- Keyboard Port B reads: `0`
- HDL M-cycle trace lines: `0`
- First HDL M-cycle trace: `none`
- Last HDL M-cycle trace: `none`
- READY stop line: `[RESUME-JBASIC] READY prompt reached mcyc=823184 vram=73925 pc=0x097a`
- FDC trace lines: `0`
- FDC stop line: `none`
- HDL VRAM dump size: `9640` (ok)
- Command echo line: `[RESUME-JBASIC-CMD] A>JBASIC command line reached mcyc=295243 vram=73525 pc=0x097a`
- Final visible `A>JBASIC` command line at scanline 71: `yes`
- Checkpoint command row bytes y=71 x=0..9: `08 10 00 00 00 00 00 00 00 00`
- HDL final command row bytes y=71 x=0..9: `08 10 0e 3c 08 1c 1c 1c 00 00`
- First changed VRAM cells: `x=2 y=71 00->0e, x=3 y=71 00->3c, x=4 y=71 00->08, x=5 y=71 00->1c, x=6 y=71 00->1c, x=7 y=71 00->1c, x=2 y=72 00->04, x=3 y=72 00->12, x=4 y=72 00->14, x=5 y=72 00->22, x=6 y=72 00->08, x=7 y=72 00->22, x=2 y=73 00->04, x=3 y=73 00->12, x=4 y=73 00->22, x=5 y=73 00->20, x=6 y=73 00->08, x=7 y=73 00->20, x=2 y=74 00->04, x=3 y=74 00->1c, x=4 y=74 00->22, x=5 y=74 00->1c, x=6 y=74 00->08, x=7 y=74 00->20`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xd9d4 vram=73456 ios=787 pic_seen=0 kbd_seen=1 fdc_ios=0 fdc_data_reads=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=800000 pc=0x097a vram=73769 ios=22783 pic_seen=0 kbd_seen=1 fdc_ios=9354 fdc_data_reads=9216 frame_ticks=73 intr_edges=59 inta_edges=177 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Stop/fail line: `none`

## Boundary

- The testbench now has opt-in `+jbasickeys=1` support for the exact
  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).
- The same bench also has `+stopjbasicready=1`, which checks the final
  `READY` prompt with exact fixed-`0xD800` glyph bytes.
- The default run now uses frame-scale key holds/gaps, `+stopfdc=0`,
  `+stopfdc_data_reads=0`, quiet keyboard/FDC tracing, and
  `+stopjbasicready=1` so the normal proof stops on the exact HDL
  `READY` glyph oracle.
- This report claims the checkpoint-resumed HDL BASIC prompt bridge:
  frame-scale command stimulus is read through PPI0 Port B, the full
  visible `A>JBASIC` command line is observed, disk-backed FDC data
  reads complete, and the fixed-`0xD800` `READY` glyph is rendered.
- The report also preserves the HDL framebuffer dump before restoring
  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`
  command glyphs at scanline 71.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first
  `N` resumed HDL M-cycle trace lines in this report.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_KBD=1` and
  `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_FDC=1` for detailed retiming
  experiments; leave them quiet for the default READY proof.
- Set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_DATA_READS=N` to recover bounded
  FDC-transfer checkpoints such as the 4096- and 8192-read windows.
- This run did reach the HDL `READY` oracle; promote the report status and CI gate.
- This run did echo the full HDL `A>JBASIC` command line; the next boundary is Return execution and FDC traffic.

## HDL stdout tail

```
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=627064 vram=73536 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=627102 vram=73536 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=627834 vram=73536 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=636558 vram=73536 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=636750 vram=73536 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=637216 vram=73536 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=644338 vram=73536 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=648345 vram=73536 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=648383 vram=73536 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=649305 vram=73546 pc=0xd820
[RESUME-PROGRESS] mcyc=650000 pc=0xc5ec vram=73546 ios=19130 pic_seen=0 kbd_seen=1 fdc_ios=6755 fdc_data_reads=6656 frame_ticks=59 intr_edges=49 inta_edges=147 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=656042 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=656234 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=659099 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=659137 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=659869 vram=73546 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=669850 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=669888 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=670620 vram=73546 pc=0xd820
[RESUME-PROGRESS] mcyc=675000 pc=0xe76d vram=73546 ios=19288 pic_seen=0 kbd_seen=1 fdc_ios=6764 fdc_data_reads=6656 frame_ticks=61 intr_edges=51 inta_edges=153 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=679548 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=686670 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=691198 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=691236 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=691968 vram=73546 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=698176 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=698368 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=698834 vram=73546 pc=0x068b
[RESUME-PROGRESS] mcyc=700000 pc=0xe5ab vram=73546 ios=19989 pic_seen=0 kbd_seen=1 fdc_ios=7368 fdc_data_reads=7252 frame_ticks=63 intr_edges=52 inta_edges=156 intr=0 pending=0 inta_idx=0 mask=0xff inte=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=705956 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=712481 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=712519 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=713251 vram=73546 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=717462 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=717654 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=718120 vram=73546 pc=0x068b
[RESUME-PROGRESS] mcyc=725000 pc=0xe76b vram=73546 ios=21029 pic_seen=0 kbd_seen=1 fdc_ios=8316 fdc_data_reads=8192 frame_ticks=66 intr_edges=53 inta_edges=159 intr=0 pending=0 inta_idx=0 mask=0xff inte=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=725242 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=733791 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=733829 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=734561 vram=73546 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=736748 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=736940 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=737406 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=744528 vram=73546 pc=0x068b
[RESUME-PROGRESS] mcyc=750000 pc=0xe932 vram=73546 ios=21645 pic_seen=0 kbd_seen=1 fdc_ios=8835 fdc_data_reads=8704 frame_ticks=68 intr_edges=54 inta_edges=162 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=755164 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=755202 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=755934 vram=73546 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=756034 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=756226 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=756692 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=763814 vram=73546 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=765842 vram=73546 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=765880 vram=73546 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=766612 vram=73546 pc=0xd820
[RESUME-PROGRESS] mcyc=775000 pc=0xcd1e vram=73576 ios=22386 pic_seen=0 kbd_seen=1 fdc_ios=9354 fdc_data_reads=9216 frame_ticks=70 intr_edges=56 inta_edges=168 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=776791 vram=73592 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=776829 vram=73592 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=777561 vram=73592 pc=0xd820
[RESUME-VRAM] writes=73600 mcyc=778598 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=787735 vram=73676 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=787773 vram=73676 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=788505 vram=73676 pc=0xd820
[RESUME-VRAM] writes=73700 mcyc=791680 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=798635 vram=73766 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=798673 vram=73766 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=799405 vram=73766 pc=0xd820
[RESUME-PROGRESS] mcyc=800000 pc=0x097a vram=73769 ios=22783 pic_seen=0 kbd_seen=1 fdc_ios=9354 fdc_data_reads=9216 frame_ticks=73 intr_edges=59 inta_edges=177 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-VRAM] writes=73800 mcyc=803187 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=809541 vram=73856 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=809579 vram=73856 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=810311 vram=73856 pc=0xd820
[RESUME-VRAM] writes=73900 mcyc=819702 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=820519 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=820557 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=821289 vram=73906 pc=0xd820
[RESUME-JBASIC] READY prompt reached mcyc=823184 vram=73925 pc=0x097a
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:638: $finish called at 1204025200 (100ps)
```
