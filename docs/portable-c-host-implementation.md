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
- checked Fastboot frames and strict V16 bundle metadata/payload validation;
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
- the complete stock request/ACK/REJ/line-turn state machine and the V16
  readiness, overlap-safe stream probe, final acknowledgement, and explicitly
  unconfirmed no-resend path;
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

No platform backend or production command has been introduced at the M1 gate.
Python remains the production host until M2 parity, caller migration, and
retirement all pass.

## M2 — in progress

Implement the POSIX serial/filesystem/clock/console layer and the single Linux
`jukuhost` command, then drive the existing simulator through stock and C8
boots, A:/B:, N4, reset, missed-ready, host-loss, reconnect, writable-media,
logging, and capture tests. Only after those pass are callers migrated and the
Python production entry points retired.

### Native Linux runtime checkpoint

The first POSIX executable is now available as `build/jukuhost`, built by
`sync/jukuhost_linux_build.sh`. It currently provides:

- strictly configured 9,600 8O1 and 19,200 8N1/8O1 serial phases with bounded
  partial reads/writes, drain support, monotonic deadlines, and clean signal
  handling;
- stock Janet and direct C8 Fastboot V16 execution through the admitted core;
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
physical tty retains strict 8O1 verification.

This is an intermediate M2 checkpoint, not promotion. Full Juku simulator
boot/reconnect/fault parity, configuration/manifest identity, caller migration,
and Python-host retirement remain open.

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
