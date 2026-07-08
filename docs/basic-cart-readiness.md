# BASIC cartridge readiness

Status: **BASIC CARTRIDGE WINDOW READY**

This guard proves the optional MAME-compatible expansion cartridge window used by
`jbasic11.bin`:

- cosim loads `JUKU_CART=roms/jbasic11.bin` and exposes it in memory mode 2 at
  `0x4000..0xBFFF`.
- `juku_top` keeps D17-D21 passive and can populate D22 with `+cart=<readmemh>`
  for the traced `0x4000..0x5FFF` BASIC socket; the HDL unit test checks D8's
  pager byte and D22's driven byte directly.
- `tests/cart_window.hex` copies a tiny routine to RAM, switches to mode 2,
  reads byte `0x4000` from the cartridge, switches to mode 3, and writes the
  byte to VRAM under cosim. The HDL unit independently checks the same D8/D22
  window and both paths must expose `0xC3`, the first byte of `jbasic11.bin`.

## Command

```sh
sync/basic_cart_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| cosim `JUKU_CART` byte visible at `0x4000` | `0xC3` |
| HDL D8 pager selects D22 for `0x4000..0x5FFF` | `0xF7` |
| HDL D22 drives `jbasic11.bin[0]` | `0xC3` |

## Remaining Boundary

- Exercise the BASIC path to a live prompt. `sync/basic_launch_probe.py` now
  documents that Monitor 3.3 reads both `jbasic11.bin` and the legacy BAS0-3
  image from the cartridge overlay and then executes in the `0x4000..0xBFFF`
  RAM window. The launch probe records this as a compatibility boundary because
  the local MAME source warns about Monitor 3.3/JBASIC compatibility and both
  BASIC images enter with absolute `JMP 0x0107`.
