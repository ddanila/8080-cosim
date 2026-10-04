# jmon33 HDL command-surface probe

Status: **JMON33 HDL A-COMMAND ORACLE READY**

This guard starts from a generated Monitor 3.3 cosim checkpoint,
loads that RAM and visible state into `juku_top`, resumes the keyboard
schedule for a command plus Enter, and checks the
visible command-state oracles pinned by `docs/jmon33-command-probe.md`
or `docs/jmon33-idle-command-probe.md`, depending on the checkpoint.

## Command

```sh
sync/jmon33_hdl_a_command_probe.py
```

Recorded environment settings:

- `JMON33_HDL_COMMAND_MAX_MCYC` = `700000`
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
- `JMON33_HDL_COMMAND_DISK` = `none`
- `JMON33_HDL_COMMAND_TRACEFDC` = `0`
- `JMON33_HDL_COMMAND_STOPFDC` = `0`
- `JMON33_HDL_COMMAND_CASES` selected `A-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint cycle: `26050000`
- Cosim checkpoint PC: `0xF3AD`
- Cosim checkpoint IFF: `1`
- Cosim checkpoint VRAM writes: `290`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Phase-checkpoint mode: `yes`

| Case | Key | Checkpoint | Exit | Timed out | Keyboard samples | Active key values | Stimulus | FDC trace | Idle cursor | Command oracle | Resume line | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| A-enter | `A\n` | `cyc=26050000 pc=0xF3AD iff=1 kbd=2/0` | `0` | `False` | `323` | - | - | - | `yes` | `[RESUME-COMMAND] jmon33 command oracle reached x0=8 y0=20 x1=8 y1=60 mcyc=543233 vram=301 pc=0x01ce` | `none` | `x=8,y=20`, `x=8,y=60` | `160` | `af3cfaefcc1f43604a02a2b2f95449a12c1b7a02a14581aea0bbfa06df51283a` | PASS |

## Disposition

- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT=1` generates a per-case cosim
  checkpoint with the command in the keyboard schedule and scales its
  frame phase into HDL M-cycles. With phase checkpoints disabled,
  the runner resumes a shared checkpoint at 19,900,000 cycles by default;
  `JMON33_HDL_COMMAND_KEY_MCYC` delays key injection after resume.
- In phase-checkpoint mode, `kbd=2/0` means the two-key schedule has
  already finished in cosim. Such a run checks the resumed command
  framebuffer without exercising command entry through HDL keyboard pins.
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
