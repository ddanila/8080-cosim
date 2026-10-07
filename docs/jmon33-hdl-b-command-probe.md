# jmon33 HDL command-surface probe

Status: **JMON33 HDL SELECTED COMMAND ORACLE READY**

This guard starts from a generated Monitor 3.3 cosim checkpoint,
loads RAM and visible state into `juku_top`, and checks the resumed
command state against the [early-command](jmon33-command-probe.md) or
[idle-command](jmon33-idle-command-probe.md) framebuffer oracles.
Whether command entry occurs in HDL depends on the checkpoint. Inspect
the recorded keyboard position below: `kbd=2/0` means the two-key
schedule already finished in cosim.

## Command

Run from the repository root with Python 3, a C compiler (`CC`, default
`cc`), Icarus Verilog (`iverilog` and `vvp`), and `roms/jmon33.bin`.
Builds and checkpoints use a temporary directory. The runner regenerates
`hdl/sim/jmon33.hex`, restores prior cosim and HDL VRAM dumps after
normal sampling, and overwrites the selected report. Relative
`JMON33_HDL_COMMAND_REPORT` paths resolve from the repository root.

```sh
sync/jmon33_hdl_b_command_probe.py
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
- `JMON33_HDL_COMMAND_CASES` selected `B-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint cycle: `26050004`
- Cosim checkpoint PC: `0xFC90`
- Cosim checkpoint IFF: `1`
- Cosim checkpoint VRAM writes: `290`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Phase-checkpoint mode: `yes`

| Case | Key | Checkpoint | Exit | Timed out | Keyboard samples | Active key values | Stimulus | FDC trace | Idle cursor | Command oracle | Resume line | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| B-enter | `B\n` | `cyc=26050004 pc=0xFC90 iff=1 kbd=2/0` | `0` | `False` | `323` | - | - | - | `yes` | `[RESUME-COMMAND] jmon33 command oracle reached x0=8 y0=20 x1=0 y1=80 mcyc=537477 vram=301 pc=0x01ce` | `none` | `x=8,y=20`, `x=0,y=80` | `160` | `891fb09d78847a92e8417b1fb8ab81f160555725853b1d21bf29e25348bad0b0` | PASS |

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
- Keep `JMON33_HDL_COMMAND_REPORT` unset for the A/B wrappers: they
  validate and rewrite their fixed report paths. Use the generic runner
  directly when selecting an alternate report path.
- `Idle cursor` records whether the checkpoint cursor survived; it is
  informational and is not a separate pass condition.
- These are bounded checkpoint-resumed command checks. Cartridge BASIC
  has a separate [boundary](cartridge-basic-boundary.md).
