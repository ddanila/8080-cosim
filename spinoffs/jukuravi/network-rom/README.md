# Juku network-first ROM

Status: **C12 / ABI 1.5 RUNTIME CONSOLE, CP/M, AND HOST SIMULATOR-QUALIFIED;
PHYSICAL ACCEPTANCE PENDING**

This is the from-scratch network-only successor to the EktaSoft monitor ROM.
Reset performs a bounded POST, acquires an identity-independent host at the
physically proven 19,200 baud, receives a checked CP/M Plus 3.1 image, and
hands the live machine to NetDisk v3 without a keypress.  The upper 10 KiB is
also the versioned common Juku platform layer used after boot.

The authoritative design and acceptance requirements are in
`~/fun/cpm-plus-juku/docs/network-first-rom-plan.md`.  The current release
line is deliberately additive:

- C4 / ABI 1.0 is the immutable automatic-boot reference.  C3 and C4 EPROM
  halves are byte-identical; C4 names the corrected matching CP/M runtime.
- C5 / ABI 1.1 adds reset-latched S21 policy, all four video geometries,
  English/Estonian/CP866 font banks, connected CP437 pseudographics, and four
  persistent key remaps.  Its combined ROM SHA-256 remains
  `9ed6273f44c1b09dcb5fcd3ca94e5a1aad813b285607558a7d8cb98b1a5e6e7a`.
  CS00015 passed the complete blind boot, keyboard, disk, diagnostic, warm
  boot, and live-reconnect matrix with this image; exact display/cursor
  observation remains a physical promotion item.
- C6 / ABI 1.2 appends bounded console-span, ordered multi-request NetDisk,
  instantaneous raw-keyboard, and sound services.  It changes none of the
  ABI 1.0/1.1 vector addresses or C5 bytes. C6 is qualified and packaged as a
  simulator release. The exact pair is fitted in CS00015 and passed every
  monitor-independent physical item; display/cursor observation remains.
  The frozen fitted image has one subsequently found raw-service limitation:
  with SHIFT or CTRL held, `JCGKEYRAW` can report column zero before reaching
  the ordinary key's column. Translated keyboard input and unmodified raw keys
  are unaffected. `juku-common` master contains the corrected scanner; it must
  enter a separately named future ROM candidate rather than rewrite C6.
- C7 is that separately named simulator successor. It retains ABI 1.2 and the
  C6 boot protocol, adds the VC-compatible CP437 box glyphs, and scans every
  ordinary matrix column before accepting a standalone global modifier. The
  build still reproduces the exact fitted C5 and C6 hashes before emitting
  `juku-network-rom-abi1.2-c7.bin`. Executable fixtures prove the exact
  Shift-F8 `(column 0Eh, PB 8Eh)` and Ctrl-Up/Home `(column 0Ah, PB 6Ah)`
  contacts with the intended S21 setting; physical acceptance remains a
  separately retained focused run.
- C8 / ABI 1.3 moves the remaining N4/host transport into resident ROM behind
  the appended `FF5Ch` selector vector, replaces the diagnostic placeholder
  with eight bounded tests, and repeats IBM-style three-tone short/long codes
  for POST failures C1--C5. The matching CP/M Plus system replaces 733 bytes
  of RAM transport with a 147-byte binding and raises TPA by 512 bytes. The
  exact C8 pair is fitted and blind-qualified in CS00015 and remains the
  physical rollback for C9 work.
- C9 / ABI 1.4 bounds transmitter readiness and whole-prefix acquisition,
  publishes stable failure/negotiation telemetry, and makes network boot
  unconditional with S21 bit 0 reserved. It preserves C8's TPA and all earlier
  vectors. C9 passes the C-model, structural HDL, CP/M local/remote, native-host
  write/time/diagnostic/warm-boot, live replacement, and `vc8080` N4 gates.
  The exact pair was physically evaluated on CS00000: all remote, disk,
  recovery, and host-replacement paths passed, but C9 left PPI0 PC7/POF high
  and suppressed local pixels despite valid sync. A live EKTA-style `0Eh`
  release restored video immediately. C9 remains immutable and is not
  promoted.
- C10 / ABI 1.4 adds the stock-compatible `0Eh` PC7/POF release after POST,
  verifies final Port C `01h`, and adds direct Port-C/POF status and diagnostic
  coverage. It preserves the exact C9 loaded system and Fastboot. The complete
  C-model fault matrix, C9-negative/C10-positive frame regression, structural
  HDL POF gate, local/remote CP/M, production native-host/replacement, and
  reproducible package gates pass. The named pair is ready to program;
  CS00000 local-video and full physical acceptance remain next.
