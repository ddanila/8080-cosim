#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== C disk/FDC and complete ekta37 RWFLOPPY deblocking/write check =="
sync/juk_disk_check.sh

echo "== HDL WD1793 synthetic-sector check =="
iverilog -g2012 -o "$TMP/fdc_1793_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/fdc_1793_tb.v
out=$(vvp "$TMP/fdc_1793_tb")
echo "$out"
grep -q "FDC-1793: PASS" <<<"$out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 vendored-media check =="
disk_out=$(vvp "$TMP/fdc_1793_tb" +disk=media/disks/JUKU1.CPM +disk_heads=2 +expect_disk)
echo "$disk_out"
grep -q "FDC-1793: PASS" <<<"$disk_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 writable-copy write-sector check =="
cp media/disks/JUKU1.CPM "$TMP/JUKU1-writable.CPM"
writable_out=$(vvp "$TMP/fdc_1793_tb" \
  +disk="$TMP/JUKU1-writable.CPM" +disk_heads=2 +disk_writable \
  +expect_disk +expect_writable)
echo "$writable_out"
grep -q "FDC-1793: PASS" <<<"$writable_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== juku_top decoded peripheral bus check =="
sync/juku_top_periph_bus_check.sh

cat > docs/fdc-readiness.md <<'EOF'
# FDC readiness

Status: **BOOT-SCOPED HDL FDC READY**

`sync/fdc_check.sh` guards the FDC behavior needed by the proven Juku boot
path. It does not claim a complete WD1793/VG93 implementation or complete
physical D93/D94 wiring.

## Passing scope

- Restore, seek, step, step-in, step-out, read-sector, write-sector,
  track/sector/data registers, BUSY/DRQ/INTRQ, side select, and
  motor-not-ready behavior.
- A 512-byte synthetic sector transfer and bytes from vendored
  `media/disks/JUKU1.CPM`.
- The exact ROMBIOS `0xA0/0xA2` write-sector path writes 512 bytes to an
  explicitly writable temporary image and reads them back byte-for-byte.
  Repository media stays read-only by default; HDL needs `+disk_writable`,
  and cosim needs `JUKU_DISK_WRITABLE=1`, on a caller-provided copy.
- The C guard first boots exact `ekta37` far enough to install its monitor RAM
  services, then drives the public ROMBIOS `RWFLOPPY` vector at `0xFF59`. It
  starts with a cold partial write, automatically prereads nonzero physical
  sector 3 with command `0x80`, caches three distinct 128-byte logical-record
  writes, reads all four cache offsets without another FDC command, and switches
  host sectors so the wrapper flushes once with `0xA2` before loading sector 4
  with `0x80`. All calls traverse
  the boot-installed `0xD7E7` monitor services and return with zero `ERRC`;
  persisted readback proves all three modified 128-byte records and the one
  untouched original record byte-for-byte.
- A second writable phase passes CP/M write type `C=2` for logical record 17,
  then writes records 18 through 20 sequentially. Exact ROM code seeds
  `UNACNT=32`, advances it to 28, and builds the complete 512-byte cache without
  any FDC preread. Crossing to record 21 produces only `0xA2,0x80`; physical
  sector 5 matches all four independent DMA patterns byte-for-byte.
- The RAM-drive phase selects EKDOS drive 2 and uses the source-defined stack
  at `0xD2FC`, outside the banked `0x4000..0xBFFF` aperture. Exact ROM code
  writes and reads independent sector-0 and sector-127 patterns across tracks
  0..11, both 16 KiB halves of all six port-`0x04` banks, and the complete
  192 KiB source-declared capacity. It reaches bank-5 offset `0x7F80`, restores
  normal bank 6 after every 32-byte slice, and issues zero FDC commands.
- The public `RAMDISKSEL` vector is executed through exact ROM bytes
  `0xFF5C -> 0xE9B3`. With bank switching unavailable it complements and
  restores ordinary RAM before returning `0xFF`; with RAM present it writes
  the 12-byte `RamDisk` signature plus 63 `0xE5` directory-entry markers,
  preserves BC, restores bank 6, and reopens a signed drive without formatting.
