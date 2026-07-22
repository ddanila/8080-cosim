# FDC readiness

Status: **BOOT + TYPE-I/II/III-TIMING/LOST-DATA/DELETED-RECORD/INTRQ HDL FDC READY**

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
  the `h` and `V` flags control the modeled head-load latch, while the visible
  HEAD LOADED status bit is the specified `HLD && HLT`. Fifteen rising
  index edges while idle automatically release HLD exactly as specified;
  index edges while BUSY do not count, and Type I-III command activity restarts
  the idle interval while an idle Type-IV event arm leaves it running. The four
  rate codes map at 2 MHz to 6,000/12,000/20,000/30,000 ticks (3/6/10/15 ms)
  and at 1 MHz to doubled 12,000/24,000/40,000/60,000 CPU-equivalent ticks
  (6/12/20/30 ms): STEP/DIRC and head motion occur at the step phase, BUSY spans
  the selected post-step interval, and `V=1` adds 15 ms at 2 MHz or 30 ms at
  1 MHz before waiting for HLT. Once HLT is high, a matching flat-image ID
  completes verification and a valid-CRC wrong-track ID reports SEEK ERROR
  immediately; a missing flat-image ID remains BUSY for three index pulses and
  reports SEEK ERROR on the fourth revolution. Restore samples active-low TR00,
  emits at most 255 outward steps, and reports SEEK ERROR if TR00 never asserts;
  the Type-I TRACK 0 status bit is the live inverse of that input. A silent D0 retains every
  already-issued partial seek step. C advances this contract from executed 8080 cycles; focused HDL
  unit/decoded guards enable it with `FDC_TYPE_I_TIMING`. Recovered sheet 3 now
  closes D95's selected 1/2 MHz source onto D93.24. The extended EKDOS I/O replay
  observes 18,489 D93 accesses and proves PC3 selects 1 MHz for every one; the
  C and HDL timers consume that selector. Oscillator accuracy and edge quality
  remain physical bring-up boundaries, while the source and waveform
  of the now-modeled HLT input remain a physical D93.23 boundary. The physical
  drive-status source for TR00 remains a D93.34 continuity boundary; the C
  harness defaults it asserted and `juku_top` retains its explicit functional
  low tie without claiming that as board copper.
  The same models cover single/multiple-record read-sector and write-sector, Read
  Address, Read Track, and writable Write Track formatting,
  track/sector/data registers, BUSY/DRQ/INTRQ, side select, and
  motor-not-ready behavior.
- For every accepted Type-II/III opcode, `E=1` now holds BUSY with DRQ low for
  30,000 ticks / 15 ms at 2 MHz or 60,000 CPU-equivalent ticks / 30 ms at
  1 MHz before ID search or
  the Type-III index wait begins; `E=0` starts without that interval. C advances
  the interval from executed 8080 cycles, and focused HDL unit/decoded guards
  enable the matching timer with `FDC_TYPE_II_III_TIMING`. Exact boundary tests
  cover both clock selections, and a silent D0 cancels the pending interval.
  With `E=0` the controller waits for HLT immediately; with `E=1` it waits after
  the settle interval. Both hold BUSY with DRQ low and begin media access on the
  HLT rising edge. The physical D93.23 HLT source/waveform and D93.24 oscillator
  accuracy/edge quality remain measurement boundaries rather than assumed timing.
- C and HDL sample the external READY input when every Type-II/III command is
  loaded. READY low completes immediately with BUSY/DRQ clear, NOT READY set,
  and INTRQ asserted, including commands carrying the optional E delay; Type-I
  motion still executes while its status reports NOT READY. Raising READY clears
  that live status indication. The C functional harness defaults the external
  input high, matching `juku_top`'s explicit behavioral-FDC tie; neither choice
  claims the still-untraced physical source at D93.32.
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
  Write Sector raises its matching-ID DRQ across the datasheet's 22-byte MFM
  ID-to-write-gate interval (1,408 nominal ticks): a supplied first byte is
  held without changing media, while an unserviced preload terminates with
  LOST DATA exactly at the boundary. Every multiple-record continuation
  re-arms that preload interval. Once streaming begins, the ordinary one-byte
  deadline applies. Write Track instead raises its initial DRQ as a preload request: the deadline does
  not age while the controller waits for index, the preloaded byte is held
  without touching media, and the first rising index either starts formatting
  or terminates with LOST DATA if no byte was supplied. After writing starts, a
  missed request substitutes
  `0x00`, sets LOST DATA, and continues. C/HDL unit guards prove all four cases,
  including the exact 1,407/1,408 boundary, unchanged media, persisted zero
  substitution, and per-record re-arming; the decoded
  top-level guard proves read overwrite and S2 through D94 plus logical DB and
  both diagnostic inversion-profile families. The byte deadline follows the MFM data rate and is
  intentionally not doubled with the D95 controller-clock selection. The C oracle
  advances the deadline from executed 8080 cycles, while the autonomous HDL
  timer is enabled only in focused unit/decoded guards with `FDC_BYTE_TIMING`;
  the uninterrupted physical top remains untimed until that waveform is calibrated.