- C11 / ABI 1.4 preserves C10 and its exact CP/M system, Fastboot, and adapter.
  Before releasing POF it constructs a deterministic 8x8 checkerboard across
  the complete stock 320x241 boot raster. Console initialization then clears
  a safe 9,648-byte physical-raster envelope, covering mode 0's extra scanline
  while retaining the 9,600-byte text surface. All four S21 geometries, local
  and remote CP/M, native-host/replacement, package, and reproducibility gates
  pass. Its C11-only boot loader also periodically emits a checked discovery
  beacon at NetDisk's 19,200/8O1 before returning to V16's 8N1 scanner. The
  production host can therefore distinguish a waiting loader from an already
  running CP/M, attach without a resume flag, and recover a reset seen during
  NetDisk. Focused physical confirmation of the checker, bottom line, and
  recovery pair remains. See `docs/c11-session-recovery.md`.
- C12 / ABI 1.5 preserves the exact C11 image and appends `FF5Fh` runtime
  console configuration. Software can query the reset-latched S21 default,
  atomically select any of four video geometries and four character banks,
  restore the default, and distinguish independent video/bank overrides. The
  switch resets cursor state and clears the full 9,648-byte raster envelope;
  it discards a pending key without erasing persistent key remaps, and invalid
  requests leave state and pixels unchanged. Active state uses the
  last two free bytes at `D7FDh..D7FEh`, while the fixed ABI workspace and TPA
  do not grow. C12 advertises a distinct checked `JB/12` discovery beacon, and
  the production host accepts both C11 and C12 recovery identities. The 4x4
  C-model matrix, focused structural HDL path, CP/M commands/package, and
  stock/C11/C12 Windows-host Wine sessions pass; physical acceptance remains
  separate. See `docs/c12-runtime-console.md`.

## Build and test

