# juku_top checkpoint JBASIC late probe

Status: **HDL EKDOS JBASIC MID FDC DRAIN READY**

This diagnostic starts from a generated cosim EKDOS `JBASIC` checkpoint
after `17408` total WD1793 data-register reads on
`media/disks/JUKPROG2.CPM`. The command is already entered in the
checkpoint, so the HDL resume runs with no keyboard stimulus.
This run stops after `10752` additional HDL FDC data-register
reads, preserving a bounded mid-transfer bridge between the prompt
checkpoint and the final BASIC prompt checkpoint.

## Command

```sh
JUKU_TOP_CHECKPOINT_JBASIC_LATE_FDC_READS=17408 JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READS=10752 JUKU_TOP_CHECKPOINT_JBASIC_LATE_REPORT=docs/juku-top-checkpoint-jbasic-mid-probe.md sync/juku_top_checkpoint_jbasic_late_probe.py
```

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `32262928`
- Cosim checkpoint VRAM writes: `73586`
- Cosim checkpoint PC: `0xE5AA`
- Cosim checkpoint keyboard position/phase: `10` / `6`
- Cosim checkpoint FDC data reads: `17408`
- Cosim checkpoint FDC track/sector/data/status: `13` / `0A` / `01` / `00`
- HDL checkpoint PC bias: `0`
- HDL resume exit code: `0`
- Timed out: `no`
- READY stop line: `none`
- FDC stop line: `[RESUME-FDC] stop reason=data-read-count target=10752 ios=10908 reads=10843 data_reads=10752 writes=65 data=0xe5 mcyc=922973 vram=73916`
- HDL final visible `READY` at scanline 121: `no`
- HDL final visible `A>JBASIC` command line at scanline 71: `yes`
- HDL final VRAM size: `9640` (ok)
- HDL final VRAM SHA256: `0df1d730144030cdaaa73ed21e4a8750f78097e24873fb2498366e76f7a6c2b1`
- Checkpoint READY row bytes y=121 x=0..9: `00 00 00 00 00 00 00 00 00 00`
- HDL final READY row bytes y=121 x=0..9: `00 00 00 00 00 00 00 00 00 00`
- First changed VRAM cells: `x=0 y=1 3e->1c, x=1 y=1 1c->3c, x=2 y=1 22->3e, x=3 y=1 00->3c, x=4 y=1 3e->1c, x=5 y=1 22->00, x=6 y=1 3c->3e, x=7 y=1 1c->3c, x=9 y=1 00->22, x=10 y=1 1c->00, x=11 y=1 00->1c, x=13 y=1 1c->08, x=14 y=1 00->3c, x=15 y=1 00->3e, x=0 y=2 20->22, x=2 y=2 24->20, x=3 y=2 00->12, x=4 y=2 20->22, x=5 y=2 24->00, x=6 y=2 12->20, x=9 y=2 00->36, x=10 y=2 22->00, x=11 y=2 00->22, x=12 y=2 02->08`
- FDC trace lines: `1`
- Last observed HDL progress FDC data reads: `10240`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xe76d vram=73586 ios=166 pic_seen=0 kbd_seen=1 fdc_ios=10 fdc_data_reads=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=900000 pc=0xe935 vram=73916 ios=15838 pic_seen=0 kbd_seen=1 fdc_ios=10390 fdc_data_reads=10240 frame_ticks=85 intr_edges=68 inta_edges=204 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Stop/fail line: `none`

## Boundary

- This is a checkpoint-resumed proof, not a replacement for the
  prompt-checkpoint command-stimulus report.
- The prompt-checkpoint report still owns the early HDL path: `JBASIC`
  key sampling, command echo, and the first 4,096 post-command FDC data
  reads.
- This mid-transfer run proves that a later `JBASIC` checkpoint can
  drain `10752` additional decoded FDC data-register reads
  under checkpoint-resumed `juku_top` execution.
- The open gap remains the uninterrupted HDL bridge from the prompt
  checkpoint through the later transfer checkpoints and then into
  the final `READY` renderer.

## HDL stdout tail

