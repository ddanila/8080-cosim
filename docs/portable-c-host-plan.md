# Portable C Juku host plan

Status: **M1 PORTABLE CORE COMPLETE; NATIVE LINUX HOST NEXT**

## Goal

Produce one small, dependable Juku network host whose production runtime does
not require Python. The same source must build as:

- a native Linux command-line program;
- a native macOS command-line program; and
- a 32-bit Windows 95 command-line program built with Open Watcom V2.

The first Windows 95 deployment is a physical x86 machine with a physical COM
port. USB-to-serial drivers and adapters are not part of the Windows 95 support
contract.

This is an incremental replacement of the production CP/M network-serving
path, not a rewrite of every Python tool in this repository. The migration is
complete only when the C host has full production parity and becomes the sole
supported runtime host. The Python host is then retired rather than retained
as an alternative or fallback. Python remains appropriate for artifact
building, simulation, test generation, diagnostic analysis, evidence
conversion, and other non-host desk tooling.

## Decisions already made

1. Use portable C for the production host. The application is primarily byte
   protocols, bounded state machines, serial I/O, timers, and disk-image I/O;
   C provides a small dependency-free Windows 95 executable without imposing a
   C++ runtime contract.
2. Use Open Watcom V2 for the Win32/Windows 95 build. Pin the compiler release
   and archive hashes by reusing the reproducible bootstrap pattern already
   proven in `ddanila/kolobok`.
3. Use GCC or Clang for Linux and Clang for macOS. Open Watcom is the Windows
   95 compiler, not a requirement for every host platform.
4. Develop and qualify the C protocol core on Linux first. Win32/Wine work
   begins only after the same core passes native simulator sessions.
5. Use headless Wine as the first Win32 execution environment. A temporary
   Wine prefix maps `COM1` to the Juku simulator PTY; actual Windows 95 and its
   physical UART are the final platform test.
6. Keep ordinary human-readable logging and an optional raw traffic capture.
   The Windows 95 executable does not need a JSON parser or JSON logger.
   Modern Python tooling may convert retained logs and captures to JSON/JSONL.
7. Preserve exact existing wire contracts and recovery behavior before
   considering any new protocol or performance change.
8. Define the MVP as full behavioral parity with the current production Python
   host on Linux, migration of every production caller to the C executable,
   and retirement of the runnable Python host. Windows and macOS use the same
   admitted C core; they do not introduce another host implementation.

## MVP and final migration boundary

The MVP is not a partial protocol demonstration. It must cover every feature
needed for the accepted CP/M workflow: stock and C8 boot discovery, Fastboot
V16, N3 A:/B:, N4, learned identity, manifests, writable-media policy,
reconnect, logging, capture, and clean shutdown. It must pass the existing
simulator, physical-acceptance harness, and retained-failure regressions on
Linux.

At that gate:

- the C executable becomes the default and only supported operational host;
- CP/M Plus acceptance runners and every repository command invoke it;
- user documentation no longer offers Python serving commands;
- runnable Python Janet/Fastboot/NetDisk/N4 server entry points are removed or
  reduced to explicitly test-only conversion/fixture code that cannot act as a
  second production host;
- accepted golden vectors, captures, and protocol specifications replace the
  live Python server as the long-term behavioral oracle;
- no automatic fallback to Python is retained.

The Win32/Wine, macOS, and physical Windows 95 milestones qualify additional
builds of that same C host. They do not postpone the architectural decision or
create platform-specific forks. No Win32 or macOS implementation work begins
before the Linux parity-and-retirement gate closes. During any gap before a
later platform build is ready, that platform is explicitly pending; the
Python host is not kept alive as a temporary platform fallback.

## Initial scope

The first complete C host covers the production network path used by current
Juku ROM and CP/M Plus builds:

- stock Janet bootstrap at 9,600 baud;
- automatic C8/JR16 readiness handling;
- Fastboot V16 at 19,200 baud;
- NetDisk v3 at 19,200 baud;
- writable A: and read-only B: media;
- N4 remote console input and output;
- station identity learned from any valid boot request;
- host loss, target reset, bounded retry, and live reconnect;
- boot-manifest/configuration verification;
- human-readable logging, summary counters, and optional byte capture;
- clean Ctrl+C/window-close handling and meaningful process exit codes.

