# jmon33 HDL T-command FDC diagnostic

Status date: 2026-07-08.

This note preserves the local `T` command checkpoint run that temporarily
overwrote `docs/jmon33-hdl-command-probe.md`. It is useful evidence, but it is
not the main command-surface milestone because the passing `A` command remains
the current HDL proof.

## Run

```sh
JMON33_HDL_COMMAND_CASES=T-enter \
JMON33_HDL_COMMAND_PHASE_CHECKPOINT=1 \
JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES=26050000 \
JMON33_HDL_COMMAND_KHOLD=500000 \
JMON33_HDL_COMMAND_MAX_MCYC=900000 \
sync/jmon33_hdl_command_probe.py
```

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint cycle: `26050003`
- Cosim checkpoint PC: `0xE436`
- Cosim checkpoint IFF: `1`
- Cosim checkpoint VRAM writes: `290`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Case: `T-enter`
- Key: `T\n`
- Checkpoint keyboard phase: `kbd=1/7`
- Keyboard samples: `527`
- Active key values: `0xC4`
- Stimulus:
  - `[RESUME-KBD-STIM] press key=1 col=8 bit=5 shift=0 mcyc=0 vram=290`
  - `[RESUME-KBD-STIM] release key=1 mcyc=48330 vram=290`
- Command oracle: `none`
- Resume line:
  `JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0xe43c ios=111485 pic_seen=0 kbd_seen=1 fdc_ios=109522`
- Visible blocks: `x=8,y=20`
- Pixels: `80`
- VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`

## Interpretation

The `T` run proves the resumed HDL path is seeing keyboard activity, but it
does not reach the `T` command framebuffer oracle. The important finding is the
large FDC I/O count: `fdc_ios=109522`. That means the mismatch is no longer
purely a keyboard-phase problem; `T` enters a disk-controller path in the
resumed `juku_top` environment.

Before treating this as an FDC core bug, compare the oracle setup. The existing
jmon33 command oracle is generated without a disk unless `JUKU_DISK` is set,
while the structural top-level has a visible FDC device on the decoded bus. The
next useful diagnostic is therefore an FDC-aware jmon33 `T` oracle or an
explicit no-disk/not-ready reference, not further blind keyboard timing scans.