- The fixture checkpoint now comes from the real disk-backed `TDD` boot at the
  EKDOS `A>` prompt boundary (`14,200,002` cycles), so the installed BIOS jump
  table is present in RAM. Public `HOME` at `0xCA18` is executed with both
  cache states: it always sets `SEKTRK=0`, clears `HSTACT` when `HSTWRT=0`,
  and preserves the active cache when `HSTWRT=1`, so dirty data is not lost.
  Public `SELDSK` at `0xCA1B` runs through its
  `DoFunction`/ROMBIOS trampoline: drives A/B/C return contiguous 16-byte DPHs,
  unavailable C and invalid drive 3 return zero, invalid selection preserves
  the prior drive, and present C selects `SEKDSK=2` without a synthetic write.
- All 24 RAM-drive endpoint writes and 24 reads now enter through installed
  EKDOS BIOS vectors `SETTRK=0xCA1E`, `SETSEC=0xCA21`, `SETDMA=0xCA24`,
  `READ=0xCA27`, and `WRITE=0xCA2A`. Setter effects are checked in the shared
  work area, WRITE types 0 and 2 are both exercised, and every public I/O call
  returns zero after traversing `DoFunction` and the ROMBIOS mover.
- Public `SECTRAN=0xCA30` is executed for every floppy logical-sector index
  0..39 using the translation pointer returned in drive A's DPH; all results
  match the source `TRANS` permutation. Calls with the RAM-drive null table
  preserve endpoint sectors 0 and 127, covering both branches of the BIOS ABI.
- Read-only-backend write-track rejection with WRITE PROTECT instead of an
  endless BUSY state.
- The public `RWFLOPPY` guard also reopens the completed image read-only, dirties
  a cold cache, and crosses host sectors. Exact ROM code consumes `RCOUNT=10`,
  observes WRITE PROTECT on ten rejected `0xA2` attempts, accepts zero data
  bytes, and leaves the image unchanged. It then issues the new-sector `0x80`
  read and returns `ERRC=0`; the successful read masks the failed dirty flush.
  This is a guarded historical firmware boundary, not claimed error safety.
- Direct decoded `juku_top` keyboard/PIC/PPI/FDC bus access through
  `sync/juku_top_periph_bus_check.sh`.
- The committed uninterrupted Verilator report
  `docs/juku-top-fdc-verilator-probe.md` drains all 10,752 FDC data-register
  reads and reaches the EKDOS `A>` bitmap; `sync/juku_top_fdc_prompt_check.sh`
  checks that evidence and can opt into the expensive rerun.
- `docs/juku-top-fdc-alignment.md` summarizes the current reset-to-prompt
  boundary against the C oracle.

## Write-path provenance

- Vendored `EKDOS30.ASM` defines `DKWR=0x12` and passes it to the ROMBIOS
  `RWFLOPPY` entry at `0xFF59`.
- Exact `roms/ekta37.bin` disassembly branches on request `0x12` at `0xE67C`,
  selects WD1793 command `0xA0` or `0xA2` at `0xE69F/0xE6A4`, writes the
  command to port `0x1C` at `0xE6AB`, and loops 512 bytes from memory to the
  data register at port `0x1F` from `0xE6AF`.
- `tests/rombios_fdc_write_test.c` executes the complete public `RWFLOPPY`
  deblocking/cache wrapper and its nested `FLOPPY` handler from the vendored ROM
  in an authentic boot-initialized RAM environment instead of duplicating them
  as test-side port writes or patching the ROM epilogue.
- The implementation intentionally stops at that firmware-proved single-sector
  contract; it does not claim general WD1793 write-track or timing conformance.

## RWFLOPPY deblocking provenance

- The EKDOS request block at `0xD61A..0xD62F` supplies drive, 16-bit track,
  logical sector, cache state, and DMA address to the `0xFF59 -> 0xE80B`
  wrapper. Its physical-sector calculation at `0xE8B2` maps four consecutive
  128-byte logical records onto one 512-byte FDC sector.
- The guard seeds physical sector 3 with a nonzero byte pattern, starts with a
  cold-cache write to logical record 9, then writes records 10 and 12 from two
  other DMA patterns. The first `DKWR` itself issues `0x80` to preserve the host
  sector before changing one record. Reading records 9 through 12 into four
  different DMA buffers reproduces all three new patterns and the untouched
  original record 11, issues no further FDC command, and preserves `HSTWRT=1`.
  Reading record 13 then crosses into physical sector 4, takes one dirty-cache
  flush before the new read, and yields `0x80, 0xA2, 0x80`.
- Physical readback requires the changed first, second, and fourth 128-byte
  records plus the untouched original third record. This exercises the full
  four-way deblocking layout, cold read-before-write, and coalescing while
  distinguishing them from direct 512-byte model-side sector injection.