The initial host does not need to replace:

- ROM, CP/M, disk-image, or Fastboot artifact builders;
- simulator orchestration unrelated to host acceptance;
- BAUDTEST/BAUDTEST2, arbitrary-rate experiments, UART-counter laboratories,
  or board-specific diagnostic probes;
- the complete Jukuravi upload/probe laboratory;
- physical-acceptance report generation and historical JSON evidence;
- graphical user interfaces, services, registry configuration, installers, or
  plug-ins.

Those non-host Python tools continue to do useful desk work and can consume
captures produced by the C host. Additional utilities may move to C later only
when there is a concrete need to run them on a legacy host. No retained Python
tool may quietly remain an alternative production network server after MVP.

## Compatibility contract

### Windows 95

- 32-bit x86 console executable, intended to run on a 386 or newer CPU;
- ANSI Win32 APIs only;
- physical `COM1` through `COM4` as the required baseline;
- ordinary RS-232-level connection and the correct Juku cable;
- no CP2102, USB stack, vendor virtual-COM driver, or network dependency;
- standard 9,600 and 19,200 rates required; experimental rates are out of
  scope;
- no hardware or software flow control;
- one executable, one INI/configuration file, system/Fastboot artifacts, and
  disk images are sufficient to run;
- no Python installation and no separately installed runtime libraries.

Later Windows versions and USB adapters are expected to work when their driver
exposes a conventional Win32 COM port, but they are optional compatibility and
must not weaken the physical-COM baseline.

### Linux and macOS

- retain explicit device selection and current serial framing;
- preserve Linux exact-baud and UART-counter features only as optional
  capabilities, not portable requirements;
- retain native POSIX PTY support where useful;
- offer the same configuration, logs, captures, defaults, and exit meanings as
  the Windows build.

## Architecture

The protocol core must not include Win32, POSIX, terminal, or concrete
filesystem headers:

```text
                   Python host during migration only
                    golden vectors / differential runs
                                  |
                         portable C protocol core
                    Janet / Fastboot / N3 / N4 / media
                         /          |          \
                 Linux POSIX    macOS POSIX    Win32/Win95
                 GCC/Clang         Clang       Open Watcom V2
                         \          |          /
                          logs + binary captures
                                  |
             frozen captures/specifications + Python evidence tools
```

Suggested module boundaries are:

| Layer | Responsibilities |
| --- | --- |
| `core/frame` | byte-exact Janet framing, incremental parser, XOR and CRC primitives |
| `core/bootstrap` | stock bootstrap discovery, learned station identities, retries and execute handoff |
| `core/fastboot` | JR16 readiness, V16 metadata validation, stream transfer and acknowledgements |
| `core/netdisk` | N3 request parsing, read-ahead semantics, A:/B: dispatch and error replies |
| `core/n4` | remote-console queues, bounded bulk output and reconnect state |
| `core/session` | cold boot, disk service, target reset, host stop and recovery state machine |
| `core/media` | geometry, bounds checks, read-only policy, working copy and journal contract |
| `core/log` | platform-neutral events, counters and capture records |
| `platform/*` | serial port, monotonic clock, sleep/wait, console, files, process signals |
| `app` | INI/arguments, artifact verification, lifecycle and final result |

All multibyte wire values are encoded and decoded field by field. C structure
layout, compiler packing, host endian order, and signed `char` must never enter
the wire or disk format implicitly.

## C and compiler policy

Use a deliberately small, verified C99 subset and compile it in the strictest
mode supported by each toolchain:

- fixed-width integer compatibility definitions with compile-time size checks;
- no variable-length arrays;
- no locale-sensitive protocol behavior;
- no structure serialization or unbounded string operations;
- no assumptions about signedness, alignment, or arithmetic overflow;
- no operating-system calls outside platform modules;
- explicit lengths and bounds checks for all target-controlled input;
- warnings treated as errors in every compiler lane.

Open Watcom supports an explicit C99 language mode, but each C library call
used by the Windows binary must still be verified against its Windows 95
runtime. Small local helpers are preferable to pulling in a compatibility
library.