- Type-II bit 4 continues across records and increments the sector register.
  Read and writable-image guards traverse sectors 9 and 10 byte-for-byte,
  advance to sector 11, and terminate with Record Not Found exactly as the
  datasheet specifies when the register exceeds the ten-sector track. A
  mid-command silent `0xD0` Force Interrupt stops the transfer while preserving
  the current incremented sector; the writable guard proves both completed sectors persist.
  Inter-record index/gap delays remain timing boundaries rather than invented
  rotational behavior in this byte-level shim.
- Type-II Data Address Mark behavior follows the FD179X command/status tables.
  Write Sector `a0=0` records a normal `0xFB` mark and `a0=1` records deleted
  `0xF8`; a completed Read Sector exposes the selected mark as bit-5 RECORD
  TYPE without confusing a deleted record with WRITE FAULT. The payload-only
  Juku raw format cannot serialize marks, so both backends keep one explicit
  bit per sector. Normal/deleted writes,
  multi-record transitions, Read Sector status, Write Track `FB`/`F8` parsing,
  and Read Track mark/CRC reconstruction are guarded in C and HDL; decoded
  top-level tests cover both Write Sector `a0` and Write Track `F8`. By default,
  closing and reopening the raw file resets this metadata to normal. An explicit
  1,600-byte companion file (`JUKU_DISK_DELETED_MARKS` in C or
  `+disk_deleted_marks=` in HDL) persists exactly one 0/1 byte per possible
  track/side/sector mark without changing the raw image; C and two-process HDL
  reopen guards prove the optional format.
- Type-II side flags follow the FD179X ID-search contract. With `C=0`, the
  recorded ID side is ignored; with `C=1`, the ID side bit must match `S`.
  The sector-only backend uses the selected image head as the reconstructed ID
  side. A mismatch holds BUSY with DRQ low through four index pulses, then
  completes with INTRQ and Record Not Found on the fifth. C, standalone HDL,
  and the decoded top-level bus guard cover the exact four/five-pulse boundary;
  matching `C=1` reads and writes cover both side values.
- A command-start Type-II search with no matching track or sector ID now keeps
  BUSY asserted and DRQ low for the datasheet's full four revolutions, then
  raises INTRQ with Record Not Found on the fourth index pulse. Exact read and
  write guards cover three-versus-four pulses, and the decoded top-level test
  exercises a missing sector-zero ID through the D94-selected register path.
  Flat-image multiple-record end-of-track still terminates deterministically
  when the incremented register exceeds sector 10; arbitrary rotational ID
  order remains a backend boundary.
- Read Address emits the complete six-byte ID field
  `{track, side, sector, length, CRC1, CRC2}`. Both models use the WD1793
  datasheet's `x^16+x^12+x^5+1` polynomial, all-ones preset, and ID address
  mark-through-length coverage; the 512-byte image geometry fixes length code
  2. Completion copies the returned track address into the sector register as
  specified, while a Force Interrupt during the ID transfer leaves the prior
  sector register unchanged. A flat sector image has no rotational position,
  so the deterministic shim returns sector 1, the first ID after index; this is
  an explicit image-format boundary rather than an invented rotation model.
- Read Track accepts the datasheet-defined `0xE0`/`0xE4` opcodes, asserts BUSY
  immediately, exposes neither DRQ nor data before the first rising index, then
  returns exactly one 6,250-byte revolution, raises INTRQ on the last byte, and
  leaves the sector register unchanged. The byte stream reconstructs
  all ten MFM ID/data fields from the raw image: 32-byte index gap; per-sector
  12-byte sync, three decoded `0xA1` missing-clock sync bytes, `0xFE` ID mark,
  CHRN and CRC; 22-byte gap; another sync/A1 run, the mounted metadata's `0xFB`/`0xF8`
  data mark, 512 payload bytes and CRC; 35-byte gap; then 128 bytes of end gap.
  This is the exact
  2,000 ns-cell/32-22-35 descriptor recorded by MAME's Juku format at commit
  `40d8c5c343efc497524832d59a6d0e2b8e59376b`; the C guard compares every byte,
  and the HDL plus decoded top-level guards check structure, CRCs, all ten IDs,
  vendored sector data, completion, status acknowledgement, and silent D0 abort
  through logical DB and both diagnostic profile families. MAME explicitly labels
  those gap counts unverified, and a sector-only image cannot preserve original
  gap contents, missing-clock waveforms, or rotational phase, so this is a
  deterministic media reconstruction rather than a claimed flux capture.
