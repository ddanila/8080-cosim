# jmon33 command-surface probe

Status: **JMON33 COMMAND SURFACE READY**

This cosim guard exercises Monitor 3.3 with frame interrupts and keyboard
stimulus long enough for the jmon33 scan loop. It proves typed
command/return paths produce deterministic visible screen states, which
is a stronger user-visible command-surface boundary than the plain idle
cursor oracle in `docs/jmon33-ready-probe.md`.

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
- `JMON33_COMMAND_ORACLE` default `early`

## Evidence

| Case | Keys | Exit | Stop PC | Cycles | Port `0x05` samples | Active key values | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | --- |
| A-enter | `A\n` | `0` | `0xFF54` | `60000012` | `5015` | `0x84`, `0x8F`, `0xC4` | `x=8,y=60` | `80` | `efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f` | PASS |
| T-enter | `T\n` | `0` | `0xFF54` | `60000006` | `5015` | `0x88`, `0x8F`, `0xC4` | `x=200,y=20`, `x=152,y=40` | `160` | `348a571e28b5021fc28ca0a83d19e87100d28a9e32910333814eb71a8573b911` | PASS |
| B-enter | `B\n` | `0` | `0xFF54` | `60000005` | `5015` | `0x8C`, `0x8F`, `0xC4` | `x=0,y=80` | `80` | `7de5d7ccbcbe39fc6f644adbeb68b1d38706be9d77616772b3d10686e005d52e` | PASS |

## Disposition

- `JUKU_KEY_START_VRAM`, `JUKU_KEY_HOLD_FRAMES`, and
  `JUKU_KEY_GAP_FRAMES` make the cosim keyboard stimulus usable for
  both ekta37's long banner path and jmon33's short cursor path.
- This proves jmon33 is accepting keyboard input and moving its visible
  command cursor deterministically. It does not prove cartridge BASIC;
  that pairing remains tracked by `docs/cartridge-basic-boundary.md`.
