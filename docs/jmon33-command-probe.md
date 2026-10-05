# jmon33 command-surface probe

Status: **JMON33 COMMAND SURFACE READY**

This cosim guard exercises Monitor 3.3 with frame interrupts and keyboard
stimulus for A, T, and B followed by Enter. After a fixed cycle budget it
checks successful trace exit, full VRAM hashes, and expected solid blocks.
It does not assert command semantics or detect when a command returns.
The no-input baseline is the [idle cursor oracle](jmon33-ready-probe.md).

## Command

Run from the repository root with Python, a C compiler (`CC`, default
`cc`), and `roms/jmon33.bin`. The probe builds a temporary executable
and overwrites the selected report; its parent directory must exist.
Each case restores the prior `cosim/vram.bin` contents, or removes the
new dump if initially absent, after sampling on normal completion.

```sh
JMON33_COMMAND_ORACLE=early JMON33_COMMAND_START_VRAM=0 \
  JMON33_COMMAND_MAX_CYCLES=60000000 JMON33_COMMAND_FRAME_CYCLES=200000 \
  JMON33_COMMAND_HOLD_FRAMES=20 JMON33_COMMAND_GAP_FRAMES=6 \
  JMON33_COMMAND_REPORT=docs/jmon33-command-probe.md sync/jmon33_command_probe.py
```

Environment overrides (script defaults; the command above records this run):

- `JMON33_COMMAND_MAX_CYCLES` default `60000000`
- `JMON33_COMMAND_FRAME_CYCLES` default `200000`
- `JMON33_COMMAND_HOLD_FRAMES` default `20`
- `JMON33_COMMAND_GAP_FRAMES` default `6`
- `JMON33_COMMAND_START_VRAM` default `0`
- `JMON33_COMMAND_ORACLE` default `early`; `idle` selects the alternate hashes.
- `JMON33_COMMAND_TRACE_IO` default `1`; `0` leaves inherited `JUKU_TRACE_IO` unchanged. Set `JUKU_TRACE_IO=0` as well to suppress detailed I/O samples.
- `JMON33_COMMAND_REPORT` overrides the report output path.

Selected oracle: `early`. Timing overrides can change the final framebuffer
and fail the fixed hashes.

## Evidence

| Case | Keys | Exit | Stop PC | Cycles | Visible blocks | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| A-enter | `A\n` | `0` | `0xFF54` | `60000012` | `x=8,y=60` | `efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f` | PASS |
| T-enter | `T\n` | `0` | `0xFF54` | `60000006` | `x=200,y=20`, `x=152,y=40` | `348a571e28b5021fc28ca0a83d19e87100d28a9e32910333814eb71a8573b911` | PASS |
| B-enter | `B\n` | `0` | `0xFF54` | `60000005` | `x=0,y=80` | `7de5d7ccbcbe39fc6f644adbeb68b1d38706be9d77616772b3d10686e005d52e` | PASS |

## Disposition

The fixed stimuli produce deterministic command-cursor framebuffers.
Cartridge BASIC remains outside this guard; see the
[cartridge boundary](cartridge-basic-boundary.md).
