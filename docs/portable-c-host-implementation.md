# Portable C host implementation status

This is the implementation ledger for the
[portable C host plan](portable-c-host-plan.md). It records admitted code and
evidence; unfinished items remain governed by the plan rather than being
silently narrowed.

## M0 — complete

Commit `81f64f76` froze the final Python-era production modules, five stock
systems, exact wire vectors, and required runtime behavior. The full baseline
passed all archived-system, station-learning, Fastboot, NetDisk, N4, media,
and reconnect regressions before implementation began.

## M1 — complete

The first platform-neutral C99 slice is under `host/`:

- explicit Janet encoding and an incremental noise/checksum-resynchronizing
  parser;
- CRC-16/CCITT, CRC-16/IBM, Fletcher-16, and XOR primitives;
- checked Fastboot frames and strict V15/V16 bundle metadata/payload
  validation;
- plain, explicit, JUKUSYS, JUKU51, and CRC-checked `JUKURM1` image
  preparation, byte-exact relocation stubs, and indexed stock-bootstrap frame
  generation;
- incremental N3/N4 request framing with bounded target-controlled lengths;
- ordinary and CRC-protected reply builders;
- V3 raw, fill, deleted-directory, and prefix/fill record encodings;
- 80-track and native 160-track geometry, bounds checks, read-only enforcement,
  and cylinder/head-interleaved `.JUK` conversion.
- in-memory N3/N4 service semantics for raw/compact/read-ahead reads, legacy
  and V3 writes, duplicate replay, console queues, clock requests, target
  reports, and capability negotiation.
- the complete stock request/ACK/REJ/line-turn state machine, exact
  stock-assisted V15 handoff, and V16 readiness, overlap-safe stream probes,
  final acknowledgement, and explicitly unconfirmed no-resend paths;
- a transport-independent lifecycle model for cold boot, Fastboot, NetDisk,
  target reset, host loss/reopen, reconnect, clean stop, and fatal stop;
- a versioned little-endian raw capture stream with CRC-32, truncated-record
  detection, and exact RX/TX/event payloads;
- an explicit CRC-protected media journal and deterministic rollback/roll-
  forward recovery for crashes before apply, after apply, and after commit.

`sync/jukuhost_core_check.sh` compiles the same sources in strict C99 mode with
GCC using signed and unsigned `char`, with Clang when installed, and under
AddressSanitizer/UndefinedBehaviorSanitizer when supported. The C test reads
the same immutable `python-era-v1.txt` oracle as the Python contract test.

The core passes frozen Python-era vectors, byte-exact one-record bootstrap
comparison, successful and rejected state transitions, fragmented/noisy/bad-
checksum parser recovery, duplicate side-effect suppression, geometry and
read-only boundaries, capture truncation/corruption, and media crash-point
fault injection. All sources are free of POSIX and Win32 headers.

At the M1 gate no platform backend or production command had been introduced;
Python remained the production host until the M2 parity, caller-migration, and
retirement work below passed.

## M2 — complete

The POSIX serial/filesystem/clock/console layer and single Linux `jukuhost`
command now drive the existing simulator through stock and C8 boots, A:/B:,
N4, reset, missed-ready, host-loss, reconnect, writable-media, logging, and
capture tests. Those passed before callers were migrated and the Python
production entry points retired.

### Native Linux runtime checkpoint

The first POSIX executable is now available as `build/jukuhost`, built by
`sync/jukuhost_linux_build.sh`. It currently provides:

- strictly configured 9,600 8O1 and 19,200 8N1/8O1 serial phases with bounded
  partial reads/writes, drain support, monotonic deadlines, and clean signal
  handling;
- stock Janet, stock-assisted Fastboot V15, and direct C8 Fastboot V16
  execution through the admitted core;
- N3 A:/B: and N4 console/clock/report service, duplicate replay, and ready-
  marker recovery;
- writable A: persistence through the CRC journal and synchronous record
  writes;
- simultaneous human-readable console/file logging and exact binary capture;
- stable command/configuration, artifact, serial, protocol, and media exit
  classes.

