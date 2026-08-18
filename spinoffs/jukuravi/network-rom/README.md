# Juku network-first ROM

Status: **ABI 1.2 C6 SIMULATOR RELEASE; BLIND PHYSICAL MATRIX PASSED**

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

## Build and test

From `8080-cosim`:

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py
sync/network_first_rom_abi_check.sh
sync/network_first_rom_hdl_check.sh
python3 tests/janet_disk_server_test.py
```

The ABI gate rebuilds the images, executes C4, C5, and C6 against the practical
C-model twin, and checks exact manifests, fixed vectors, stack guards,
interrupt ownership, overlay protection, all S21 geometries, locale pixels,
keyboard behavior, cursor phases, and resident serial activity.  The focused
HDL gate retains the exact C4 reset/POST, call-gate, framebuffer, keyboard,
serial, and one-record NetDisk boundary; full CP/M, recovery, and long-soak
coverage remains in the faster C-model oracle.

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

S21 bit 0 selects immediate automatic boot versus the concealed local `N`
recovery wait.  Bits 2:1 select 40x24, 53x24, 64x20, or MODX-compatible 80x24.
Bits 4:3 select English, Estonian, CP866 Russian, or English/user-remap.  ROM
samples the byte once at reset and CP/M consumes the same latched value.

## Resident ABI

The manifest is fixed at `FF00h` and vectors start at `FF20h`.  ABI 1.2 offers:

- console init/status/input/output and `FF53h` bounded span output;
- 19,200-baud serial initialization plus bounded byte receive/transmit;
- NetDisk single request and `FF56h` ordered batches of 1..8 requests;
- translated keyboard events and `FF59h` raw matrix samples;
- S21 configuration, key remapping, built-in sound cue/silence, and safe
  diagnostics.

Framebuffer writes cannot execute directly through the active ROM overlay.
The resident text policy calls the copied low-RAM helper, which briefly selects
all-RAM mode 3, commits pixels, and restores mode 1.  Mutable disk/cache/DMA,
keyboard, cursor, protocol, and stack state remains in RAM.  The CP/M Plus
binding preserves a measured `0100h..99FFh` transient span: 39,168 bytes,
exactly 8 KiB above the frozen RAM-BIOS reference.

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
