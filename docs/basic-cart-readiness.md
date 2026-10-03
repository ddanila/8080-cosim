# BASIC cartridge readiness

Status: **PHYSICAL D8 CARTRIDGE WINDOW CLOSED / COSIM OPTION BOUNDED**

This guard compares the modeled physical-PROM decode with cosim for the optional
`jbasic11.bin` cartridge path:

- cosim loads `JUKU_CART=roms/jbasic11.bin` and exposes it in memory mode 2 at
  `0x4000..0xBFFF`: the 8 KiB image occupies `0x4000..0x5FFF`,
  with the remaining window filled with `0xFF`.
- The repeated physical D8 `.039` table returns `0xFF` for the `0x4000` row,
  so every socket select including D22 remains released. The HDL unit test
  proves that a populated D22 therefore cannot drive the bus in this state.
- `tests/cart_window.hex` copies a tiny routine to RAM, switches to mode 2,
  reads byte `0x4000` from the cartridge, switches to mode 3, and writes the
  byte to VRAM under cosim. That behavior is an explicit MAME-compatible option,
  not a claim about the stock physical `.039` program.

## Command

```sh
sync/basic_cart_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| cosim `JUKU_CART` byte visible at `0x4000` | `0xC3` |
| HDL physical D8 row at `0x4000` | `0xFF` |
| HDL D22 bus contribution | released (`Z`) |

The cosim assertion checks only the first byte copied to VRAM. The standalone
HDL test checks one D8 address row and D22 at offset zero; it does not sweep
the cartridge window, run BASIC, or measure a physical board.

## Remaining Boundary

- Monitor 3.3 cartridge BASIC remains an artifact/procedure/configuration
  boundary summarized in [the cartridge guide](cartridge-basic-boundary.md). A different PROM,
  strap, expander decode, or procedure may be required. Disk-side BASIC is
  independently proven and this optional branch is not a fabrication blocker.
