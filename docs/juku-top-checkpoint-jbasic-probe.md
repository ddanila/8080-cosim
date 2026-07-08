# juku_top checkpoint JBASIC probe

Status: **HDL EKDOS JBASIC COMMAND STIMULUS READY**

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
- Cosim checkpoint keyboard position/phase: `4` / `0`
- HDL resume exit code: `0`
- Timed out: `no`
- JBASIC key presses: `7`
- JBASIC key releases: `7`
- First key press: `[RESUME-KBD-STIM] press key=0 col=7 bit=5 shift=1 mcyc=50000 vram=73446`
- Last key release: `[RESUME-KBD-STIM] release key=6 mcyc=62500 vram=73446`
- Keyboard hit lines: `0`
- First keyboard hit: `none`
- Last keyboard hit: `none`
- PPI0 non-keyboard trace lines: `10`
- Keyboard column writes: `0`
- Keyboard Port B reads: `0`
- READY stop line: `none`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0x627a vram=73446 ios=1 pic_seen=0 kbd_seen=0 fdc_ios=0 frame_ticks=2 intr_edges=1 inta_edges=1 intr=1 pending=1 inta_idx=1 mask=0xdf inte=0`
- Last progress line: `[RESUME-PROGRESS] mcyc=75000 pc=0x7c60 vram=73446 ios=14 pic_seen=0 kbd_seen=0 fdc_ios=1 frame_ticks=7 intr_edges=2 inta_edges=4 intr=1 pending=1 inta_idx=1 mask=0xdf inte=0`
- Stop/fail line: `JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0xbf51 ios=14 pic_seen=0 kbd_seen=0 ppi0_reads=5 ppi0_writes=5 kbd_col_writes=0 kbd_active_reads=0 kbd_noncf_reads=0 fdc_ios=1`

## Boundary

- The testbench now has opt-in `+jbasickeys=1` support for the exact
  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).
- The same bench also has `+stopjbasicready=1`, which checks the final
  `READY` prompt with exact fixed-`0xD800` glyph bytes.
- This report only claims the checkpoint-resumed HDL command stimulus
  boundary. The tracked run is intentionally short and stops before
  the HDL path samples the injected keys or reaches the `READY` oracle.
- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key
  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`
  to stop at the first sampled keyboard hit during retiming experiments.
- Next work is to lengthen or retime the resumed HDL run until keyboard
  reads sample the injected command and post-command FDC/data traffic
  begins, then finally stop on `[RESUME-JBASIC]`.

## HDL stdout tail

```
FDC-1793: loaded raw disk media/disks/JUKPROG2.CPM (2 sides)
[RESUME] loaded checkpoint pc=0xfed4 sp=0xd2f4 inta_n=1 sys_status=0x00 core_inta=0 core_minta=0 core_intr=0 inte=0 intr=0
[RESUME-PROGRESS] mcyc=25000 pc=0x627a vram=73446 ios=1 pic_seen=0 kbd_seen=0 fdc_ios=0 frame_ticks=2 intr_edges=1 inta_edges=1 intr=1 pending=1 inta_idx=1 mask=0xdf inte=0
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=48177 vram=73446 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=48183 vram=73446 pc=0xd7ef
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=48239 vram=73446 pc=0x068b
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=48256 vram=73446 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=48262 vram=73446 pc=0xd7ef
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=48281 vram=73446 pc=0xe786
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=48287 vram=73446 pc=0xe78b
[RESUME-PPI0] IN port=0x06 data=0x05 mcyc=48365 vram=73446 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x04 mcyc=48371 vram=73446 pc=0xd7ef
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=48431 vram=73446 pc=0x068b
[RESUME-PPI0] IN port=0x06 data=0x04 mcyc=48448 vram=73446 pc=0xd7ea
[RESUME-PPI0] OUT port=0x06 data=0x05 mcyc=48454 vram=73446 pc=0xd7ef
[RESUME-KBD-STIM] press key=0 col=7 bit=5 shift=1 mcyc=50000 vram=73446
[RESUME-PROGRESS] mcyc=50000 pc=0x1ab8 vram=73446 ios=14 pic_seen=0 kbd_seen=0 fdc_ios=1 frame_ticks=4 intr_edges=1 inta_edges=4 intr=0 pending=0 inta_idx=1 mask=0xdf inte=0
[RESUME-KBD-STIM] release key=0 mcyc=51250 vram=73446
[RESUME-KBD-STIM] press key=1 col=4 bit=1 shift=1 mcyc=51875 vram=73446
[RESUME-KBD-STIM] release key=1 mcyc=53125 vram=73446
[RESUME-KBD-STIM] press key=2 col=5 bit=5 shift=1 mcyc=53750 vram=73446
[RESUME-KBD-STIM] release key=2 mcyc=55000 vram=73446
[RESUME-KBD-STIM] press key=3 col=1 bit=5 shift=1 mcyc=55625 vram=73446
[RESUME-KBD-STIM] release key=3 mcyc=56875 vram=73446
[RESUME-KBD-STIM] press key=4 col=14 bit=3 shift=1 mcyc=57500 vram=73446
[RESUME-KBD-STIM] release key=4 mcyc=58750 vram=73446
[RESUME-KBD-STIM] press key=5 col=6 bit=1 shift=1 mcyc=59375 vram=73446
[RESUME-KBD-STIM] release key=5 mcyc=60625 vram=73446
[RESUME-KBD-STIM] press key=6 col=8 bit=5 shift=0 mcyc=61250 vram=73446
[RESUME-KBD-STIM] release key=6 mcyc=62500 vram=73446
[RESUME-PROGRESS] mcyc=75000 pc=0x7c60 vram=73446 ios=14 pic_seen=0 kbd_seen=0 fdc_ios=1 frame_ticks=7 intr_edges=2 inta_edges=4 intr=1 pending=1 inta_idx=1 mask=0xdf inte=0
JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0xbf51 ios=14 pic_seen=0 kbd_seen=0 ppi0_reads=5 ppi0_writes=5 kbd_col_writes=0 kbd_active_reads=0 kbd_noncf_reads=0 fdc_ios=1
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:411: $finish called at 143569000 (100ps)
```
