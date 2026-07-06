# BASIC launch probe

Status: **BASIC LAUNCH NOT YET REACHED**

This probe exercises the full EktaSoft monitor `B` command with
`JUKU_CART=roms/jbasic11.bin`. It complements `sync/basic_cart_check.sh`,
which already proves the cartridge window wiring independently.

## Command

```sh
sync/basic_launch_probe.py
```

Environment overrides:

- `BASIC_LAUNCH_KEYS` default `B`
- `BASIC_LAUNCH_MAX_CYCLES` default `120000000`
- `BASIC_LAUNCH_FRAME_CYCLES` default `40000`

## Evidence

| Check | Result |
| --- | --- |
| trace exit code | `0` |
| `jbasic11.bin` cartridge loaded | PASS |
| keyboard ports used | PASS |
| PC entered `0x4000..0xBFFF` | `0` cycles |
| pchist count in `0x4000..0xBFFF` | `0` |
| VRAM dump size | `9640` bytes |
| VRAM SHA256 | `1a178175b438c9d5b6ef20febe467efb58657646bd9ee6622349bcfa359eed9f` |

## Stop State

- Stop PC: `0xFED4`
- Cycles: `120000008`
- Mode: `0`
- Mode switches: `422664`

## Disposition

- The cartridge is loaded and the keyboard path is active, but the current
  `B` command run never executes in `0x4000..0xBFFF`.
- The remaining work is monitor command/control-flow validation, not the
  D8/D22 cartridge-window wiring guarded by `sync/basic_cart_check.sh`.
