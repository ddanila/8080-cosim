# BASIC launch probe

Status: **BASIC RAM EXECUTION REACHED**

This probe exercises the monitor `B` command with
`JUKU_CART=roms/jbasic11.bin`. By default it checks Monitor 3.3,
which MAME tags as `Monitor/Bootstrap 3.3 \w JBASIC`, plus the
EktaSoft 3.43m #0037 ROM used by the main boot guard. It complements
`sync/basic_cart_check.sh`,
which already proves the cartridge window wiring independently.

## Command

```sh
sync/basic_launch_probe.py
```

Environment overrides:

- `BASIC_LAUNCH_KEYS` default `B`
- `BASIC_LAUNCH_ROM` default unset (runs `jmon33.bin` and `ekta37.bin`)
- `BASIC_LAUNCH_MAX_CYCLES` default `120000000`
- `BASIC_LAUNCH_FRAME_CYCLES` default unset (`jmon33`: `200000`, `ekta37`: `40000`)

## Evidence

| Monitor | ROM | Frame cycles | Infra | Cart overlay reads | PC in `0x4000..0xBFFF` | Mode-1 PC cycles | Mode-2 PC cycles | `0x00` opcode cycles | RAM writes | RAM nonzero bytes | RAM byte sum | Visible pixels | Stop PC | Mode | VRAM SHA256 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| jmon33 | `roms/jmon33.bin` | `200000` | PASS | `8196` | `17881962` | `17881962` | `0` | `17881962` | `1636` | `0` | `0` | `0` | `0x9B6A` | `1` | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| ekta37 | `roms/ekta37.bin` | `40000` | PASS | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `16555` | `0xFED4` | `0` | `1a178175b438c9d5b6ef20febe467efb58657646bd9ee6622349bcfa359eed9f` |

## Disposition

- `jmon33` reads the BASIC cartridge and executes in `0x4000..0xBFFF`; `17881962` of those PC cycles are in RAM/ROM mode 1 and `0` are in cartridge overlay mode 2. `17881962` PC cycles fetch a `0x00` opcode there. The RAM window saw `1636` accepted writes, `0` of them nonzero, ending with `0` nonzero bytes and byte sum `0`. The captured framebuffer has `0` visible pixels.
- `ekta37` does not select the cartridge overlay in this run.
- The remaining BASIC work is a user-visible BASIC prompt oracle and HDL-side
  coverage of this stronger Monitor 3.3 path.
