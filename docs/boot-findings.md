# Boot findings — RESOLVED: emulator boots to the banner

The `cosim/` software emulator now **boots the real BIOS and renders the boot
banner to video RAM**. Summary of the journey and the resolution.

## The banner (ekta37.bin, rendered from VRAM @ 0xD800, stride 40 = 320px)
```
EktaSoft '88  Serial #0037
Screen b/w 40x24/+wnd
Juku' Qwerty/sw kbd
Parallel printer
DiskBios (Fdc 1793 on MBoard*)
NetBios
Max Rom on Board: 4000
RomBios 3.43m
*                     <- prompt
```

## What the stall actually was
The boot looked hung for a long time. It was **not** the keyboard handshake (the
earlier guess). It was the **ROM self-test checksum**:
- `0x042C` = a block checksum (sums `[HL]` until `DE==0` or HL hits a 0x800
  boundary, `H&7==0`); compares the sum to a stored byte.
- On mismatch → `0x0408`/`0x0443`: a beep/strobe loop driven by `C` and big
  software delays, and the self-test **retries forever** → effectively hung.

## Root cause for ekta43: a stale checksum byte
- ekta43 block-1 (`0x000B..0x07FF`) sums to **0x57**, but the stored checksum at
  **0x000A is 0xF2** → self-test fails → infinite retry.
- **Checksum survey of `~/Downloads/juku/`** confirmed our logic and isolated it:
  | ROM | block-1 | stored | |
  |---|---|---|---|
  | ekta24/31/32/35/37 | = stored | ✓ | official, pass |
  | **ekta43** | 0x57 | 0xF2 | ✗ stale (homebrew AT-kbd mod) |
  | jbasic11 (cart), jmon33 (proto) | — | — | different format |
- So `ekta43.bin` has a genuine stale checksum (the homebrew author changed code
  but didn't update 0x000A). `trace.c` patches that one byte at load so it boots;
  **ekta37 (official) boots with no patch** and is the better default.

## State of the behavioral track
- Boots, banks (mode 0↔1), draws the banner. `render.py` turns VRAM → PNG.
- Next for "react to commands": feed keystrokes at the `*` prompt (8255 Port A/B
  keyboard), optionally model the frame interrupt for cursor/timing, and wrap a
  small CLI so an LLM can drive it (write key, step, read VRAM).
- ekta43's 53x24 screen uses a different framebuffer stride than ekta37's 40x24;
  render stride must match the ROM's screen-width register.
