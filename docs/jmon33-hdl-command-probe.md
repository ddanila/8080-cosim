# jmon33 HDL command-surface probe

Status: **JMON33 HDL A-COMMAND ORACLE READY**

This guard starts from a generated Monitor 3.3 cosim checkpoint,
loads that RAM and visible state into `juku_top`, injects a single
command plus Enter through the `juku_top` keyboard pins, and checks the
visible command-state oracles pinned by `docs/jmon33-command-probe.md`
or `docs/jmon33-idle-command-probe.md`, depending on the checkpoint.

## Command

```sh
sync/jmon33_hdl_command_probe.py
```

Environment overrides:

- `JMON33_HDL_COMMAND_MAX_MCYC` default `700000`
- `JMON33_HDL_COMMAND_TIMECAP` default `4000000000`
- `JMON33_HDL_COMMAND_FRAMEIRQ` default `200000`
- `JMON33_HDL_COMMAND_KHOLD` default `500000`
- `JMON33_HDL_COMMAND_KGAP` default `100000`
- `JMON33_HDL_COMMAND_CHECKPOINT_CYCLES` default `19900000`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT` default `1`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES` default `26050000`
- `JMON33_HDL_COMMAND_PHASE_START_VRAM` default `210`
- `JMON33_HDL_COMMAND_HOLD_FRAMES` default `20`
- `JMON33_HDL_COMMAND_GAP_FRAMES` default `6`
- Expected checkpoint SHA256 `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- `JMON33_HDL_COMMAND_KEY_MCYC` default `50000`
- `JMON33_HDL_COMMAND_DEFER_IFF` default `1`
- `JMON33_HDL_COMMAND_FORCE_CLEAN_STATUS` default `1`
- `JMON33_HDL_COMMAND_DISK` default `none`
- `JMON33_HDL_COMMAND_TRACEFDC` default `0`
- `JMON33_HDL_COMMAND_STOPFDC` default `0`
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

- The HDL checkpoint harness now has a generic two-key command stimulus
  path in addition to the fixed EKDOS `TDD` stimulus path.
- The default checkpoint is the monitor-idle cursor state. A later
  `JMON33_HDL_COMMAND_KEY_MCYC` delay lets the resumed keyboard scan
  settle before the command key is pressed.
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT=1` generates a per-case
  cosim checkpoint with the command key already in the monitor
  keyboard schedule, scales that frame phase into HDL M-cycles,
  and resumes through the remaining key/Enter path.
- The default checkpoint is deliberately before the 20,000,000-cycle
  ready-probe stop, because that stop is visually idle but lands in
  the frame interrupt vector (`PC=0xFF54`, `IFF=0`).
- The default checkpoint is the monitor-idle cursor state, so the
  default expected command hashes come from
  `docs/jmon33-idle-command-probe.md`, not from reset-time typed
  command runs.
- The current HDL rows are diagnostic until their final command
  framebuffers match the selected cosim oracle.
- The `Idle cursor` column checks whether the monitor-idle cursor
  block from the checkpoint survived into the final framebuffer.
- This proof is scoped to jmon33 monitor commands. Cartridge BASIC remains
  tracked by `docs/cartridge-basic-boundary.md`.