```
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=723663 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=723701 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=724433 vram=73906 pc=0xd820
[RESUME-PROGRESS] mcyc=725000 pc=0xcd9a vram=73906 ios=11770 pic_seen=0 kbd_seen=1 fdc_ios=7276 fdc_data_reads=7168 frame_ticks=69 intr_edges=56 inta_edges=168 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=725826 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=726018 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=726484 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=733606 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=734393 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=734431 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=735163 vram=73906 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=745115 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=745153 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=745885 vram=73906 pc=0xd820
[RESUME-PROGRESS] mcyc=750000 pc=0xc260 vram=73906 ios=12448 pic_seen=0 kbd_seen=1 fdc_ios=7795 fdc_data_reads=7680 frame_ticks=71 intr_edges=58 inta_edges=174 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=755838 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=755876 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=756608 vram=73906 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=766621 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=766659 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=767391 vram=73906 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=771163 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=771355 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=771821 vram=73906 pc=0x068b
[RESUME-PROGRESS] mcyc=775000 pc=0xe5aa vram=73906 ios=12846 pic_seen=0 kbd_seen=1 fdc_ios=8039 fdc_data_reads=7918 frame_ticks=73 intr_edges=60 inta_edges=180 intr=0 pending=0 inta_idx=0 mask=0xff inte=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=778943 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=788116 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=788154 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=788886 vram=73906 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=798808 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=798846 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=799578 vram=73906 pc=0xd820
[RESUME-PROGRESS] mcyc=800000 pc=0xc279 vram=73906 ios=13260 pic_seen=0 kbd_seen=1 fdc_ios=8314 fdc_data_reads=8192 frame_ticks=76 intr_edges=62 inta_edges=186 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=809601 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=809639 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=810371 vram=73906 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=816703 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=816895 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=817361 vram=73906 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=824483 vram=73906 pc=0x068b
[RESUME-PROGRESS] mcyc=825000 pc=0xe933 vram=73906 ios=13871 pic_seen=0 kbd_seen=1 fdc_ios=8833 fdc_data_reads=8704 frame_ticks=78 intr_edges=63 inta_edges=189 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=831124 vram=73906 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=831162 vram=73906 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=832084 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=841712 vram=73916 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=841750 vram=73916 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=842482 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=843404 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=843596 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=844062 vram=73916 pc=0x068b
[RESUME-PROGRESS] mcyc=850000 pc=0xe5ac vram=73916 ios=14482 pic_seen=0 kbd_seen=1 fdc_ios=9290 fdc_data_reads=9155 frame_ticks=80 intr_edges=65 inta_edges=195 intr=0 pending=0 inta_idx=0 mask=0xff inte=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=851184 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=852414 vram=73916 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=852452 vram=73916 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=853184 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=863081 vram=73916 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=863119 vram=73916 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=863851 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=868056 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=868248 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=868714 vram=73916 pc=0x068b
[RESUME-PROGRESS] mcyc=875000 pc=0xe5aa vram=73916 ios=15186 pic_seen=0 kbd_seen=1 fdc_ios=9835 fdc_data_reads=9693 frame_ticks=83 intr_edges=67 inta_edges=201 intr=0 pending=0 inta_idx=0 mask=0xff inte=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=875836 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=884379 vram=73916 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=884417 vram=73916 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=885149 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=891821 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=892013 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=892479 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=899601 vram=73916 pc=0x068b
[RESUME-PROGRESS] mcyc=900000 pc=0xe935 vram=73916 ios=15838 pic_seen=0 kbd_seen=1 fdc_ios=10390 fdc_data_reads=10240 frame_ticks=85 intr_edges=68 inta_edges=204 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=905681 vram=73916 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=905719 vram=73916 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=906451 vram=73916 pc=0xd820
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=915586 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=915778 vram=73916 pc=0x068b
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=916244 vram=73916 pc=0x068b
[RESUME-FDC] stop reason=data-read-count target=10752 ios=10908 reads=10843 data_reads=10752 writes=65 data=0xe5 mcyc=922973 vram=73916
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:742: $finish called at 1402060210 (100ps)
```
