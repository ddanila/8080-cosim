# VJUGA ROM images

## `ekta37_z80.bin` — Z80-executable Juku boot ROM (derived)

VJUGA uses a **Z80** CPU so the board runs from a single +5 V rail: the original
Juku CPU is a КР580ВМ80 (8080) needing +5 / +12 / −5 V, and dropping it removes
two supplies — the whole point of the minimal board.

The stock Juku firmware (`../../../roms/ekta37.bin`) is 8080 code, and three of
its bytes are 8080 "undocumented NOP" opcodes that a Z80 decodes as real
instructions (`EX AF,AF'` / `DJNZ` / `JR NZ`), so a stock Z80 diverges within
the first 40 opcode fetches. `ekta37_z80.bin` rewrites exactly those three
opcode bytes to canonical `NOP` (`0x00`), plus one checksum byte (below):

| Offset | Original | Patched | 8080 meaning | Z80 (stock) meaning |
| --- | --- | --- | --- | --- |
| `0x0021` | `0x08` | `0x00` | NOP | `EX AF,AF'` |
| `0x0024` | `0x10` | `0x00` | NOP | `DJNZ e` |
| `0x0026` | `0x20` | `0x00` | NOP | `JR NZ,e` |
| `0x000A` | `0x1A` | `0xE2` | block-1 checksum (data) | block-1 checksum (data) |

The opcode swaps are **length-preserving** (all absolute addresses unchanged)
and **8080-behavior-identical** (both bytes are NOP on the 8080). On a Z80 the
patched ROM now follows the same control flow.

**Checksum:** the ROM self-tests by summing block-1 (`0x000B..0x07FF`) and
comparing it to the stored byte at `0x000A`; a mismatch stalls the boot (this is
exactly what fails the homebrew `ekta43` ROM). The three opcode patches lower
the block-1 sum by `0x38`, so the stored checksum is recomputed from `0x1A` to
`0xE2`. `0x000A` sits outside the summed range, so the fix does not cascade, and
the self-test passes again. Verified: the 8080 `cosim` runs the patched ROM
byte-for-byte identically to the original through 200M cycles (banner + past the
self-test), confirming no other checksummed block is disturbed.

Only these three bytes are reachable as divergent opcodes during boot; no
`0xCB/0xDD/0xED/0xFD/0xD9` alternate JMP/CALL/RET encodings are executed, so no
further opcode patches are needed for the boot path.

### Provenance / regeneration

- Source ROM: `roms/ekta37.bin` — SHA256 `fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`
- Derived ROM: `ekta37_z80.bin` — SHA256 `343ef2e6f0e5358bdc52cab7117f54ec583c0dc754499f5518ff8933bbc7befa`
- Generator: `../tools/make_z80_rom.c` (trace-driven: patches only bytes the boot
  fetches as opcodes, over the same memory map cosim uses).

Regenerate and verify (from repo root):

```sh
cc -O2 -I cosim -o /tmp/mkz80 spinoffs/minimal-vga/tools/make_z80_rom.c cosim/i8080.c
/tmp/mkz80 roms/ekta37.bin spinoffs/minimal-vga/roms/ekta37_z80.bin
```

`sim/boot_check.sh` regenerates this file, checks it is byte-identical to the
committed copy, confirms cosim is unchanged by the patch, then boots it on the
VJUGA T80 core in **Z80 mode** and compares the framebuffer to cosim.
