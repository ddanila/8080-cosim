# jmon33 HDL command-surface probe

Status: **JMON33 HDL COMMAND BOUNDED DIAGNOSTIC**

This guard starts from the same pre-cursor Monitor 3.3 cosim checkpoint
used by `docs/jmon33-checkpoint-cursor-probe.md`, injects a single
command plus Enter through the `juku_top` keyboard pins, and checks the
visible command-state oracles pinned by `docs/jmon33-command-probe.md`.

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
- `JMON33_HDL_COMMAND_KEY_MCYC` default `260000`
- `JMON33_HDL_COMMAND_CASES` selected `A-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint VRAM SHA256: `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d`

| Case | Key | Exit | Timed out | Keyboard samples | Active key values | Command oracle | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A-enter | `A\n` | `0` | `False` | `289` | `0x84`, `0x8F`, `0xC4` | `none` | `x=8,y=40` | `80` | `fef67bc592458805f1db4f8f07406f21c2c33cb1ae877fa999c3c4b97b593433` | FAIL |

## Disposition

- The HDL checkpoint harness now has a generic two-key command stimulus
  path in addition to the fixed EKDOS `TDD` stimulus path.
- This is currently a bounded diagnostic, not a completed HDL command
  oracle. The keyboard samples match the cosim values, but the
  checkpoint-resumed top-level run has not yet reached the final cosim
  command framebuffer within the practical local bound.
- This proof is scoped to jmon33 monitor commands. BASIC remains tracked
  separately by `docs/basic-launch-probe.md` and
  `docs/basic-factory-command-probe.md`.
