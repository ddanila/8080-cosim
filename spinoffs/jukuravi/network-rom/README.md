# Juku network-first ROM

Status: **C12 / ABI 1.5 SIMULATOR-QUALIFIED; FOCUSED CS00000 PHYSICAL
CHECKS PASSED; BROADER RELEASE QUALIFICATION SEPARATE**

This is the from-scratch network-only successor to the EktaSoft monitor ROM.
Reset performs a bounded POST, discovers a host, receives a checked CP/M Plus
3.1 image, and hands the machine to NetDisk v3 without a keypress. The upper
10 KiB provides the versioned resident platform layer.

The sibling `cpm-plus-juku/docs/network-first-rom-plan.md` owns the design and
acceptance requirements. Boot uses 19,200/8N1 and NetDisk uses 19,200/8O1;
this is separate from the stock-ROM JF17 recovery profile at 9,600/8O1.
Matching system, ROM and host profiles are required.

## Release and physical scope

| Release | ABI | Purpose and qualification boundary |
| --- | --- | --- |
| C4 | 1.0 | Immutable automatic-boot reference; ROM halves are byte-identical to C3 |
| C5 | 1.1 | S21 policy, four geometries, locale banks and persistent remaps; CS00015 blind functional matrix passed, exact display/cursor observation not qualified |
| C6 | 1.2 | Console spans, ordered NetDisk batches, raw keyboard and sound; fitted CS00015 pair passed monitor-independent checks; modified raw-key scan has a known limitation |
| C7 | 1.2 | Corrects modified raw-key scanning and CP437 boxes under separate names; simulator qualification does not establish focused physical acceptance |
| C8 | 1.3 | Resident N4 transport, diagnostics and POST tones; fitted and blind-qualified in CS00015; retained physical rollback |
| C9 | 1.4 | Bounded transport and negotiation telemetry; CS00000 remote/disk/recovery paths passed, but POF suppressed local video; immutable and not promoted |
| C10 | 1.4 | Corrects the POF release; desk-qualified programming candidate, broader physical acceptance separate |
| C11 | 1.4 | Deterministic checkerboard, full-raster clear and checked loader discovery/recovery; focused acceptance procedure belongs to the sibling project |
| C12 | 1.5 | Runtime mode/bank selection and distinct discovery identity; corrected CP437, warm/default, reset and power-cycle checks passed on CS00000; broader qualification separate |

The corrected C12 physical record in
[the runtime-console contract](../../../docs/c12-runtime-console.md) binds the
exact tested pair and distinguishes earlier failed-pair evidence. It does not
qualify continuously running-host reset recovery, Windows serial hardware or
a new endurance run. The
[C11 recovery contract](../../../docs/c11-session-recovery.md),
[C9 boundary](../../../docs/network-rom-c9-plan.md) and
[C10 video correction](../../../docs/network-rom-c10-plan.md) retain the relevant
protocol and defect evidence.

C6's fitted raw scanner can report a global modifier before reaching an
ordinary key's column; translated input and unmodified raw keys are unaffected.
C7 scans ordinary columns first. Named releases are immutable: rebuilding a
corrected scanner under C6 filenames would invalidate its physical identity.

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
  resident-host release; physical rollback scope described above.
- `juku-network-rom-abi1.4-c9{,-d15,-d16}.bin` and JSON: C9 / ABI 1.4
  bounded-host simulator/HDL candidate.
- `juku-network-rom-abi1.4-c10{,-d15,-d16}.bin` and JSON: C10 / ABI 1.4
  POF-release candidate ready for physical programming.
- `juku-network-rom-abi1.4-c11{,-d15,-d16}.bin` and JSON: C11 / ABI 1.4
  deterministic POST/checker and complete-raster-clear candidate.
- `juku-network-rom-abi1.5-c12{,-d15,-d16}.bin` and JSON: C12 / ABI 1.5
  runtime-console and versioned-recovery simulator candidate.

The per-release JSON manifests beside the binaries own the combined and
half-image SHA-256 hashes. Physical acceptance records bind the exact installed
pair; a later rebuilt release is not implicitly qualified by earlier evidence.

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
state at `D780h`; it then enters the versioned loader at 19,200/8N1. Complete transfers with failed
integrity checks return to the loader scan. An incomplete accepted V16 body
waits for the remaining bytes; its receive path has no timeout, so host
discovery alone cannot restart it. See [the recovery limits](../../../docs/c11-session-recovery.md).
C4/C5 use the compatibility V15
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

The 2026-08-18 C6 halves were programmed, verified, and fitted in
CS00015. Repeated automatic boot, local keyboard, sound, A:/B:, sequential
reads, synchronous writes, diagnostics, warm boot, soak, and live host
replacement passed. The external display was unavailable, so exact physical
geometry, glyph, pseudographic, and cursor appearance of that pair remain
unclaimed. C5 and
the stock ROM/RAM-BIOS route remain recovery and comparison baselines.