`sync/jukuhost_linux_check.sh` proves the executable over real PTYs: N3 raw,
compact, V3 write and duplicate replay, native high-track B:, N4 capabilities,
bulk output and input, persisted media, journal cleanup, capture creation, and
Ctrl+C shutdown. Linux PTYs do not preserve physical parity-enable bits in
termios readback, so only `/dev/pts/*` relaxes that one readback assertion; a
physical tty retains strict 8O1 verification. The PTY backend also deliberately
does not request kernel parity generation: Linux may accept the first request,
silently clear it, and reject the same PTY when a replacement process adopts
it. This is confined to named `/dev/pts/*` devices and the integration-only
`--serial-fd` path; physical serial ports still require set-and-readback parity.

At this intermediate checkpoint, full Juku simulator boot/reconnect/fault
parity, configuration/manifest identity, caller migration, and Python-host
retirement were still open. The subsequent checkpoints below close each item.

### C8 end-to-end simulator checkpoint

`sync/jukuhost_c8_cosim_check.sh` now boots the admitted C8 network ROM and
current CP/M Plus image entirely through the native C executable. It proves
the one-shot JR16 readiness exchange, Fastboot V16, the transition to 19,200
baud NetDisk v3, the first CP/M prompt, bidirectional N4 console traffic, a
complete `DIR`, writable-media journal setup, clean signal shutdown, text log,
and binary capture.

The runtime preserves the Python-era NetDisk-v3 descriptor pacing: each
read-ahead record is transmitted as its own chunk after accounting for queued
8O1 wire time and the established four-millisecond decoder guard. Sending the
whole aggregate reply at once reproduced the historical one-byte-USART Disk
I/O loop; the chunked path reaches the prompt and completes the directory
workload deterministically.

The simulator harness passes its already-open PTY master as an inherited file
descriptor, avoiding a relay process that could alter timing. Its verbose
simulator trace is written to a file rather than an unread pipe; this prevents
test-infrastructure backpressure from blocking the simulated CPU during a
long N4 transcript.

The same gate now runs a second fault session which discards the ROM's
one-shot JR16 readiness frame before starting the host. The overlap-safe V16
probe recovers and reaches CP/M. After `DIR`, that session cleanly stops the
first host, starts a fresh `--resume-disk` process on the same PTY and media,
and proves resumed N4 traffic with `VER`. This pins missed-readiness and host-
replacement behavior, including repeated PTY adoption.

A third session resets the modeled board after byte 900 of the V16 stream.
The new ROM emits a fresh checked `JR16` readiness frame; the host distinguishes
that explicit reset from a merely lost final acknowledgement, flushes stale
bytes, and retransmits the complete bootstrap within the configured bounded
restart count. It then reaches CP/M, completes `DIR`, and records exactly one
target reset and one bootstrap restart. The no-resend safety rule remains
unchanged when no explicit reset marker is observed.

### Serial reconnect checkpoint

`tests/jukuhost_serial_reconnect_test.py` starts the production executable on
a named PTY symlink, completes a disk request, removes that serial endpoint,
atomically points the same configured name at a fresh PTY, and leaves the host
process running. The host detects EOF/HUP, performs bounded reopen attempts,
reapplies and verifies 19,200 8O1, emits `NRN3`, and serves the next request.
The final evidence records one reconnect and two accepted requests. Inherited
test descriptors intentionally cannot be reopened.

### Evidence and media-recovery checkpoint

The normal text log now records explicit artifact-validation, serial-open,
stock/Fastboot, NetDisk, reconnect, and stop/failure phases. Its final summary
includes requests, read operations, returned records, writes, parser/duplicate
retries, bootstrap restarts, target resets, and serial reconnects. Every log
message is also a typed INFO/WARN/ERROR event in the CRC-protected binary
capture alongside exact RX and TX bytes. Important transitions are flushed;
configured log or capture failure has a distinct nonzero exit instead of
silently discarding required evidence.