From `8080-cosim`:

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py
sync/network_first_rom_abi_check.sh
sync/network_first_rom_hdl_check.sh
python3 tests/janet_disk_server_test.py
```

The ABI gate rebuilds the images, executes C4 through C12 against the practical
C-model twin, and checks exact manifests, fixed vectors, stack guards,
interrupt ownership, overlay protection, all S21 geometries, locale pixels,
keyboard behavior, cursor phases, runtime mode/bank transitions, invalid-call
atomicity, and resident serial activity.  The focused
HDL gate retains the exact C4 reset/POST, call-gate, framebuffer, keyboard,
serial, and one-record NetDisk boundary; full CP/M, recovery, and long-soak
coverage remains in the faster C-model oracle.

The matching C8 rollback and C9/C10/C11/C12 system/TPA/local/N4 gates are run
from `cpm-plus-juku`:

```sh
make c8-check
make c9-check
make c10-check
make c11-check
make c12-check
```

The native production-host and reconnect gate is:

```sh
sync/jukuhost_c9_cosim_check.sh
sync/jukuhost_c10_cosim_check.sh
sync/jukuhost_c11_cosim_check.sh
```

The deterministic, explicitly non-physical C12 package is produced from
`cpm-plus-juku` with `make c12-simulator-candidate`. Its manifest records
`physical_programming_authorized: false`; physical promotion remains a
separate decision.

The burn-ready C10 package, its independent reproducibility check, and the
programming/acceptance worksheet are produced from `cpm-plus-juku` with
`make c10-release-candidate`.

The C11 burn-ready package and focused visual worksheet are produced with
`make c11-release-candidate`.

From `cpm-plus-juku`, the complete C6 release gate is:

```sh
make c6-release-candidate
```

It re-runs the ROM ABI gate, exercises both authoritative local console and N4
remote console paths, performs the 64-cycle read/write/reconnect soak, and
then writes a byte-reproducible candidate containing the combined ROM, named
D15/D16 halves, matching CP/M system and bootstrap, A:/B: volumes, fallback
slot, manifests, hashes, and the complete ROM/RAM/vector map.

## Deterministic artifacts

- `juku-network-rom-abi1{,-d15,-d16}.bin` and JSON: immutable C4 / ABI 1.0.
- `juku-network-rom-abi1.1-c5{,-d15,-d16}.bin` and JSON: C5 / ABI 1.1.
- `juku-network-rom-abi1.2-c6{,-d15,-d16}.bin` and JSON: C6 / ABI 1.2.
- `juku-network-rom-abi1.2-c7{,-d15,-d16}.bin` and JSON: C7 / ABI 1.2
  modified-raw bench candidate.
- `juku-network-rom-abi1.3-c8{,-d15,-d16}.bin` and JSON: C8 / ABI 1.3
  resident-host simulator candidate.
- `juku-network-rom-abi1.4-c9{,-d15,-d16}.bin` and JSON: C9 / ABI 1.4
  bounded-host simulator/HDL candidate.
- `juku-network-rom-abi1.4-c10{,-d15,-d16}.bin` and JSON: C10 / ABI 1.4
  POF-release candidate ready for physical programming.
- `juku-network-rom-abi1.4-c11{,-d15,-d16}.bin` and JSON: C11 / ABI 1.4
  deterministic POST/checker and complete-raster-clear candidate.
- `juku-network-rom-abi1.5-c12{,-d15,-d16}.bin` and JSON: C12 / ABI 1.5
  runtime-console and versioned-recovery simulator candidate.

These named releases are immutable. In particular, rebuilding a modified
scanner under the C6 filenames is not a C6 update: the fitted combined image
remains SHA-256
`0487d5150f9b662a193b3f031aadd90002ee232477d355d3877a757a247c2f09`.
The C7 combined image is
`a05c74d948d9f01c5a89dc3ea69bfeb4fdf9ac48b3e37845d1edbf03e6e203b8`;
its D15-low and D16-high hashes are respectively
`8a1db7dcd0bdf6403bcd64ac7a7f12b278ae0c70778508ddbe90d4cc50e3f413`
and `5512b75f1550ec4c305b721ad0ee179556c938780a197b3bed1001366c7e4b94`.
The current C8 combined, D15-low and D16-high hashes are respectively
`a54cb877edfe25e939e05ada0e98783acb53cfc8969071c63928b119c8e09e46`,
`aa14d114a0176d3123b5d58366c45d05462c8a2127893fa996a533a9107d1773`,
and `1afbed0b22ec5ab8d32fffb9784c0e87a287f54ec65cb2b0565afa91552dc5ee`.
The C9 combined, D15-low and D16-high hashes are respectively
`352417fafcf1ceaef40b8d39916acdaee6de03d914eafe2b54185ccbabe35530`,
`b18e96e8f4cc88c7436e457b63b564ad42e1bf55f3e997f272301096c463593e`,
and `6f9bdf53bcf7ee919224305bcaf135c2d0076779218f49a2aed5395dc6baf932`.
The matching non-physical candidate archive is
`43b03802e156dba0492c860fe27a9fc1aec1672cf5dc0afab82176fbd243eb75`.
The C10 combined, D15-low and D16-high hashes are respectively
`fbf9baaad9027a5335e3549da3a396eb999bbaae1a1f3f5f6e2f36798848a6bc`,
`a8e54e8ffac5b2654ba23f3dbff8acee17dd857d05f3654fa0fa9d23fdd58c7c`,
and `e4c423a0d3bf2dea6ff69170787f67d6c481a07b246727625906293e5aea618e`.
The recovery C11 combined, D15-low and D16-high hashes are respectively
`b93428bb33cd7e31c2d9b2b84aa07ea17edda76c9d53ab73b3cb8687e8d53dfd`,
`a94e8fa2911fd3f7e715c6086d237b45fe630e71e8e14786bdcce435d99a8134`,
and `ac80ca047adeff842a911266ff1c054e30ac4628e925ea9fbb1be54e872b9581`.
The CP437-corrected C12 combined, D15-low and D16-high hashes are respectively
`b1a8152c0b4684d9d5608bd8bb60a06a21393c3bd7e7894cd8b7b61c494350d6`,
`b95eb5b0842d501ee602d82a7907b1cf4baf3e1b2cd74f73ef553eac60faf9de`,
and `3c6530816ed114f8a6d612c2b023a67a841b4e0c323754a9692d0d197664dd8a`.
The 2026-09-05 CS00000 visual check exposed the old 17-entry lookup against
the 26-entry glyph table. Only D16 changes. The corrected 80-column visual,
warm/default, RESET and power-cycle checks passed on CS00000. See
`docs/c12-runtime-console.md` for exact evidence scope and the retained
original-pair failure boundary.

D15 is always the low 8 KiB and D16 the high 8 KiB; concatenating them must
reproduce the 16 KiB image exactly.  The generated JSON is the machine-readable
authority for image hash, ABI, feature bits, vector map, code sizes, POST-stage
dictionary, and promotion status.

## Reset and boot path

Reset establishes PPI/PIC, memory overlay, stock-compatible D54/D55/D57
raster and refresh timing, serial and known video/sound state.  CPU, scratch
RAM data/address, complete-ROM integrity, PIT progress, and USART progress are
bounded and retain distinct status in low RAM.  On success the ROM installs
the call gate at `D620h`, framebuffer helper at `D700h`, and resident mutable
state at `D780h`; it then enters the versioned loader at 19,200/8N1. Corrupt or
truncated transfers resynchronize and retry. C4/C5 use the compatibility V15
path and download a checked extension. C6 instead copies its complete 361-byte
V16 receive/CRC/ZX0 engine from boot-only ROM offset `0600h` to `0300h`, then
enters a 49-byte core padded to the fixed 128-byte descriptor at `0F00h`.
Its JF16 wire artifact has a zero-byte executable extension and carries only
the bounded compressed system stream. The loaded system changes to
19,200/8O1 NetDisk v3 while normal execution stays in memory mode 1.

C4--C8 use S21 bit 0 to select immediate automatic boot versus the concealed
local `N` recovery wait. C9 reserves bit 0 and always boots from the network.
Bits 2:1 select 40x24, 53x24, 64x20, or MODX-compatible 80x24.
Bits 4:3 select English, Estonian, CP866 Russian, or English/user-remap.  ROM
samples the byte once at reset and CP/M consumes the same latched value.

The implemented C9 scope, including the physical/model console-output
investigation and bounded transport hardening, is collected in
[`docs/network-rom-c9-plan.md`](../../../docs/network-rom-c9-plan.md).
The proved physical-video defect and focused successor scope are collected in
[`docs/network-rom-c10-plan.md`](../../../docs/network-rom-c10-plan.md).
The C11 programming and focused visual acceptance procedure is in
`cpm-plus-juku/docs/c11-physical-acceptance-worksheet.md`.

## Resident ABI

The manifest is fixed at `FF00h` and vectors start at `FF20h`. ABI 1.2 offers:

- console init/status/input/output and `FF53h` bounded span output;
- 19,200-baud serial initialization plus bounded byte receive/transmit;
- NetDisk single request and `FF56h` ordered batches of 1..8 requests;
- translated keyboard events and `FF59h` raw matrix samples;
- S21 configuration, key remapping, built-in sound cue/silence, and safe
  diagnostics.

ABI 1.3 appends `FF5Ch` without moving an earlier vector. C selects bounded
host-console, capability, time, publication, bulk, or state operations. Its
27 mutable bytes occupy `D7E0h..D7FAh`; framing/recovery code stays in ROM.
The complete-ROM diagnostic selector checks the independently balanced
resident `D800h..FFFFh` span. POST failure tones use SSL, SLS, SLL, LSS and
LSL for C1 through C5, with short intra-series gaps and a long repeat pause.

ABI 1.4 retains that selector vector and the ABI 1.3 two-byte state prefix,
then appends negotiation flags and the failed operation. Its reason values
distinguish TX timeout, RX timeout, prefix budget, sequence, integrity, and
host status. The C9 implementation resides at `F800h`; the public low-RAM gate
and `D600h..D7FFh` reservation do not grow.

ABI 1.5 appends `FF5Fh` and feature bit `1000h`. Selector 0 queries the
reset-latched default, active video mode, active character bank, and override
flags; selector 1 sets a validated mode/bank pair; selector 2 restores S21.
Set/default synchronously hide the cursor, apply timing and font policy, clear
the complete physical raster, reset keyboard pending state, and return only
after the new configuration is active. Warm boot and ordinary console init
preserve an override; reset and `JCGINIT` restore the latched default.

Framebuffer writes cannot execute directly through the active ROM overlay.
The resident text policy calls the copied low-RAM helper, which briefly selects
all-RAM mode 3, commits pixels, and restores mode 1.  Mutable disk/cache/DMA,
keyboard, cursor, protocol, and stack state remains in RAM.  The CP/M Plus
binding preserves a measured `0100h..9BFFh` transient span: 39,680 bytes,
exactly 8,704 bytes above the frozen RAM-BIOS reference.

Multi-request NetDisk is ordered and fail-fast.  Writes remain synchronous
write-through and invalidate affected read-ahead before the first attempt.
The block-console operation is bounded and best effort when N4 is absent;
local display and keyboard stay authoritative.  Cryptographic boot
authentication and write-back caching remain explicit non-goals until their
8080 cost and failure semantics justify them.

## Acceptance boundary

Simulator qualification proves automatic boot, exact memory/ABI contracts,
local console/keyboard/cursor integration, N4 block output, A:/B: media,
sequential reads, synchronous writes, diagnostics, warm boot, absent/corrupt
host recovery, duplicate replies, modeled 8251 overrun recovery, stateless
server replacement, and long read/write/reconnect operation.

On 2026-08-18 the named halves were programmed, verified, and fitted in
CS00015. Repeated automatic boot, local keyboard, sound, A:/B:, sequential
reads, synchronous writes, diagnostics, warm boot, soak, and live host
replacement passed. The external display was unavailable, so exact physical
geometry, glyph, pseudographic, and cursor appearance remain unclaimed. C5 and
the stock ROM/RAM-BIOS route remain recovery and comparison baselines.
