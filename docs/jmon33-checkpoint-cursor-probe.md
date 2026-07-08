# jmon33 checkpoint cursor probe

Status: **JMON33 CHECKPOINT CURSOR NOT YET REACHED**

This diagnostic starts from a generated pre-cursor Monitor 3.3 cosim
checkpoint, loads its RAM and visible CPU/PPI/PIC state into `juku_top`,
and resumes the LVS-checked CPU until the same monitor-idle cursor oracle
used by `docs/jmon33-ready-probe.md` appears.

## Command

```sh
sync/jmon33_checkpoint_cursor_probe.py
```

Environment overrides:

- `JMON33_CHECKPOINT_CURSOR_CYCLES` default `3500000`
- `JMON33_CHECKPOINT_CURSOR_FRAME_CYCLES` default `200000`
- `JMON33_CHECKPOINT_CURSOR_MAX_MCYC` default `2000000`
- `JMON33_CHECKPOINT_CURSOR_TIMEOUT` default `90` seconds

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `3500003`
- Cosim checkpoint PC: `0xF3A1`
- Cosim checkpoint VRAM SHA256: `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d`
- HDL resume exit code: `124`
- Timed out: `yes`
- Cursor stop line: `none`
- First IRQ line: `[RESUME-IRQ] inta fall count=1 mcyc=1 vram=200`
- Last IRQ line: `[RESUME-IRQ] intr rise count=2 mcyc=57230 vram=200`
- HDL cursor VRAM SHA256: `missing`

## Boundary

- This is a checkpoint-resumed Monitor 3.3 cursor proof, not yet a full
  uninterrupted `juku_top` run from reset to the user-visible prompt.
- The checkpoint VRAM is deliberately blank, so the cursor evidence comes
  from resumed HDL CPU execution after the checkpoint.

## Observations

- checkpoint-resumed HDL run did not reach the jmon33 cursor oracle

## HDL stdout tail

```text
[RESUME] loaded checkpoint pc=0xf3a1 sp=0x00ec
[RESUME-IRQ] inta fall count=1 mcyc=1 vram=200
[RESUME-IRQ] intr rise count=1 mcyc=28572 vram=200
[RESUME-IRQ] inta fall count=2 mcyc=28574 vram=200
[RESUME-IRQ] inta fall count=3 mcyc=28575 vram=200
[RESUME-IRQ] intr rise count=2 mcyc=57230 vram=200
```
