# jmon33 command-surface probe

Status: **JMON33 IDLE COMMAND SURFACE READY**

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
JMON33_COMMAND_ORACLE=idle JMON33_COMMAND_START_VRAM=210 \
  JMON33_COMMAND_MAX_CYCLES=60000000 JMON33_COMMAND_FRAME_CYCLES=200000 \
  JMON33_COMMAND_HOLD_FRAMES=20 JMON33_COMMAND_GAP_FRAMES=6 \
  JMON33_COMMAND_REPORT=docs/jmon33-idle-command-probe.md sync/jmon33_command_probe.py
```

See [the command probe](jmon33-command-probe.md#command) for environment
overrides and defaults. The command above records this idle-oracle run.

Selected oracle: `idle`. Timing overrides can change the final framebuffer
and fail the fixed hashes.

## Evidence

| Case | Keys | Exit | Stop PC | Cycles | Visible blocks | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| A-enter | `A\n` | `0` | `0xFF54` | `60000002` | `x=8,y=20`, `x=8,y=60` | `af3cfaefcc1f43604a02a2b2f95449a12c1b7a02a14581aea0bbfa06df51283a` | PASS |
| T-enter | `T\n` | `0` | `0xFF54` | `60000002` | `x=8,y=20`, `x=296,y=60` | `9da43c195487eae0eeac8c65725a3251ff502642025b745a16691a1d7044bae3` | PASS |
| B-enter | `B\n` | `0` | `0xFF54` | `60000006` | `x=8,y=20`, `x=0,y=80` | `891fb09d78847a92e8417b1fb8ab81f160555725853b1d21bf29e25348bad0b0` | PASS |

## Disposition

The fixed stimuli produce deterministic command-cursor framebuffers.
Cartridge BASIC remains outside this guard; see the
[cartridge boundary](cartridge-basic-boundary.md).
