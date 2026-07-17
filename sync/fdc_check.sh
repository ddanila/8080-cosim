#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== C disk/FDC and complete ekta37 RWFLOPPY deblocking/write check =="
sync/juk_disk_check.sh

echo "== HDL КР580ВА87 bidirectional inversion check =="
iverilog -g2012 -o "$TMP/buf_8287_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/buf_8287_tb.v
buf_out=$(vvp "$TMP/buf_8287_tb")
echo "$buf_out"
grep -q "BUF-8287: PASS" <<<"$buf_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 synthetic-sector check =="
iverilog -g2012 -DFDC_BYTE_TIMING -o "$TMP/fdc_1793_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/fdc_1793_tb.v
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

Status: **BOOT + TYPE-II/TYPE-III/LOST-DATA/INTRQ HDL FDC READY**

`sync/fdc_check.sh` guards the FDC behavior needed by the proven Juku boot
path. It does not claim a complete WD1793/VG93 implementation or complete
physical D93/D94 wiring.

## Passing scope

- C/HDL-identical Type-I restore, seek, step, step-in, and step-out semantics.
  The physical head position is independent of the Track register: update-off
  steps move only the head, verify compares the next flat-image ID track to the
  register and reports SEEK ERROR on a mismatch, SEEK preserves any existing
  physical/register offset, and only RESTORE recalibrates both to track zero.
  Later sector commands reject a mismatched head/register pair. The Type-I status view dynamically
  reports TRACK 0, HEAD LOADED, INDEX, media write protection, and SEEK ERROR;
  the `h` and `V` flags control the modeled head-load latch. Exact step-rate,
  15 ms settle, 15-revolution unload, and external TR00/HLT timing remain
  physical timing boundaries. The same models cover single/multiple-record read-sector and write-sector, Read
  Address, Read Track, and writable Write Track formatting,
  track/sector/data registers, BUSY/DRQ/INTRQ, side select, and
  motor-not-ready behavior.
- C and HDL now share the WD1793 interrupt contract for the modeled commands:
  loading a command clears pending INTRQ, normal/error completion raises it,
  and reading status acknowledges it. Type-IV Force Interrupt `0xD0` terminates
  an active transfer silently; `0xD1` arms not-ready-to-ready, `0xD2` arms
  ready-to-not-ready, and `0xD4` arms every index pulse. Those event modes can
  reassert after a status acknowledgement until another command disarms them.
  `0xD8` asserts immediately and remains asserted across status reads until a
  `0xD0` or non-Force command disarms it. C, HDL, and decoded-bus guards cover
  the event edges, acknowledgement, reassertion, and disarm lifecycle.
- C and HDL share the datasheet-defined one-byte DRQ service deadline for an
  active Type-II/III byte stream. The
  modeled window is 64 2 MHz-equivalent ticks, i.e. one 32 us MFM byte at the
  Juku image's 250 kbit/s data rate. An unserviced read byte is overwritten by
  the next assembled byte, sets LOST DATA, and the command continues. An
  unserviced first Write Sector or Write Track request terminates before media
  changes; the byte-level shim conservatively applies the same bounded window
  while exact ID-to-data and command-to-index lead-in remain rotational
  boundaries. After the first byte is accepted, a missed write request substitutes
  `0x00`, sets LOST DATA, and continues. C/HDL unit guards prove all four cases,
  including unchanged media and persisted zero substitution; the decoded
  top-level guard proves read overwrite and S2 through D94 plus logical DB and
  both safe D100 families. Exact wall-clock calibration remains conditional on
  the measurement-gated physical D93.24 clock source. Accordingly, the C oracle
  advances the deadline from executed 8080 cycles, while the autonomous HDL
  timer is enabled only in focused unit/decoded guards with `FDC_BYTE_TIMING`;
  the uninterrupted physical top remains untimed until D93.24 is measured.
- Type-II bit 4 continues across records and increments the sector register.
  Read and writable-image guards traverse sectors 9 and 10 byte-for-byte,
  advance to sector 11, and terminate with Record Not Found exactly as the
  datasheet specifies when the register exceeds the ten-sector track. A
  mid-command silent `0xD0` Force Interrupt stops the transfer while preserving
  the current incremented sector; the writable guard proves both completed sectors persist.
  Inter-record index/gap delays remain timing boundaries rather than invented
  rotational behavior in this byte-level shim.
- Read Address emits the complete six-byte ID field
  `{track, side, sector, length, CRC1, CRC2}`. Both models use the WD1793
  datasheet's `x^16+x^12+x^5+1` polynomial, all-ones preset, and ID address
  mark-through-length coverage; the 512-byte image geometry fixes length code
  2. Completion copies the returned track address into the sector register as
  specified, while a Force Interrupt during the ID transfer leaves the prior
  sector register unchanged. A flat sector image has no rotational position,
  so the deterministic shim returns sector 1, the first ID after index; this is
  an explicit image-format boundary rather than an invented rotation model.