The Linux PTY gate independently parses every capture record and verifies its
CRC, directions, lifecycle events, media-write event, and clean final summary.
It then plants an on-disk `APPLIED` journal and a corresponding partially
changed A: record, starts a fresh production process, and proves deterministic
rollback plus sidecar removal before service begins. This complements the
portable core's prepared/applied/complete crash-point matrix with real POSIX
file operations.

`tools/jukuhost_evidence.py` is a post-session converter, not another host. It
validates the native capture header and every record CRC, extracts the compact
request events into the established JSONL acceptance schema, and can derive a
manifest-bound boot-result JSON record from the first disk request. This keeps
JSON useful to modern acceptance tooling without adding a JSON runtime or a
second protocol implementation to `jukuhost`.

High-frequency N4 polls are never printed individually. They are retained as
compact capture events, while `--verbose` text output remains limited to disk
requests. A regression demonstrated why this separation matters: an unread
stdout pipe can otherwise fill and block the host, changing target timing.
The resident V16 probe loop now also runs until the configured boot deadline,
so starting the host before an operator powers or resets the Juku does not
exhaust a short fixed probe count.

### Stock-assisted V15 compatibility checkpoint

A 2026-08-21 CS00000 session isolated a host defect rather than a target or
USART failure. Stock Janet loaded and executed the exact 128-byte JF15 core,
but the retired Python wrapper exhausted roughly four seconds of fixed probes
before the physical core answered. Reattaching directly at 19,200/8N1 without
RESET immediately received `C5`; the same resident core accepted the 267-byte
extension and 9,267-byte ZX0 stream, installed 16,384 bytes with CRC16/IBM
`1C42`, and entered working NetDisk v3 with no extension or stream retry.

Version `0.3.0-m6` admits that exact stock-assisted path in the sole production
C host. It validates JF15 structure and both compressed/system CRCs before
opening the serial device, sends only the core through learned-identity Janet,
then switches to 19,200/8N1 and probes the overlap-safe core until the normal
boot deadline. It does not reintroduce V1-V14 or a Python fallback.

The stock state machine also recognizes a resumed ready/poll turn while an ACK
is pending as an implicit reject. It resends the identical checked frame and
raises only that session's destination-zero turnaround guard from zero through
2, 5, and 10 ms. Thus boards needing more analog/firmware settling receive it
without charging every frame or slowing boards that acknowledge immediately.
Explicit REJ uses the same bounded adaptation.

PTY `tcdrain()` means only that a peer process consumed queued bytes, not that
the modeled UART wire finished. The POSIX PTY backend now accounts for 10-bit
8N1 and 11-bit 8O1 wire time before a drain completes. This exposed and fixed
an inconsistent accelerated C8 test whose target-time capability window could
expire while the host correctly modeled real 19,200-baud transmission.

`tests/jukuhost_v15_delayed_pty_test.py` holds the core response for five
seconds and proves the former fixed-window failure cannot recur.
`tests/jukuhost_stock_v15_cosim_test.py` boots stock Ekta4401 through the C
host, JF15, CP/M Plus, and NetDisk/N4 to `A>`. The existing C8 gate still passes
normal, missed-ready plus host-replacement, and mid-stream-reset variants at a
physical 1.7 MHz clock. On 2026-08-22, CS00000 with EK37 / RomBios 3.43m fitted
physically passed the new C path: identity `02 -> 01`, zero Janet rejects,
two core probes, one stream-header probe, zero extension/stream retries,
CP/M `A>`, and 22 clean NetDisk requests. The exact removed `#0031` pair still
belongs in the controlled ROM/socket comparison; the implementation itself is
no longer awaiting a physical confirmation.

### Stock-system simulator checkpoint

`sync/jukuhost_stock_cosim_check.sh` boots all five frozen stock-system images
through the native executable: `CPM22.BIN`, `CPM231E.BIN`, `EKDOS229.BIN`,
`EKDOS230.BIN`, and `EKDOSVSW.BIN`. It verifies the installed payload and
entry address, the selected system preparation mode, and the final USART
state. A sixth run sends an unconfigured station identity and proves automatic
identity learning. The integration-only `--boot-only` mode ends immediately
after a successful bootstrap so this test exercises the real production
bootstrap implementation without requiring a compatible NetDisk client.