CI must inspect the generated PE import table. The Windows artifact fails the
build if it imports an API outside a reviewed Windows 95 allowlist. It must
also record executable size and SHA-256, and prove that a clean rebuild with
the pinned compiler is byte-identical or document the exact deterministic
boundary if the toolchain embeds unavoidable metadata.

## Serial and timing contract

Serial correctness is a first-class interface rather than scattered platform
calls. Every backend must provide:

- open with exclusive ownership;
- apply and read back baud, data bits, parity, stop bits, and flow-control
  state;
- flush stale input/output at defined session transitions;
- bounded partial read and partial write handling;
- a bounded wait for the driver transmit queue to drain;
- framing, parity and overrun status when the platform exposes it;
- cable/device disappearance reporting and bounded reopen attempts;
- a monotonic deadline clock with wrap-safe comparisons;
- sleep/wait primitives whose measured resolution is logged.

The Win32 backend must initialize every relevant DCB field rather than inherit
the last program's COM settings. It must acknowledge `ClearCommError` states
and report both requested and applied configuration at startup.

Windows 95's basic millisecond clock is coarse and wraps. The initial Win32
spike therefore measures clock resolution, transmit drain, read timeout, and
short guard behavior before the protocol port begins. Use a verified
high-resolution clock when present, retain a wrap-safe fallback, and prefer
target acknowledgements or driver queue state to blind sleeps. Wine timing is
diagnostic but is not accepted as proof of physical Windows 95 timing.

## Configuration and artifact identity

The runtime configuration should be a small ASCII INI-like file rather than
JSON. It is generated from the canonical modern build manifest and contains,
at minimum:

```ini
[host]
port=COM1
log=JUKUHOST.LOG
capture=JUKUHOST.CAP

[system]
file=SYSTEM.BIN
size=17920
sha256=...

[fastboot]
file=FAST16.BIN
size=...
sha256=...

[disk_a]
file=DISKA.IMG
writable=yes
geometry=juku-cpm3
sha256=...

[disk_b]
file=DISKB.JUK
writable=no
geometry=juku-native
sha256=...
```

The example is a direction, not a frozen syntax. The final parser remains
line-oriented, bounded, case-insensitive where appropriate, and rejects
unknown required fields, duplicate keys, malformed numbers, oversized lines,
wrong artifact sizes, and wrong hashes. The C host includes a small SHA-256
implementation so that moving away from JSON does not mean losing manifest
safety.

Command-line overrides are allowed for routine choices such as port and log
path, but the normal Windows 95 launch should work from a short `JUKU.BAT`
without typing a long command. Use ASCII and short distribution filenames so
that code-page, quoting, long-path, and case behavior cannot become protocol
problems.

## Logging and capture

Logging is required. It has repeatedly separated cable, host, target, timing,
and harness failures and must not be traded away for executable simplicity.

`JUKUHOST.LOG` is line-oriented text suitable for both a Windows 95 user and
simple modern parsers:

```text
00000000 INFO  start version=0.1 port=COM1
00000142 INFO  bootstrap request client=01 server=02
00005891 INFO  fastboot complete bytes=7670 retries=0
00007622 INFO  disk session protocol=N3 baud=19200
00018450 WARN  request retry op=11 seq=24 attempt=2
00019371 INFO  reconnect count=1
00042510 INFO  stop reads=74 records=592 writes=0 retries=1
```

Logging levels are:

- normal: identity, applied settings, phase changes, retries, failures,
  reconnects, media writes, and final counters;
- verbose: individual frames/requests and phase timing;
- trace: byte-range summaries in the text log, with full bytes in the capture.

`JUKUHOST.CAP` is an optional compact binary stream with a versioned header and
records containing monotonic time, direction/event type, length, and bytes.
The format has explicit little-endian fields and CRC protection. It records
host identity and applied serial settings once, then exact TX/RX traffic and
important local events. It must be streamable and useful even if the final
record is truncated by a crash.

Routine output may be buffered or placed in a fixed-size memory queue so a
slow FAT disk cannot alter serial timing. Startup settings, failures,
reconnects, media journal transitions, and the final summary are flushed at
defined points. Logging failure is reported prominently; the policy for
continuing or stopping depends on whether media safety or required evidence
would be lost.

