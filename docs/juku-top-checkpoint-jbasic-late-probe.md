# juku_top checkpoint JBASIC late probe

Status: **HDL EKDOS JBASIC LATE READY**

This diagnostic starts from a generated cosim EKDOS `JBASIC` checkpoint
after the complete 19,968-byte WD1793 data-register transfer on
`media/disks/JUKPROG2.CPM`. The command is already entered in the
checkpoint, so the HDL resume runs with no keyboard stimulus and stops
only when the fixed-`0xD800` BASIC `READY` glyph oracle appears.

## Command

```sh
sync/juku_top_checkpoint_jbasic_late_probe.py
```

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `32687566`
- Cosim checkpoint VRAM writes: `73586`
- Cosim checkpoint PC: `0xE5AA`
- Cosim checkpoint keyboard position/phase: `10` / `8`
- Cosim checkpoint FDC data reads: `19968`
- Cosim checkpoint FDC track/sector/data/status: `14` / `09` / `00` / `00`
- HDL checkpoint PC bias: `0`
- HDL resume exit code: `0`
- Timed out: `no`
- READY stop line: `[RESUME-JBASIC] READY prompt reached mcyc=59120 vram=73975 pc=0x097a`
- HDL final visible `READY` at scanline 121: `yes`
- HDL final visible `A>JBASIC` command line at scanline 71: `yes`
- HDL final VRAM size: `9640` (ok)
- HDL final VRAM SHA256: `0b61035c5326e23450c49633cfa449c43851619f9da9fbae2c2ec3c9e80109df`
- Checkpoint READY row bytes y=121 x=0..9: `00 00 00 00 00 00 00 00 00 00`
- HDL final READY row bytes y=121 x=0..9: `3c 3e 08 3c 22 00 00 00 00 00`
- First changed VRAM cells: `x=0 y=70 ff->00, x=0 y=71 f7->08, x=0 y=72 eb->14, x=0 y=73 dd->22, x=0 y=74 dd->22, x=0 y=75 c1->3e, x=0 y=76 dd->22, x=0 y=77 dd->22, x=0 y=78 ff->00, x=0 y=79 ff->00, x=8 y=91 00->3c, x=9 y=91 00->08, x=10 y=91 00->1c, x=11 y=91 00->1c, x=12 y=91 00->1c, x=8 y=92 00->12, x=9 y=92 00->14, x=10 y=92 00->22, x=11 y=92 00->08, x=12 y=92 00->22, x=8 y=93 00->12, x=9 y=93 00->22, x=10 y=93 00->20, x=11 y=93 00->08`
- FDC trace lines: `0`
- Last observed HDL progress FDC data reads: `0`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xd7f0 vram=73726 ios=317 pic_seen=0 kbd_seen=1 fdc_ios=1 fdc_data_reads=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=50000 pc=0x13c9 vram=73926 ios=645 pic_seen=0 kbd_seen=1 fdc_ios=1 fdc_data_reads=0 frame_ticks=4 intr_edges=4 inta_edges=12 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Stop/fail line: `none`

## Boundary

- This is a late-state proof, not a replacement for the prompt-checkpoint
  command-stimulus report. It proves that checkpoint-resumed `juku_top`
  can continue from the post-transfer JBASIC state to the user-visible
  BASIC `READY` prompt.
- The prompt-checkpoint report still owns the early HDL path: `JBASIC`
  key sampling, command echo, and the first 4,096 post-command FDC data
  reads.
- The open gap is now the uninterrupted HDL bridge between those two
  checkpoint windows, not the final BASIC prompt renderer itself.

## HDL stdout tail

```
FDC-1793: loaded raw disk media/disks/JUKPROG2.CPM (2 sides)
[RESUME] loaded checkpoint pc=0xe5aa sp=0xd2ee inta_n=1 sys_status=0x00 core_inta=0 core_minta=0 core_intr=0 inte=0 intr=0
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=392 vram=73586 pc=0x068b
[RESUME-JBASIC-CMD] A>JBASIC command line reached mcyc=4350 vram=73595 pc=0x1006
[RESUME-VRAM] writes=73600 mcyc=8297 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=10913 vram=73626 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=10951 vram=73626 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=11778 vram=73626 pc=0xd820
[RESUME-VRAM] writes=73700 mcyc=19834 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=21830 vram=73716 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=21868 vram=73716 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=22600 vram=73716 pc=0xd820
[RESUME-PROGRESS] mcyc=25000 pc=0xd7f0 vram=73726 ios=317 pic_seen=0 kbd_seen=1 fdc_ios=1 fdc_data_reads=0 frame_ticks=2 intr_edges=2 inta_edges=6 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=32758 vram=73796 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=32796 vram=73796 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=33528 vram=73796 pc=0xd820
[RESUME-VRAM] writes=73800 mcyc=33813 pc=0x097a
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=43650 vram=73896 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=43688 vram=73896 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=44420 vram=73896 pc=0xd820
[RESUME-VRAM] writes=73900 mcyc=45320 pc=0x097a
[RESUME-PROGRESS] mcyc=50000 pc=0x13c9 vram=73926 ios=645 pic_seen=0 kbd_seen=1 fdc_ios=1 fdc_data_reads=0 frame_ticks=4 intr_edges=4 inta_edges=12 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1
[RESUME-PIC] OUT port=0x01 data=0xff mcyc=54615 vram=73946 pc=0xd7c1
[RESUME-PIC] OUT port=0x00 data=0x20 mcyc=54653 vram=73946 pc=0xd7dc
[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=55385 vram=73946 pc=0xd820
[RESUME-JBASIC] READY prompt reached mcyc=59120 vram=73975 pc=0x097a
[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin
/home/ddanila/fun/8080-cosim/hdl/sim/juku_top_checkpoint_resume_tb.v:638: $finish called at 86694800 (100ps)
```