### Configuration and identity checkpoint

The portable core now includes a bounded INI parser and SHA-256 implementation.
The parser applies defaults explicitly, accepts the primary system/Fastboot
pair and one inseparable fallback pair, validates A:/B: geometry and media
policy, and rejects unknown, duplicate, incomplete, oversized, or malformed
input. The same code passes GCC with both `char` signedness modes, Clang, and
ASan/UBSan.

The Linux application accepts `jukuhost CONFIG.INI`, resolves artifact paths
relative to that file, verifies declared sizes and SHA-256 values before
opening serial, and logs the applied identities. A failed primary identity
selects the fallback pair; it never mixes artifacts across slots. Writable
snapshot mode authenticates and preserves an immutable base, creates a
separate working image, and resumes only that working image on later runs.
Direct and read-only modes remain explicit. `tests/jukuhost_config_test.py`
proves rejection, fallback, snapshot creation/resume, base preservation, and
the no-serial `--selftest` command. The exact syntax and policies are recorded
in [jukuhost-config.md](jukuhost-config.md).

### Operational-wrapper migration checkpoint

`tools/juku_run.py` now launches only `build/jukuhost` for its interactive
Janet netboot and served-disk modes. It builds the native executable on demand,
passes explicit NetDisk baud/protocol/read-ahead policy, retains the C text log
and raw capture, and sends SIGINT for an orderly host shutdown. There is no
Python-host selection or fallback. `tests/juku_run_host_test.py` freezes both
the boot-only and A:/B: command forms.

A real wrapper-level simulator run used stock Ekta 3.7, scripted `TN0201`, and
`media/system/CPM22.BIN`. The native executable accepted the learned Janet
identity, completed all 53 bootstrap records, and exited cleanly with 2,421 RX
bytes, 11,095 TX bytes, and no protocol retry. This proves the wrapper's
auto-discovered serial PTY rather than only testing constructed arguments.

### Acceptance and demonstration caller checkpoint

The current `cpm-plus-juku` physical-acceptance runner now launches only the
native C host, snapshots that executable and the evidence converter, waits for
the explicit serial-open phase, and derives its JSON/JSONL report from the C
text log and raw capture. The obsolete C4/V15 qualification runner was removed;
current physical work is C8/V16. Its focused runner test passes independently
of the repository's separately tracked historical artifact pins.

`tools/netboot_demo_gifs.py` also invokes only `build/jukuhost`. Its stock-ROM
CP/M 2.2 and current C8/V16 CP/M Plus scenarios both pass from bootstrap through
their scripted console workloads and retain host log, raw capture, and simulator
log beside the framebuffer capture. The generator now owns the simulator PTY
and passes its master descriptor directly to the host, matching the admitted
C8 integration topology. The old stock-ROM V15 CP/M Plus GIF remains frozen
historical evidence and is not a runnable scenario.

During that migration, orderly SIGINT under continuous N4 traffic exposed a
real lifecycle race: an interrupted, back-pressured serial write was reported
as a serial failure. The runtime now recognizes the pending stop before
reconnect/error classification. The Linux PTY gate deliberately fills the
reply queue and interrupts an active write; it requires exit zero and a clean
stop event.

The related `vc8080` interactive launcher has likewise moved from embedded
Python serving to the current C8/V16 artifacts and `jukuhost`, preserving its
host log and raw capture. That local repository has no configured remote, so
its migration commit is retained locally pending publication of that project.

### Python-host retirement checkpoint

The three generic Python Janet, Fastboot, and NetDisk command files have been
removed from `tools/`. Their frozen implementations live under
`tests/fixtures/legacy_janet_*.py`, have no `__main__` entry point, and remain
only for byte-exact historical PTY regressions and the explicitly out-of-scope
BAUD diagnostic laboratories. Normal documentation and operational wrappers
cannot launch them. The current C host and frozen fixtures both pass the M0
contract, five-system stock-bootstrap, Fastboot, NetDisk/N4, direct-ROM, and
network-ROM regression gates.