Python tools convert the text/capture pair to JSON/JSONL acceptance evidence,
generate summaries, and replay traffic. JSON remains useful in the modern
analysis environment without becoming a Windows 95 runtime dependency.

## Writable-media safety

B: is always read-only in the initial release. A: is read-only unless the
configuration explicitly enables writes.

The host must never depend on POSIX rename-overwrite semantics or assume that
Windows 95/FAT makes a whole-image replacement atomic. The writable policy is:

1. validate the base/working image and geometry before opening the serial
   port;
2. preserve the base image in copy/snapshot modes;
3. record each persistent mutation in a compact sidecar journal with drive,
   offset/record, old or new data as required by the chosen recovery scheme,
   sequence, and CRC;
4. flush the journal before applying the image write;
5. flush the image before marking the journal transaction complete;
6. detect and deterministically recover or reject an incomplete transaction
   on the next start;
7. expose an explicit clean-shutdown result in the log.

The simplest safe first implementation may keep the session image in memory
and persist only a separate working copy, but a forced host reset must at worst
lose uncommitted changes; it must not silently corrupt the only base image.
Media behavior and recovery fixtures must be identical in C and the accepted
Python-era baseline before writable mode is promoted. After migration, those
fixtures and captures remain the oracle; the Python host does not.

## User interface and lifecycle

The first release is a single foreground console program. It does not use a
GUI, tray icon, service manager, registry, or installer. Required commands are
kept small:

```text
JUKUHOST                 run the configured boot/disk/console service
JUKUHOST CONFIG.INI      run an explicit configuration
JUKUHOST --selftest      run portable and Win32 platform self-tests
JUKUHOST --version       print build and protocol identity
JUKUHOST --help          print the bounded command summary
```

Exact syntax is frozen only after the Linux implementation makes the normal
workflow clear. Linux and macOS may additionally accept conventional long
options, but the Windows 95 BAT-file path remains first-class.

The lifecycle state machine explicitly defines:

- idle discovery and learned station identity;
- bootstrap and Fastboot handoff;
- active NetDisk/N4 service;
- target reset returning to discovery;
- host-side serial loss and reopen;
- live N4/NetDisk reconnect;
- Ctrl+C and console-window close;
- clean versus recoverable versus fatal shutdown;
- stable process exit codes.

Keyboard input is consumed only while the protocol is idle, matching the
existing rule that transfers and tool execution are not interrupted.

## Test strategy

Every hardware-discovered software or timing failure becomes a deterministic
desk regression where the model can express it. The test ladder deliberately
introduces one new uncertainty at a time.

### 1. Linux portable-core tests

- CRC/XOR and frame golden vectors;
- fragmented, concatenated, malformed, truncated, and noise-prefixed input;
- byte order, signed-char, bounds, counter wrap, and timeout boundaries;
- bootstrap, V16, N3, N4 and reconnect state transitions;
- disk geometry and media-recovery fault injection;
- log and capture truncation/replay;
- fuzz/property tests for parsers and target-controlled lengths;
- differential results against the current Python modules while they still
  exist, followed by pinned standalone vectors that no longer require them.

### 2. Native Linux integration

Implement the POSIX backend and pass the complete simulator workloads using
the same system, Fastboot, A:, and B: artifacts as the accepted Python-era
baseline. Compare:

- every transmitted/replied byte where ordering is deterministic;
- boot and disk request counts;
- retries and failure classifications;
- disk-image mutations;
- N4 input/output and paging;
- reset, missed-ready, host loss, reconnect, and clean shutdown;
- retained logs and captures replayed by both implementations.

Linux is the main development loop. No Win32 issue is debugged until the
corresponding core behavior passes here.

### 3. Linux promotion and Python-host retirement

Retirement is an implementation milestone with an explicit repository-wide
closure, not a documentation label:

1. Inventory every import, subprocess launch, shell command, Make target, CI
   job, document, and related-repository caller of `janet_netboot.py`,
   `janet_fastboot.py`, and `janet_disk_server.py`.
2. Move reusable artifact parsing or test-vector generation out of runnable
   server entry points where Python remains the right build/test tool.
