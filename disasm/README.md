# Annotated ROM disassemblies

SkoolKit-based, round-trip-guarded disassemblies of the vendored Juku ROMs —
all eight CPU ROM images and the BASIC cartridge are covered. The maintained
artifact is the **control file** (`.ctl`), containing labels, comments, and
code/data boundaries. The `.skool` file is generated from it and vendored for browsing; it
must always regenerate identically and reassemble to the exact pinned ROM
bytes. One guard covers every image: `sync/disasm_check.sh` (a generic-CI
step).

**Ctl-editing hazard**: SkoolKit decodes Z80, and the 8080-undocumented
bytes `08/10/18/20/28/30/38/CB/D9/DD/ED/FD` have different semantics and
may have different lengths on Z80. In particular, Z80 relative branches and
prefixes can make a `c` block's tail consume bytes past its boundary, producing
overlapping entries — the round-trip guard then fails with a shifted,
longer binary. An 8080 may execute these undocumented bytes with semantics
that differ from Z80; encountering one is not proof that the region is data.
Establish instruction
lengths and control flow against the CPU implementation and execution evidence
before extending code boundaries; the byte round trip cannot prove them.

## ekta37 (EktaSoft '88 Serial #0037, RomBios 3.43m)

- [`ekta37/ekta37.ctl`](ekta37/ekta37.ctl) — hand-maintained knowledge.
- [`ekta37/ekta37.skool`](ekta37/ekta37.skool) — generated disassembly.

The ROM contains code and data. In reset mode 0, the emulator maps all
ROM offsets `0000h-3FFFh` at the same CPU addresses. In modes 1/2, it maps
ROM offsets `1800h-3FFFh` at `D800h-FFFFh` for reads; the EKDOS monitor
vectors at runtime `FF50h` are ROM `3F50h`. This is banking, not a copy of
the high ROM into RAM. Addresses in the ctl/skool are ROM file offsets.