- Read Track accepts the datasheet-defined `0xE0`/`0xE4` opcodes, asserts
  BUSY+DRQ, returns exactly one 6,250-byte revolution, raises INTRQ on the last
  byte, and leaves the sector register unchanged. The byte stream reconstructs
  all ten MFM ID/data fields from the raw image: 32-byte index gap; per-sector
  12-byte sync, three decoded `0xA1` missing-clock sync bytes, `0xFE` ID mark,
  CHRN and CRC; 22-byte gap; another sync/A1 run, `0xFB` data mark, 512 payload
  bytes and CRC; 35-byte gap; then 128 bytes of end gap. This is the exact
  2,000 ns-cell/32-22-35 descriptor recorded by MAME's Juku format at commit
  `40d8c5c343efc497524832d59a6d0e2b8e59376b`; the C guard compares every byte,
  and the HDL plus decoded top-level guards check structure, CRCs, all ten IDs,
  vendored sector data, completion, status acknowledgement, and silent D0 abort
  through logical DB and both physical D100 families. MAME explicitly labels
  those gap counts unverified, and a sector-only image cannot preserve original
  gap contents, missing-clock waveforms, or rotational phase, so this is a
  deterministic media reconstruction rather than a claimed flux capture.
- On an explicitly writable image, Write Track accepts the corresponding
  index-to-index MFM formatter stream from the vendored FD179X datasheet's
  Type-III/IBM System 34 tables. `F5` emits a missing-clock `0xA1`, `F6`
  emits missing-clock `0xC2`, and each `F7` emits both generated CRC bytes, so
  the canonical ten-sector Juku layout consumes 6,230 CPU data writes while
  producing 6,250 on-disk bytes. Both models parse all ten CHRN fields, require
  track/side/sector/512-byte geometry representable by the flat image, and
  persist every completed data field. The writable guards read all ten sectors
  back; a mid-track D0 test proves sector 1 persists while untouched sector 2
  remains byte-identical, matching a non-atomic physical abort. A full
  unrepresentable gap-only revolution completes with the modeled WRITE FAULT
  bit and leaves the flat image unchanged instead of silently claiming that
  unrepresentable flux/ID metadata was saved. Read-only and motor-off commands
  still complete with WRITE PROTECT and NOT READY respectively. Actual index
  timing, deleted-data metadata, arbitrary sector geometry, and
  partial gap/header damage remain explicit backend/timing boundaries.
- A 512-byte synthetic sector transfer and bytes from vendored
  `media/disks/JUKU1.CPM`.
- The physical КР580ВА87/8287 device models complement all 256 byte values in
  both directions. D100 is tested under both safe control families:
  qualified `/OE=FDC_CS_N`, `T=D93_RE_N`, and the same-board precedent
  `/OE=GND`, `T=D93_RE_N`. Selected writes drive CPU `DB` to inverted `DAL`;
  selected reads drive `DAL` to inverted `DB`; an unselected or D94-suppressed
  read cycle either
  disables both sides or holds direction A->B so D100 cannot contend on CPU
  `DB`. The same exhaustive guard now proves D23-D25's full bidirectional model,
  including D25's traced turnaround input. Raw `IORD` is excluded as D100 `T`
  because D94 can suppress `/RE` on its low-A4 register-3 branch. These are
  functional constraints;
  they do not promote either still-unmeasured D100 conductor.
