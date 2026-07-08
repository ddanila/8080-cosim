# jmon33 HDL command-surface probe

Status: **JMON33 HDL COMMAND BOUNDED DIAGNOSTIC**

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

- `JMON33_HDL_COMMAND_MAX_MCYC` default `500000`
- `JMON33_HDL_COMMAND_TIMECAP` default `4000000000`
- `JMON33_HDL_COMMAND_FRAMEIRQ` default `200000`
- `JMON33_HDL_COMMAND_KHOLD` default `200000`
- `JMON33_HDL_COMMAND_KGAP` default `100000`
- `JMON33_HDL_COMMAND_CHECKPOINT_CYCLES` default `20000000`
- Expected checkpoint SHA256 `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- `JMON33_HDL_COMMAND_KEY_MCYC` default `50000`
- `JMON33_HDL_COMMAND_CASES` selected `A-enter,T-enter,B-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`

| Case | Key | Exit | Timed out | Keyboard samples | Active key values | Idle cursor | Command oracle | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | ---: | --- | --- |
| A-enter | `A\n` | `0` | `False` | `289` | `0x84`, `0x8F`, `0xC4` | `no` | `none` | `x=8,y=60` | `80` | `efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f` | FAIL |
| T-enter | `T\n` | `0` | `False` | `289` | `0x88`, `0x8F`, `0xC4` | `no` | `none` | `x=8,y=60` | `80` | `efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f` | FAIL |
| B-enter | `B\n` | `0` | `False` | `289` | `0x8C`, `0x8F`, `0xC4` | `no` | `none` | `x=8,y=60` | `80` | `efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f` | FAIL |

## Disposition

- The HDL checkpoint harness now has a generic two-key command stimulus
  path in addition to the fixed EKDOS `TDD` stimulus path.
- The default checkpoint is the monitor-idle cursor state. A later
  `JMON33_HDL_COMMAND_KEY_MCYC` delay lets the resumed keyboard scan
  settle before the command key is pressed.
- The default checkpoint is the monitor-idle cursor state, so the
  default expected command hashes come from
  `docs/jmon33-idle-command-probe.md`, not from reset-time typed
  command runs.
- The current HDL rows are diagnostic until their final command
  framebuffers match the selected cosim oracle.
- The `Idle cursor` column checks whether the monitor-idle cursor
  block from the checkpoint survived into the final framebuffer.
- This proof is scoped to jmon33 monitor commands. BASIC remains tracked
  separately by `docs/basic-launch-probe.md` and
  `docs/basic-factory-command-probe.md`.
