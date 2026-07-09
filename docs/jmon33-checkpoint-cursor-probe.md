# jmon33 checkpoint cursor probe

Status: **PASS**

This diagnostic starts from a generated pre-cursor Monitor 3.3 cosim
checkpoint, loads its RAM and visible CPU/PPI/PIC state into `juku_top`,
and resumes the LVS-checked CPU until the same monitor-idle cursor oracle
used by `docs/jmon33-ready-probe.md` appears.

## Command

```sh
sync/jmon33_checkpoint_cursor_probe.py
```

Environment overrides:

- `JMON33_CHECKPOINT_CURSOR_CYCLES` default `3801000`
- `JMON33_CHECKPOINT_CURSOR_FRAME_CYCLES` default `200000`
- `JMON33_CHECKPOINT_CURSOR_MAX_MCYC` default `250000`
- `JMON33_CHECKPOINT_CURSOR_PROGRESS_MCYC` default `25000`
- `JMON33_CHECKPOINT_CURSOR_TIMEOUT` default `180` seconds

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `3801005`
- Cosim checkpoint PC: `0xF2C0`
- Cosim checkpoint VRAM SHA256: `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d`
- HDL resume exit code: `0`
- Timed out: `no`
- Cursor stop line: `[RESUME-CURSOR] jmon33 cursor oracle reached x=8 y=20 at bounded exit mcyc=250000 vram=210 pc=0xfc90`
- First IRQ line: `[RESUME-IRQ] intr rise count=1 mcyc=29329 vram=210`
- Last IRQ line: `[RESUME-IRQ] inta fall count=24 mcyc=234602 vram=210`
- First progress line: `[RESUME-PROGRESS] mcyc=25000 pc=0xfc95 vram=210 ios=11 pic_seen=0 kbd_seen=0 fdc_ios=0 fdc_data_reads=0 frame_ticks=0 intr_edges=0 inta_edges=0 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- Last progress line: `[RESUME-PROGRESS] mcyc=225000 pc=0xf3a5 vram=210 ios=452 pic_seen=0 kbd_seen=1 fdc_ios=0 fdc_data_reads=0 frame_ticks=7 intr_edges=7 inta_edges=21 intr=0 pending=0 inta_idx=0 mask=0xdf inte=1`
- HDL cursor VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`

## Boundary

- This is a checkpoint-resumed Monitor 3.3 cursor proof, not yet a full
  uninterrupted `juku_top` run from reset to the user-visible prompt.
- The checkpoint VRAM is deliberately blank, so the cursor evidence comes
  from resumed HDL CPU execution after the checkpoint.
