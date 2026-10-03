# jmon33 command-surface probe

Status: **JMON33 IDLE COMMAND SURFACE READY**

This cosim guard exercises Monitor 3.3 with frame interrupts and keyboard
stimulus for A, T, and B followed by Enter. After a fixed cycle budget it
checks successful trace exit, full VRAM hashes, and expected solid blocks.
It does not assert command semantics or detect when a command returns.
The no-input baseline is the [idle cursor oracle](jmon33-ready-probe.md).

## Command

```sh
sync/jmon33_command_probe.py
```

Environment overrides:

- `JMON33_COMMAND_MAX_CYCLES` default `60000000`
- `JMON33_COMMAND_FRAME_CYCLES` default `200000`
- `JMON33_COMMAND_HOLD_FRAMES` default `20`
- `JMON33_COMMAND_GAP_FRAMES` default `6`
- `JMON33_COMMAND_START_VRAM` default `0`
- `JMON33_COMMAND_ORACLE` default `early`; `idle` selects the alternate hashes.
- `JMON33_COMMAND_TRACE_IO` default `1`; `0` suppresses detailed I/O samples.
- `JMON33_COMMAND_REPORT` overrides the report output path.

Selected oracle: `idle`. Timing overrides can change the final framebuffer
and fail the fixed hashes. I/O sample counts are diagnostic, not pass criteria.

## Evidence

| Case | Keys | Exit | Stop PC | Cycles | Port `0x05` samples | Active key values | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | --- |
| A-enter | `A\n` | `0` | `0xFF54` | `60000002` | `5015` | `0x84`, `0x8F`, `0xAF`, `0xE4`, `0xEF` | `x=8,y=20`, `x=8,y=60` | `160` | `af3cfaefcc1f43604a02a2b2f95449a12c1b7a02a14581aea0bbfa06df51283a` | PASS |
| T-enter | `T\n` | `0` | `0xFF54` | `60000002` | `5015` | `0x88`, `0x8F`, `0xAF`, `0xE4`, `0xEF` | `x=8,y=20`, `x=296,y=60` | `160` | `9da43c195487eae0eeac8c65725a3251ff502642025b745a16691a1d7044bae3` | PASS |
| B-enter | `B\n` | `0` | `0xFF54` | `60000006` | `5015` | `0x8C`, `0x8F`, `0xAF`, `0xE4`, `0xEF` | `x=8,y=20`, `x=0,y=80` | `160` | `891fb09d78847a92e8417b1fb8ab81f160555725853b1d21bf29e25348bad0b0` | PASS |

## Disposition

- `JUKU_KEY_START_VRAM`, `JUKU_KEY_HOLD_FRAMES`, and
  `JUKU_KEY_GAP_FRAMES` make the cosim keyboard stimulus usable for
  both ekta37's long banner path and jmon33's short cursor path.
- This proves jmon33 is accepting keyboard input and moving its visible
  command cursor deterministically. It does not prove cartridge BASIC;
  see the [cartridge boundary](cartridge-basic-boundary.md).