Smoke-kit v2 now publishes a statically linked `bin/jukuhost` beside the C
simulator and labels the Python files as test fixtures. This lets downstream
CP/M integration tests preserve historical fault injection without packaging
a second runnable production host.

### M2 promotion and closure

`sync/jukuhost_m2_check.sh` is the repeatable promotion gate. It compares the
frozen Python-era behavior with the native C implementation, then exercises
the Linux executable through stock and C8 boots, A:/B:, N4, target reset,
missed readiness, host replacement, serial reopen, media recovery, evidence,
and the current ROM fault matrix. The gate passes.

All known operational callers now launch `jukuhost`. The only imports of the
frozen Python implementation are tests and four explicitly bounded UART
diagnostic laboratories. CP/M Plus CI consumes smoke-kit v2, which contains a
static C host and labels those Python files as non-runnable test fixtures.
There is no production Python command or fallback.

The complete comparison, related-repository commits, CI image digests, and
single-host audit are retained in
[portable-c-host-m2-acceptance.md](portable-c-host-m2-acceptance.md). M2 is
therefore accepted.

### Pre-M3 sequence

1. M2.1 is complete: the exact accepted Linux host passed the physical
   CS00015 matrix documented in
   [portable-c-host-m2.1-physical-acceptance.md](portable-c-host-m2.1-physical-acceptance.md).
2. M2.2 is desk-complete: the admitted core builds reproducibly as a 16-bit
   DOS executable and passes real-COM1-path stock and C8 simulator sessions.
   Its evidence is retained in
   [portable-c-host-m2.2-dos-acceptance.md](portable-c-host-m2.2-dos-acceptance.md).
3. M2.3 is next: validate that exact Pocket8086 executable against CS00015 and
   compare its full workload with the M2.1 Linux baseline.

Only after all three pass does M3 begin. The detailed entry/exit criteria are
in [portable-c-host-plan.md](portable-c-host-plan.md).

## M2.2 — Pocket8086 DOS port desk-complete

The production source is no longer POSIX-shaped. `jukuhost_main.c` and
`platform_file.c` are shared, while `platform_posix.c` and `platform_dos.c`
provide only their platform boundaries. Media reads, writes, native B: layout,
identity hashing, snapshots, and journal recovery are streamed through a
file-backed backend; neither 400 KiB A: nor 800 KiB B: is copied into 16-bit
memory.

The DOS layer directly owns COM1 or COM2, preserves and restores the previous
UART registers, programs 9,600/19,200 baud and 8O1/8N1, detects a FIFO, drains
TX, counts line-status errors, and clears stale RX on every framing change.
The combined BIOS tick/PIT channel-0 clock gives one-millisecond deadlines.
The local N4 console uses DOS `CON`; F10 requests a clean stop only while the
host is polling the idle console path, so an active transfer is not aborted.

`sync/jukuhost_dos_build.sh` uses the exact Open Watcom V2 asset vendored in
this repository and treats warnings as errors. `tools/package-jukuhost-dos.py`
authenticates the adjacent CP/M Plus C8 manifest and emits one 8.3-safe folder
with the EXE, no-options INI/BAT entry point, system/Fastboot artifacts, A:/B:
images, and a package SHA-256 list. There is no Kolobok dependency.

`sync/jukuhost_dos_check.sh` rebuilds twice and compares the executables, runs
the actual 16-bit program under headless DOSBox-X, then places its emulated
COM1 on a paced bridge to the Juku simulator. The gate covers stock 9,600/8O1
Janet and current C8 19,200/8N1 Fastboot followed by 19,200/8O1 NetDisk v3 and
N4. The exact artifact identity, measurements, test boundary, and next physical
gate are in
[portable-c-host-m2.2-dos-acceptance.md](portable-c-host-m2.2-dos-acceptance.md).