The runnable cosim and HDL protect this high ROM window from writes.
Only mode 0's low ROM overlay permits writes to underlying RAM; see
[the hardware map](../docs/hardware-map.md#cpu-and-memory). Read-address
relocation alone does not establish write behavior.

The code map includes the reset entry, monitor vector table, and
byte-verified NetBios entries from
[`../docs/ekta37-netbios-notes.md`](../docs/ekta37-netbios-notes.md).
Regions not yet proven code remain `b` (data) blocks; refine them in the ctl
as understanding grows, never by editing the skool.

## ekta43 (EktaSoft '90 Serial #0043, RomBios 2.43m, homebrew AT-keyboard mod)

- [`ekta43/ekta43.ctl`](ekta43/ekta43.ctl) — hand-maintained knowledge.
- [`ekta43/ekta43.skool`](ekta43/ekta43.skool) — generated disassembly.

The emulator uses the same banking for this image as for ekta37. Static
landmarks include the same `JMP 0017h` entry and monitor-vector table shape
at ROM `3F50h`; those bytes alone do not verify physical memory decoding.
Seeded landmarks include the boot PIT programming at `01DCh`, the shared
alternative/restore D54/D55 parameter routines (`0F03h`/`0F2Fh`), and the
AT keyboard layout table at `14AFh` — resident low ROM, consistent with an
interrupt-served keyboard. The round trip preserves the image's stale
block-1 checksum byte exactly (`F2h` at `000Ah`; see
[`../docs/ektasoft-rombios-lineage.md`](../docs/ektasoft-rombios-lineage.md)).
The open research question for this image — how the AT keyboard physically
connects — lives in the ctl workflow: trace the PIC setup, label the ISR.

## jmon22 (Juku Monitor v2.2, public museum image with corrupt blocks)

- [`jmon22/jmon22.ctl`](jmon22/jmon22.ctl) — hand-maintained knowledge.
- [`jmon22/jmon22.skool`](jmon22/jmon22.skool) — generated disassembly.

This disassembly exists to support the block-repair project in
[`../docs/jmon22-reconstruction.md`](../docs/jmon22-reconstruction.md). The
image is preserved exactly as dumped, including its proven-wrong byte
(`1EFCh` reads `9Ah`, evidence-proven `DAh`) — the round-trip guard pins the
*dumped* bytes. Blocks 6-7 (`3000h-3FFFh`) came from unstable physical
reads; the ctl marks them untrusted data and excludes them from code
discovery. The Monitor family boots differently from EktaSoft: only ~200
bytes of boot code run in place (checksum verifier over the stored table at
`0003h-000Ah`, PIT init, PPI init), then `3F40h-3FFFh` is copied to
`FF40h-FFFFh` for the relocated vector table. Static seeding is deliberately
minimal here, and the shared BASIC body (`03C8h..`) is documented by title rather than decoded.
It differs from jmon33 at the proven repair byte `1EFCh`; the vendored
disassembly preserves that mismatch.

## jmon33 (Juku Monitor v3.3, MAME default BIOS — repair reference)

- [`jmon33/jmon33.ctl`](jmon33/jmon33.ctl) — hand-maintained knowledge.
- [`jmon33/jmon33.skool`](jmon33/jmon33.skool) — generated disassembly.

All eight block checksums pass under the same convention as jmon22
(byte-verified: stored table at `0003h-000Ah`, block 0 covering
`0004h-07FFh`). Same Monitor memory model: short in-place boot, then the
`3F40h-3FFFh` vector region is copied to `FF40h-FFFFh`. Unlike jmon22, no blocks
are excluded for known read damage, so descent includes the vector slots. Passing additive checksums
does not prove that every byte is historically correct. Use it as a comparison
reference for jmon22's untrusted blocks 6-7, subject to the donor constraints in
[the reconstruction report](../docs/jmon22-reconstruction.md).

## Other EktaSoft variants (ekta24, ekta31, ekta32, ekta35)

- [`ekta24/`](ekta24/ekta24.ctl) — Serial #0024, RomBios 3.42, Juss keyboard,
  FDC 1791/2.
- [`ekta31/`](ekta31/ekta31.ctl) — Serial #0031, RomBios 3.43, 40x24.
- [`ekta32/`](ekta32/ekta32.ctl) — Serial #0032, RomBios 2.43; the stock
  comparison image for #0043, whose banner declares an IBM AT keyboard.
  The banners alone do not establish its source ancestry.
- [`ekta35/`](ekta35/ekta35.ctl) — Serial #0035, RomBios 3.43, 53x24, Juss
  keyboard.

The emulator uses the ekta37 banking for all four images. They have
`JMP 0017h` entries and `3F50h` vector tables and are seeded the same way.
See [`../docs/ektasoft-rombios-lineage.md`](../docs/ektasoft-rombios-lineage.md)
for their identity and configuration matrix.

## jbasic11 (Juku BASIC 1.1 cartridge, 8 KiB — data-only seed)

- [`jbasic11/jbasic11.ctl`](jbasic11/jbasic11.ctl) /
  [`jbasic11/jbasic11.skool`](jbasic11/jbasic11.skool)

The cartridge's physical runtime mapping is an explicitly open boundary
([the cartridge boundary](../docs/cartridge-basic-boundary.md)): under an org-0 reading its apparent
entry jump targets data (ASCII), so **this seed asserts no code at all** —
addresses are file offsets, everything is data blocks with titled
landmarks. The 7,224-byte BASIC body at offset `0100h` is byte-identical to Monitor 3.3
at file offset `03C8h`; Monitor 2.2 differs at its proven repair byte
`1EFCh`. This mapping-independent comparison supplied the donor byte for
the jmon22 block-3 proof. Code discovery starts when
the mapping boundary closes.

## Workflow

Run from the repository root with Bash and Python 3. Creating the SkoolKit
environment requires Python venv support and pip access to the package:

```sh
# Install the expected version:
python3 -m venv ~/.venvs/skoolkit && ~/.venvs/skoolkit/bin/pip install skoolkit==10.0

# After editing the ctl, regenerate the vendored skool:
~/.venvs/skoolkit/bin/sna2skool.py --hex --org 0 --start 0 --end 16384 \
  --ctl disasm/ekta37/ekta37.ctl roms/ekta37.bin > disasm/ekta37/ekta37.skool

# Guard (also runs in generic CI):
sync/disasm_check.sh
```

For each of the nine images, the guard checks the pinned ROM SHA256,
byte-identical regeneration of its vendored skool from the ctl, and exact
ROM-byte reassembly with `skool2bin.py`. These checks preserve bytes and generated
text; they do not verify comments, code/data classification or runtime mapping.

The guard installs SkoolKit 10.0 in a temporary environment only when
`sna2skool.py` is absent from `PATH`. Otherwise it uses the installed commands
without checking their version. To use the environment above, run:

```sh
PATH="$HOME/.venvs/skoolkit/bin:$PATH" bash sync/disasm_check.sh
```

## Caveats

- SkoolKit emits **Z80 mnemonics** for this 8080 machine. Round-trip is
  unaffected, but read carefully: byte `08h` displays as `EX AF,AF'`, which
  on the real КР580ВМ80А/8080 is an undocumented NOP; Z80-only semantics
  must never be inferred from the listing.
- `cosim/dis8080.py` renders documented instructions with Intel mnemonics, but
  returns one-byte `DB` entries for undocumented opcodes. In particular, it
  does not consume the two operands of `CBh` or `DDh/EDh/FDh`; linear output
  after one of those bytes can be misaligned. Check `cosim/i8080.c` and execution
  evidence for their modeled JMP/CALL semantics (`D9h` is modeled as RET).