- The decoded top-level harness runs multi-read over vendored sectors 9/10,
  multi-write/readback, and a full 6,230-write MFM track format over an isolated
  writable copy in the logical DB build and both physical D100/DAL candidates.
  The format path reads sectors 1 and 10 back byte-for-byte; all three
  multiple-record paths reach sector 11 with RNF. These semantics are exercised
  through D94 strobes and both safe D100 control families rather than only
  inside the controller unit.
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
  table is present in RAM. Public cold `BOOT=0xCA00` runs to its non-returning
  `CCP=0xB400` handoff: it installs `JMP 0xCA03` and the exact `0xBC06` BDOS
  vector at low memory, sets DMA `0x0080`, clears the three cache fields,
  selects drive 0, formats a blank cloned RAM drive with its signature and 63
  directory markers, performs exactly 10,240 framebuffer writes through 144
  installed monitor-trampoline entries, and issues no FDC command.
  Public `WBOOT=0xCA03` is separately executed through the source-defined
  resident-BDOS branch by changing only the pointed high byte from `0xBC` to
  nonzero `0xB5`; it reaches the same CCP handoff, preserves `0xB506` in the
  low-memory BDOS vector, and performs no framebuffer or FDC work. The default
  `WRetry` branch is independently guarded after poisoning `0xB400..0xBDFF`:
  the Monitor's low-stack dispatcher writes its `0xFEE8` return frame into RAM
  beneath the low ROM read overlay, restores `SP=0x0100`, and START issues five
  exact `0x80` commands for physical sectors `3,2,4,6,5`. It consumes 2,560
  data bytes through 40 monitor trampolines, reloads system sectors 2..6 at
  their address-numbered 512-byte slots, and reaches CCP with the exact final
  bytes after the source-defined three-byte `CCPExit` patch. Public `HOME` at
  `0xCA18` is executed with both
  cache states: it always sets `SEKTRK=0`, clears `HSTACT` when `HSTWRT=0`,
  and preserves the active cache when `HSTWRT=1`, so dirty data is not lost.
  Public `LISTST` at `0xCA2D` starts with `A=0xA5` and executes source target
  `POLLPT`, returning `A=0` because the printer-status device is unimplemented.
  Public `PUNCH=0xCA12` and `READER=0xCA15` are both executed from nonzero A;
  the prompt checkpoint proves they share the same `XRA A; RET` target, and
  each returns unavailable as `A=0` without inventing auxiliary hardware.
  Public `CONST=0xCA06` traverses `DoFunction` to exact ROM monitor entry
  `CONSTA=0xFF98`; with the established released-matrix input `0xCF` and the
  prompt key buffer empty, it returns `A=0` (no character ready).
  Public `CONIN=0xCA09` traverses `DoFunction` to exact monitor entry
  `RDCHR=0xFFD3` and waits on the monitor's interrupt-fed keyboard buffer.
  The fixture drives the source-faithful shifted-`T` matrix position
  (column 4, encoder bit 3) while delivering the established 200,000-cycle
  frame IRQ at exact ROM vector `0xFED4`. Two frame services perform 34 matrix
  reads, sample the active `0x88` encoding twice, and return exact ASCII
  `T=0x54` through the public BIOS vector and installed `D7E7` trampoline.
  Public `CONOUT=0xCA0C` traverses `DoFunction` to exact monitor entry
  `WRCHR=0xFFD9`. At the prompt checkpoint, input `C='C'` renders the exact
  ten-scanline character cell at byte column 2 / rows 70..79: blank top row,
  glyph bytes `1C 22 20 20 20 22 1C`, and two blank bottom rows. The guard
  requires exactly ten framebuffer writes, advances the monitor cursor from
  byte column 2 to 3, and observes the installed `D7E7` trampoline.
  Public `LIST=0xCA0F` traverses exact `PrintCh=0xFFEE`, whose ROM jump reaches
  the boot-installed `D7F1->E2A2` USART service. With transmitter-ready bit 3
  asserted at status port `0x0E`, input `C='L'` is emitted exactly at data port
  `0x0C`. This path uses the installed direct service jump rather than `D7E7`.
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
- Read-only-backend Write Track rejection with WRITE PROTECT instead of an
  endless BUSY state, plus writable whole-track persistence and partial-abort
  behavior as described above.
- The public `RWFLOPPY` guard also reopens the completed image read-only, dirties
  a cold cache, and crosses host sectors. Exact ROM code consumes `RCOUNT=10`,
  observes WRITE PROTECT on ten rejected `0xA2` attempts, accepts zero data
  bytes, and leaves the image unchanged. It then issues the new-sector `0x80`
  read and returns `ERRC=0`; the successful read masks the failed dirty flush.
  This is a guarded historical firmware boundary, not claimed error safety.
- Direct decoded `juku_top` keyboard/PIC/PPI/FDC bus access through
  `sync/juku_top_periph_bus_check.sh`.
- The behavioral controller intentionally consumes logical system `DB` rather
  than the control-disconnected physical D100/DAL path. `docs/fdc-bus-polarity.md`
  proves the two firmware/hardware profiles: EktaSoft 2.4 and Monitor 3.3 wrap
  every VG93 transfer in `CMA` for the populated inverting КР580ВА87, while
  EktaSoft 3.1/3.5/3.7 use NOPs for a non-inverting path. `cosim/trace` models
  the former with `JUKU_FDC_BUS_INVERT=1`; fitted D15/D16 dumps and D100
  `/OE`/`T` continuity still decide the exact physical-board configuration.
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
- The firmware path intentionally stops at its proved single-sector contract.
  The independent command guard additionally covers multiple-record Type-II
  continuation, Read Address, reconstructed Read Track, and representable Juku
  MFM Write Track formatting and the datasheet one-byte LOST DATA contract, but
  neither model claims arbitrary-flux, rotational, or general timing conformance.

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
- The source inspector requires archival evidence for all seventeen exercised
  BIOS vectors and derives their standard three-byte table addresses. It
  deliberately guards the damaged PUNCH spelling `DP RTNEMPTY` as preserved
  evidence; the adjacent READER line retains `JMP RTNEMPTY`.
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

- The model is a Juku boot/media shim with datasheet-guarded Read Address,
  reconstructed Read Track, representable MFM Write Track, and Type-II
  multiple-record continuation and the datasheet one-byte LOST DATA contract,
  not a general WD1793 conformance model. Exact physical calibration of the
  byte deadline and initial-write rotational lead-in, Type-I
  step/settle/head-unload timing, arbitrary flux/sector
  layouts, deleted-data metadata, inter-record delays, and physical rotational timing remain outside
  its proved scope. Type-IV READY-transition and index-event semantics are
  guarded, but the board's physical event sources, pulse widths, and rotational
  timing remain outside this byte-level shim.
- Physical D93 INTRQ/DRQ, reset, clock, and D100 OE/T still require the targeted
  continuity checks in `docs/fdc-hardware-handoff.md`. The D100 component model
  and required cycle truth table are now guarded; only its board control sources
  remain open.
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
