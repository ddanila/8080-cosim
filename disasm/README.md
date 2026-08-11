# Annotated ROM disassemblies

SkoolKit-based, round-trip-guarded disassemblies of the vendored Juku ROMs —
all nine CPU images are covered. The maintained artifact is the **control
file** (`.ctl`): labels, comments, and code/data boundaries accumulate
there. The `.skool` file is generated from it and vendored for browsing; it
must always regenerate identically and reassemble to the exact pinned ROM
bytes. One guard covers every image: `sync/disasm_check.sh` (a generic-CI
step).

**Ctl-editing hazard**: SkoolKit decodes Z80, and the 8080-undocumented
bytes `08/10/18/20/28/30/38/CB/D9/DD/ED/FD` have *different lengths* on
Z80 (JR family, prefixes). A `c` block whose tail reaches one of these
makes the Z80 decoder consume bytes past the block boundary, producing
overlapping entries — the round-trip guard then fails with a shifted,
longer binary. Real 8080 code never executes these bytes; if one shows up
as an opcode, the region is data or the block is misaligned. The seed
generators stop code discovery at these bytes for exactly this reason.

## ekta37 (EktaSoft '88 Serial #0037, RomBios 3.43m)

- [`ekta37/ekta37.ctl`](ekta37/ekta37.ctl) — hand-maintained knowledge.
- [`ekta37/ekta37.skool`](ekta37/ekta37.skool) — generated disassembly.

Memory model (byte-verified, see the ctl header): ROM `0000-17FF` executes in
place; ROM `1800-3FFF` is relocated to RAM at `+C000h` and executes at
`D800h-FFFFh` — the EKDOS monitor vectors at runtime `FF50h` are ROM
`3F50h`. Addresses in the ctl/skool are ROM file offsets.

The initial code map was seeded by recursive descent from the reset entry
and the monitor vector table, translating control-flow targets in
`D800h-FFFFh` back by `-C000h`, plus the byte-verified NetBios entries from
[`../docs/ekta37-netbios-notes.md`](../docs/ekta37-netbios-notes.md).
Regions not yet proven code remain `b` (data) blocks; refine them in the ctl
as understanding grows, never by editing the skool.

## ekta43 (EktaSoft '90 Serial #0043, RomBios 2.43m, homebrew AT-keyboard mod)

- [`ekta43/ekta43.ctl`](ekta43/ekta43.ctl) — hand-maintained knowledge.
- [`ekta43/ekta43.skool`](ekta43/ekta43.skool) — generated disassembly.

Same memory model as ekta37 (verified: same `JMP 0017h` entry, same monitor
vector table shape at ROM `3F50h`, same `+C000h` relocation of `1800-3FFF`).
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
`FF40h-FFFFh` and everything dispatches through that relocated vector table
and interrupts — so static seeding is deliberately minimal here, and the
shared BASIC body (`03C8h..` byte-identical to jmon33) is documented by
title rather than decoded.

## jmon33 (Juku Monitor v3.3, MAME default BIOS — healthy repair reference)

- [`jmon33/jmon33.ctl`](jmon33/jmon33.ctl) — hand-maintained knowledge.
- [`jmon33/jmon33.skool`](jmon33/jmon33.skool) — generated disassembly.

All eight block checksums pass under the same convention as jmon22
(byte-verified: stored table at `0003h-000Ah`, block 0 covering
`0004h-07FFh`). Same Monitor memory model: short in-place boot, then the
`3F40h-3FFFh` vector region is copied to `FF40h-FFFFh` and everything
dispatches through it. Because every byte is trusted, descent covers the
vector slots too, making this the best-covered seed. Its primary purpose is
structural: the healthy reference for aligning jmon22's untrusted blocks 6-7
(`3F40h-3FFFh` is 55% positionally identical to jmon22's; block 6 is ~1%
and will need routine-level alignment). Notable anchors: the ENSV TA Kub.I /
AT EKB credit, the Bootstrap v3.3 / FDC 1791 banner, and the
checksum-failure UI that reports the failing EPROM number.

## Covered-line variants (ekta24, ekta31, ekta32, ekta35)

- [`ekta24/`](ekta24/ekta24.ctl) — Serial #0024, RomBios 3.42, Juss keyboard,
  FDC 1791/2; the oldest serial.
- [`ekta31/`](ekta31/ekta31.ctl) — Serial #0031, RomBios 3.43, 40x24.
- [`ekta32/`](ekta32/ekta32.ctl) — Serial #0032, RomBios 2.43; the stock
  sibling of the homebrew #0043 and the reference for isolating its
  AT-keyboard modification.
- [`ekta35/`](ekta35/ekta35.ctl) — Serial #0035, RomBios 3.43, 53x24, Juss
  keyboard.

All four share the ekta37 memory model (verified: `JMP 0017h` entries,
`3F50h` vector tables, `+C000h` relocation) and are seeded the same way.
See [`../docs/ektasoft-rombios-lineage.md`](../docs/ektasoft-rombios-lineage.md)
for their identity and configuration matrix.

## jbasic11 (Juku BASIC 1.1 cartridge, 8 KiB — data-only seed)

- [`jbasic11/jbasic11.ctl`](jbasic11/jbasic11.ctl) /
  [`jbasic11/jbasic11.skool`](jbasic11/jbasic11.skool)

The cartridge's physical runtime mapping is an explicitly open boundary
(PLAN.md, "cartridge BASIC loading"): under an org-0 reading its apparent
entry jump targets data (ASCII), so **this seed asserts no code at all** —
addresses are file offsets, everything is data blocks with titled
landmarks. The BASIC body at offset `0100h` is byte-identical to the
Monitor images at `+2C8h` (mapping-independent, content-level fact) and
served as a donor in the jmon22 block-3 proof. Code discovery starts when
the mapping boundary closes.

## Workflow

```sh
# Install once (any machine; also done automatically by the check script):
python3 -m venv ~/.venvs/skoolkit && ~/.venvs/skoolkit/bin/pip install skoolkit==10.0

# After editing the ctl, regenerate the vendored skool:
sna2skool.py --hex --org 0 --start 0 --end 16384 \
  --ctl disasm/ekta37/ekta37.ctl roms/ekta37.bin > disasm/ekta37/ekta37.skool

# Guard (also runs in generic CI):
sync/ekta37_disasm_check.sh
```

The guard asserts three identities: the pinned `roms/ekta37.bin` SHA256, the
vendored skool regenerating byte-identically from the ctl, and
`skool2bin.py` reassembling the skool to the exact ROM bytes.

## Caveats

- SkoolKit emits **Z80 mnemonics** for this 8080 machine. Round-trip is
  unaffected, but read carefully: byte `08h` displays as `EX AF,AF'`, which
  on the real КР580ВМ80А/8080 is an undocumented NOP; Z80-only semantics
  must never be inferred from the listing. Cross-check questionable
  instructions with `cosim/dis8080.py` (exact Intel mnemonics).
- SkoolKit is pinned to 10.0; a version bump must regenerate the skool and
  re-run the guard.
