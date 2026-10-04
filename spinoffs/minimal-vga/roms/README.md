# VJUGA ROM images

Build the complete Rev B first-article ROM set from the repository root:

```sh
python3 spinoffs/minimal-vga/roms/build_revb_rom.py
python3 spinoffs/minimal-vga/roms/build_revb_rom.py --check
```

The builder checks the pinned stock/patched EKTA, C10 and immutable C9 binaries,
builds DIAG from Python source, and writes the five derived binaries, diagnostic
instruction map and `revb-rom-set.json`. `--check` computes the same outputs and
compares them without writing. It does not regenerate the patched EKTA source or
reassemble C10; their own builders and execution gates remain separate.

Every 27C256 image
duplicates its verified 16 KiB member into both halves so direct A0–A14 wiring
also maps the D800–FFFF overlay correctly. `revb-rom-set.json` is the authority
for provenance, hashes and the program/readback procedure:

| Label | File | SHA-256 |
|---|---|---|
| EKTA3.7/VJUGA | `ekta37_z80-27c256.bin` | `e06dc0ee989d33049ad60c5a182df4d3da8814f206fd19c4f500603c772d9b2f` |
| NETC10/VJUGA | `netc10_vjuga-27c256.bin` | `6e84664b4513c1c3f8f2f717bbee5ed15495225636f1b2f2fe8de8924a889f3f` |
| DIAG/VJUGA | `diag_vjuga-27c256.bin` | `c220bf654711d8dda13e1e980763c11e00821b38bbdd55bd65c85a2b27f138a7` |

`EKTA3.7/VJUGA` is the retained programming/manifest label for the Z80-adapted
archive-0037 image, whose source banner is `RomBios 3.43m`. The label does not
identify a BIOS version 3.7. Its source is `roms/ekta37.bin`.

NETC10 is byte-identical to the reproducibly assembled C10 16 KiB source: its
canonical `zmac -8` instruction set needs no opcode substitutions, and its real
D57 mode-2/count-four sequence is retained. DIAG's builder and instruction map
prove that stack/helpers are absent until ROM, RAM-data and RAM-address pass.
`check_revb_rom_set.py` executes DIAG under cosim and checks POST order, selected
PIT writes, late USART text and the framebuffer-write count. See the
[DIAG guide](revb-diag/README.md) for the exact scope and generated scratch file.

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
comparing it to the stored byte at `0x000A`; a mismatch stalls the boot. The three opcode patches lower
the block-1 sum by `0x38`, so the stored checksum is recomputed from `0x1A` to
`0xE2`. `0x000A` sits outside the summed range, so the fix does not cascade, and
the block checksum is restored. The executable boot gate compares original
and patched ROM framebuffers at its selected video-write limit; it does not
compare every CPU state or prove all firmware services equivalent.

Only these three divergent opcode bytes occur in the traced boot workload; no
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

`spinoffs/minimal-vga/sim/boot_check.sh` regenerates this file in a temporary
directory and checks it against the committed copy. It compares the original
and patched 8080 framebuffers, then boots the patched image on the VJUGA T80
core in **Z80 mode** and compares that framebuffer to cosim. This is boot
coverage, not general 8080/Z80 compatibility or physical EPROM qualification.