3. Change `cpm-plus-juku` physical acceptance and simulator orchestration to
   launch the C host and consume its stable logs/captures.
4. Replace all normal Linux user commands with the C executable and the shared
   configuration format. Mark macOS and Win32 as pending until their later C
   ports land; do not preserve Python commands for either platform.
5. Preserve a compact, immutable set of Python-era success and failure
   captures plus byte-exact expected outputs.
6. Run the complete regression once with the last Python host and once with
   the C candidate; retain the comparison report.
7. Remove the runnable Python production host, its fallback selection, and
   obsolete operational documentation in the same promotion change.
8. Prove a clean checkout contains only one supported program capable of
   serving the production Janet/Fastboot/NetDisk/N4 workflow.

No work on another platform begins until this gate passes.

### 4. Open Watcom build and Wine self-test

- bootstrap a pinned Open Watcom toolchain;
- build the Windows 95 console artifact on Linux CI;
- audit PE target, imports, size, and hash;
- run `JUKUHOST.EXE --selftest` in a temporary 32-bit Wine prefix;
- run configuration, file, hash, log, capture, timer, and media tests under
  the Win32 API without requiring serial I/O.

### 5. Headless Wine serial integration

The repository owns a small shell harness rather than adopting a large Wine
testing framework. It:

1. creates a temporary isolated `WINEPREFIX`;
2. starts the existing Juku simulator and obtains its PTY path;
3. maps `$WINEPREFIX/dosdevices/com1` to that PTY;
4. runs the Open Watcom executable through Wine;
5. performs the same bootstrap, Fastboot, disk, N4 and reconnect workloads;
6. validates exit code, log, capture, request counts and final media;
7. stops `wineserver` and removes the prefix.

Run a line-oriented console executable directly when possible. CI may wrap
the whole harness in `xvfb-run -a` so Wine prefix initialization or incidental
USER32 behavior cannot fail merely because the runner has no display. Xvfb is
infrastructure, not part of the Juku host.

Wine maps a Win32 COM name through a prefix `dosdevices/com1` symlink, so the
Win32 serial backend can exercise the same Linux PTY used by current tests.
Wine proves Win32 call behavior and catches many porting errors, but it does
not prove Windows 95 scheduling, UART-driver timing, or physical electrical
behavior.

### 6. macOS build

Compile the already-qualified core with Clang, retain the POSIX backend's
Darwin differences, and pass unit plus PTY simulator tests. Retained physical
evidence from the Python era informs the platform port, but the retired Python
host is not an available fallback or release path.

### 7. Physical Windows 95 qualification

Use the exact hash-pinned EXE that passed Wine. The first spike and final
qualification use the physical Windows 95 machine's physical COM port.

The spike proves, before the full physical protocol qualification:

- Open Watcom executable starts on the target OS;
- COM port opens exclusively and applied settings read back correctly;
- loopback TX/RX and partial-write handling;
- monotonic timer resolution and wrap-safe deadline tests;
- output-drain and short-guard measurements;
- simultaneous console/file logging and orderly Ctrl+C/window close.

The final qualification then runs stock bootstrap, V16, N3 A:/B:, N4,
reconnect, clean writable-media shutdown, and retained capture replay. This is
the only stage that claims real Windows 95 UART behavior.

## Milestones and exit gates

### M0 — frozen behavioral contract

- catalogue Python entry points, importers, related-repository callers, and
  production defaults;
- retain golden frames and representative successful/failing captures;
- specify C result codes, events, capture records and configuration identity;
- prove the migration harness can replay every admitted fixture and emit
  standalone expected results that survive Python-host removal.

Exit: byte and state expectations are explicit enough that C is not judged by
visual similarity.

### M1 — portable core on Linux

- core modules compile with GCC and Clang;
- unit, malformed-input, timeout, media and differential tests pass;
- no platform headers escape platform modules.

Exit: every production protocol decision can run through an in-memory C
transport and agrees with the accepted Python-era baseline.

### M2 — native Linux host parity

- complete cold boot to CP/M prompt;
- A:/B:, N4, warm boot, host replacement and reconnect pass;
- logging, capture and writable-media recovery pass;
- current simulator timing/fault regressions pass.

