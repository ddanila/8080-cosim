# jmon33 HDL command-surface probe

Status: **JMON33 HDL FDC TRACE REQUIREMENT FAILED**

This wrapper generates a disk-backed cosim checkpoint with the T command
scheduled, then resumes its RAM and visible state in `juku_top`. The default
checkpoint is already inside the FDC polling loop. The HDL run stops after
eight FDC events and checks for a write-track or write-protect trace marker;
it does not require a completed command or matching command framebuffer.

## Command

```sh
sync/jmon33_hdl_fdc_command_probe.py
```

Recorded environment settings:

- `JMON33_HDL_COMMAND_MAX_MCYC` = `120000`
- `JMON33_HDL_COMMAND_TIMECAP` = `4000000000`
- `JMON33_HDL_COMMAND_FRAMEIRQ` = `200000`
- `JMON33_HDL_COMMAND_KHOLD` = `500000`
- `JMON33_HDL_COMMAND_KGAP` = `100000`
- `JMON33_HDL_COMMAND_CHECKPOINT_CYCLES` = `19900000`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT` = `1`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES` = `26050000`
- `JMON33_HDL_COMMAND_PHASE_START_VRAM` = `210`
- `JMON33_HDL_COMMAND_HOLD_FRAMES` = `20`
- `JMON33_HDL_COMMAND_GAP_FRAMES` = `6`
- Expected checkpoint SHA256 `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- `JMON33_HDL_COMMAND_KEY_MCYC` = `50000`
- `JMON33_HDL_COMMAND_DEFER_IFF` = `1`
- `JMON33_HDL_COMMAND_FORCE_CLEAN_STATUS` = `1`
- `JMON33_HDL_COMMAND_DISK` = `media/disks/JUKU1.CPM`
- `JMON33_HDL_COMMAND_TRACEFDC` = `1`
- `JMON33_HDL_COMMAND_STOPFDC` = `8`
- `JMON33_HDL_COMMAND_CASES` selected `T-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint cycle: `26050000`
- Cosim checkpoint PC: `0xE43C`
- Cosim checkpoint IFF: `1`
- Cosim checkpoint VRAM writes: `290`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Phase-checkpoint mode: `yes`

| Case | Key | Checkpoint | Exit | Timed out | Keyboard samples | Active key values | Stimulus | FDC trace | Idle cursor | Command oracle | Resume line | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| T-enter | `T\n` | `cyc=26050000 pc=0xE43C iff=1 kbd=2/0` | `0` | `False` | `0` | - | - | `[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=422 vram=290 ios=1`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=430 vram=290 ios=2`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=438 vram=290 ios=3`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=446 vram=290 ios=4`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=454 vram=290 ios=5`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=462 vram=290 ios=6`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=470 vram=290 ios=7`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x44 mcyc=478 vram=290 ios=8` | `yes` | `none` | `none` | `x=8,y=20` | `80` | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` | FAIL |

## Disposition

- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT=1` generates a per-case cosim
  checkpoint with the command in the keyboard schedule and scales its
  frame phase into HDL M-cycles. With phase checkpoints disabled,
  the runner resumes a shared checkpoint at 19,900,000 cycles by default;
  `JMON33_HDL_COMMAND_KEY_MCYC` delays key injection after resume.
- The expected checkpoint hash selects the idle-cursor or early-command
  framebuffer oracles. Each `PASS` row requires a zero HDL exit code,
  the expected framebuffer hash and visible blocks, and a command-oracle
  marker. The generic runner can exit successfully with diagnostic rows;
  use the [A wrapper](../sync/jmon33_hdl_a_command_probe.py) or
  [B wrapper](../sync/jmon33_hdl_b_command_probe.py) to require its pinned oracle.
- `Idle cursor` records whether the checkpoint cursor survived; it is
  informational and is not a separate pass condition.
- These are bounded checkpoint-resumed command checks. Cartridge BASIC
  has a separate [boundary](cartridge-basic-boundary.md).

## FDC-Specific Disposition

- This wrapper intentionally stops on the FDC trace boundary, so the generic
  command framebuffer result remains `FAIL`/diagnostic.
- The wrapper accepts either a write-track command (`OUT 0x1C = 0xFD`)
  or a write-protect status read (`IN 0x1C = 0x40`) in the trace. It does
  not require both markers or verify their order.
- Compare the [cosim FDC oracle](jmon33-fdc-command-probe.md) for the
  polling-loop interpretation. This check does not prove disk formatting
  or complete the generic command framebuffer oracle.