- The unallocated-write branch at ROM `0xE83E` copies CP/M write type `C`, and
  `C=2` seeds the 32-record sequence at `0xE84F`. Matching drive/track/sector
  progression clears the preread flag at `0xE89E`; after four writes the guard
  requires `UNACNT=28`, `HSTWRT=1`, and zero FDC commands. The host-sector
  transition then flushes once and reads the next sector, giving `0xA2,0x80`.
- When `SEKDSK` equals the RAM-drive number at `0xCA36`, `RWFLOPPY` branches to
  `0xEA3B`. Track bit 0 selects the lower (`0x4000`) or upper (`0x8000`) 16 KiB
  half, track bits above it choose one of six 32 KiB banks, and the 128-sector
  track maps sector bit 0 to the 128-byte half of a 256-byte page. The ROM moves
  each record as four 32-byte slices, selects/restores banks through port `0x04`,
  and stages data at `0xD200`; direct backing-store checks guard both track
  halves as well as public readback.
- EKDOS `MDISKPAR` independently fixes the geometry at 128 records per track,
  block shift 3 (1 KiB), and `DSM=191`: 192 KiB total, exactly six 32 KiB banks
  or twelve track halves. The executable guard writes every low/high endpoint
  before reading any back, so aliasing between banks, halves, or endpoint
  records cannot pass by immediate overwrite/readback coincidence.
- Source arithmetic fixes `BIOS=0xCA00`, hence standard jump-table entry 10
  (zero-based index 9) is `SELDSK=0xCA1B`; the prompt checkpoint guards the
  actual jump opcode and adjacent `NoofRamDisk=2`. `SELDSK` returns DPH offsets
  `+0/+16/+32`; the C-drive DPH has null translation and points to the exact
  15-byte `MDISKPAR` DPB. Its caller uses stack `0xD6F8`, while `DoFunction`
  saves that stack and temporarily owns source-defined `STAK=0xD2FC`.
- The source inspector requires all eight exercised disk-vector jump mnemonics
  in the archived assembly and derives their standard three-byte table
  addresses.
  The prompt checkpoint independently requires a live `JMP` opcode at each
  derived address; actual calls then prove their destinations and ABI rather
  than treating opcode presence as behavioral evidence.
- `RAMDISKSEL` does not merely select a register. Its probe relies on a failed
  bank command leaving ordinary RAM visible: it saves byte `0x4000`, attempts
  a complemented write after selecting bank 0, restores bank 6, and returns
  `0xFF` if ordinary RAM changed. A working bank instead receives the ROM's
  12-byte signature at `0x4000`, zeroed signature-entry tail, and `0xE5` in the
  first byte of directory entries 1..63. A matching signature bypasses this
  initialization; a retained byte guards that idempotent path.
- In the read-only phase, the exact command sequence is initial preread `0x80`,
  ten rejected `0xA2` retries from EKDOS `VIARV=10`, then the requested next-
  sector read `0x80`. The controller returns WRITE PROTECT throughout the retry
  loop and accepts no payload bytes. The wrapper nevertheless returns zero
  `ERRC` because the final successful read replaces the flush error; byte-for-
  byte media comparison proves that this masking does not imply a write.

## Commands

```sh
sync/juk_disk_check.sh
sync/fdc_check.sh
sync/ekdos_fdc_probe.py
sync/juku_top_fdc_prompt_check.sh
```

Checkpoint tools remain available for narrowing a regression, but their old
intermediate reports are not milestones now that uninterrupted reset-to-prompt
evidence exists.

## Remaining boundaries

- The model is a Juku boot/media shim, not a general WD1793 conformance model.
- Physical D93 INTRQ/DRQ, reset, clock, and D100 OE/T still require the targeted
  continuity checks in `docs/fdc-hardware-handoff.md`.
- D94 `.092` uses the validated physical table; direct continuity closes its
  enable to D93.CS, D1 to ground, D2 to D93.RE, D3 to D93.WE, and D4 to the
  D93 back-bias/NC socket contact. The runnable model consumes the physical
  D2/D3 strobes under explicit simulation-only enable, A3, and A4 fits. Their
  upstream physical sources plus D0/D5-D7 branches still block board release.
- Adopt a larger upstream controller core only if a concrete required command
  or timing behavior exceeds this guarded scope; re-evaluate license and
  adapter cost at that time.
EOF

echo "FDC-CHECK: PASS"
echo "Wrote docs/fdc-readiness.md"