Exit: full production parity is demonstrated; every operational caller uses C;
the runnable Python host and fallback are retired; C is the sole supported
host. Frozen fixtures, specifications, and captures become the long-term
oracle.

### M3 — Windows 95 artifact and headless self-test

- pinned Open Watcom build is reproducible;
- PE/import compatibility audit passes;
- headless Wine self-tests pass in a clean prefix.

Exit: the binary is structurally suitable for Windows 95 and its non-serial
Win32 paths work.

### M4 — Wine COM1 end-to-end parity

- Wine `COM1` mapped to simulator PTY;
- full boot/disk/N4/reconnect suite passes;
- captured Win32 traffic agrees with the frozen native contract;
- no X display or persistent Wine prefix is required.

Exit: all automatable Win32 behavior is proven before physical testing.

### M5 — macOS parity

- Clang build and native simulator suite pass;
- platform capability report accurately distinguishes Darwin from Linux.

Exit: Linux, macOS and Win32 artifacts share one admitted core.

### M6 — physical Windows 95 release candidate

- exact Wine-qualified EXE passes the physical COM spike;
- complete Juku network workflow passes on the real machine;
- timing, settings, counters, log and capture are retained;
- capture replays successfully in the simulator;
- rollback instructions and known limitations are documented.

Exit: Windows 95 moves from build-compatible to physically qualified.

## Risk controls

| Risk | Control |
| --- | --- |
| rewrite silently changes wire behavior | byte-exact Python/C differential tests during migration, then frozen capture/vector replay before hardware |
| Wine masks or invents serial behavior | native Linux first; Wine treated as Win32 desk gate; physical Windows 95 remains final authority |
| coarse Windows 95 timers break tuned guards | early physical timer/drain spike, acknowledgement-first design, logged applied timing capability |
| slow logging perturbs the serial loop | bounded buffering, compact capture, defined flush points and timing regression |
| host crash damages A: | read-only default, working copies, CRC journal and startup recovery tests |
| modern API enters the Win95 binary | PE import allowlist plus real Win95 start test |
| compiler differences corrupt frames | explicit serialization, fixed sizes, strict warnings and three-compiler tests |
| scope expands into every Python utility | retire only the runnable host; preserve useful non-host build, simulation, diagnostic, and evidence tools |
| old platform becomes hard to operate | one foreground EXE, short INI/BAT names, startup parameter dump and actionable errors |

## Final acceptance principles

- Desk tests are cheap and repeatable; exhaust them before requesting bench
  work.
- Every relevant hardware-discovered failure becomes a regression fixture.
- Hardware is reserved for electrical behavior, physical UART/driver timing,
  real Windows 95 API behavior, keyboard mechanics, display, and sound.
- The Python production host is removed after full parity rather than kept as
  a fallback. Python remains wherever it is the more useful non-host build,
  simulation, analysis, or research tool.
- The C host is promoted by captured equivalence and recovery evidence, not by
  reaching a prompt once.
- No optimization or new wire protocol is mixed into the compatibility port.
  Performance work starts only after the C host reproduces the accepted
  Python-era baseline.

## References

- [Open Watcom V2 supported targets and cross-development](https://open-watcom.github.io/open-watcom-v2-wikidocs/c_readme.html)
- [Open Watcom linker target definitions](https://open-watcom.github.io/open-watcom-v2-wikidocs/lguide.html)
- [Open Watcom C language modes](https://open-watcom.github.io/open-watcom-v2-wikidocs/cguide.html)
- [Microsoft communications functions](https://learn.microsoft.com/en-us/windows/win32/devio/communications-functions)
- [Microsoft communications-resource configuration](https://learn.microsoft.com/en-us/windows/win32/devio/modification-of-communications-resource-settings)
- [Microsoft `GetTickCount` behavior](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount)
- [Wine COM-device prefix mapping](https://manpages.debian.org/unstable/wine/wine.1.en.html)
- [Wine console execution modes](https://www.winehq.org/pipermail/wine-patches/2003-March/005564.html)
- [86Box serial port and named-pipe support](https://86box.readthedocs.io/en/latest/settings/ports.html)