- On an explicitly writable image, Write Track accepts the corresponding
  index-to-index MFM formatter stream from the vendored FD179X datasheet's
  Type-III/IBM System 34 tables. Its command-time DRQ preloads one byte without
  starting the byte deadline or modifying media; the first rising index starts
  with that byte, while a missing preload terminates with LOST DATA. `F5` emits
  a missing-clock `0xA1`, `F6` emits missing-clock `0xC2`, and each `F7` emits
  both generated CRC bytes, so
  the canonical ten-sector Juku layout consumes 6,230 CPU data writes while
  producing 6,250 on-disk bytes. Both models parse all ten CHRN fields, require
  track/side/sector/512-byte geometry representable by the flat image, and
  persist every completed data field and its normal/deleted mark in mounted
  metadata. The writable guards read all ten sectors back; a mid-track D0 test
  proves sector 1 persists while untouched sector 2
  remains byte-identical, matching a non-atomic physical abort. A full
  unrepresentable gap-only revolution completes with the modeled WRITE FAULT
  bit and leaves the flat image unchanged instead of silently claiming that
  unrepresentable flux/ID metadata was saved. Read-only and motor-off commands
  still complete with WRITE PROTECT and NOT READY respectively. Actual index
  timing, arbitrary sector geometry, and partial gap/header damage remain
  explicit backend/timing boundaries. Cross-reopen deleted marks are supported
  only through the explicit companion format, not inside payload-only
  `.juk`/`.CPM` files.
- A 512-byte synthetic sector transfer and bytes from vendored
  `media/disks/JUKU1.CPM`.
- The generic КР580ВА87/8287 model complements all 256 byte values in both
  directions. Two control families remain exercised solely as unmapped
  firmware-profile diagnostics. The same exhaustive guard proves D23-D25's
  physical bidirectional behavior, including D25's traced turnaround input.
  Factory sheet 1 independently assigns physical D100 to drive outputs, not DB.
- The decoded top-level harness runs multi-read over vendored sectors 9/10,
  multi-write/readback, and a full 6,230-write MFM track format over an isolated
  writable copy in the logical DB build and both unmapped inversion-profile builds.
  The format path reads sectors 1 and 10 back byte-for-byte; all three
  multiple-record paths reach sector 11 with RNF. These semantics are exercised
  through D94 strobes and both diagnostic profile families rather than only
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
  byte column 2 to 3, and observes the installed `D7E7` trampoline. Its
  precondition accepts either uniform `00` or `FF` for the Monitor's ten-byte
  blinking cursor phase, then normalizes the cell before the glyph check;
  realistic FDC polling changes elapsed blink phase, not character output.
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
- Factory sheet 1 proves the behavioral controller's direct system-`DB` path.
  `docs/fdc-bus-polarity.md` proves two preserved firmware profiles: EktaSoft
  2.4 and Monitor 3.3 wrap every VG93 transfer in `CMA`, while EktaSoft
  3.1/3.5/3.7 use NOPs. The former remains an unmapped diagnostic inversion
  adjunct (`JUKU_FDC_BUS_INVERT=1`); fitted D15/D16 dumps are still required,
  but physical D100 is now source-proved as the drive-output buffer.
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
  not a general WD1793 conformance model. D95 selector-dependent Type-I and
  Type-II/III E-delay intervals are guarded, but physical D93.24 oscillator accuracy/edges,
  physical D93.23 HLT generation, D93.34 TR00 drive-status continuity, and
  step-interface timing, arbitrary flux/sector layouts, inter-record delays,
  and physical rotational timing remain outside
  its proved scope. Command-load READY sampling and Type-IV READY-transition and
  index-event semantics are guarded, but the board's physical D93.32 READY
  source, event pulse widths, and rotational timing remain outside this
  byte-level shim.
- Physical D93 DRQ and reset are now owner-closed: DRQ reaches D28.11 and the
  10k R94 pull-up to +5 V; D1.12 RESET reaches D13.9 and inverted D13.8 drives
  D93.19 plus the outer-bus rightmost middle-row contact (top view). INTRQ and
  the clock waveform still require bench calibration
  checks in `docs/fdc-hardware-handoff.md`. D100's drive-output channels are
  source-proved; shared pins 9/11 continue to an unresolved sheet-1 conductor,
  and the pin-6 write-data input is source-closed to D101.9.
- D94 `.092` uses the validated physical table. All five address inputs are
  owner/source-closed: BA0, BA1, IORD, qualified IOWR from D105.3, and D101.7
  Q0. D1 drives D99.9 through its pull-up, while D2/D3 drive D93 `/RE` and
  `/WE`; D4-D7 are owner/drawing-closed no-connects. The runnable model consumes
  those physical paths. Remaining board-release boundaries are the upstream
  source beyond the local D94.15/D93.3 enable join and D0's hidden load beyond
  its measured R8 pull-up.
- Adopt a larger upstream controller core only if a concrete required command
  or timing behavior exceeds this guarded scope; re-evaluate license and
  adapter cost at that time.
