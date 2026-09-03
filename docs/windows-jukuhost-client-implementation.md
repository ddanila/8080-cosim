# Windows Juku host client implementation status

This is the implementation and qualification ledger for
[windows-jukuhost-client-plan.md](windows-jukuhost-client-plan.md). A gate is
complete only when its implementation and named checks are present in the
repository. Physical results are never inferred from Wine, a simulator, or a
Linux USB adapter.

## W0 — product contract frozen

Status: **complete**

The first release is one 32-bit ANSI Win32 GUI executable named
`JUKUWIN.EXE`. It uses the existing C protocol/media core through a shared
runner, embeds all boot payloads, and leaves only its simple INI and disk
images as input files. The UI, configuration schema, deployment shape,
durability rules, non-goals, and test gates are frozen in the plan.

The embedded catalog is pinned by
[`host/windows/payload-manifest.json`](../host/windows/payload-manifest.json)
to `cpm-plus-juku` revision `1efbcd1` and these exact artifacts:

| Mode | Role | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| stock | system | 16,896 | `254f940e36501dcf3f46c5ba23b2b6cb3b1b7f3a13b1e42ae9786f2fa337a4a4` |
| stock | JF15 | 9,670 | `881befd8ebd306ae7313b2dff8b83cb8d964988e17627d76efedaa49e6a19a5d` |
| C11 | system | 18,432 | `923be9c41068b7de6f14d93dd7fd28e31bbefbf2fd68609c0483597092becd5f` |
| C11 | JF16 | 7,914 | `fc4fa48ef7c96064d7879782c293c740e30f73f50e06db2ad6fc09bbb0dd2d31` |

The stock pair is the exact JF15/system pair retained in
`tests/fixtures/jukuhost-v15` and physically accepted on CS00000. The C11 pair
is the exact system/JF16 pair from the accepted C11 manifest and the physical
CS00000 session.

The available USB adapter identifies as Prolific `067B:2303`, product
`USB-Serial Controller D`, and exposes no USB serial number. Consequently the
release contract uses a Windows device-instance identity when one exists but
must report ambiguity instead of guessing when two indistinguishable
adapters are attached. Its Windows driver identity and the qualification OS
version remain W4 evidence because no real Windows environment is currently
available.

The pre-extraction regression boundary is the existing strict core test,
Linux PTY integration, stock/JF15 co-simulation, C11 co-simulation, reconnect
test, and DOS build/emulator gate. W1 must keep all of those green.

## W1 — shared runner extraction

Status: **complete**

The production lifecycle now has a public frontend-neutral API in
`jukuhost_runner.h`. It accepts immutable options, embedded or file-backed
boot artifacts, cooperative cancellation, log/state/progress callbacks, N4
console callbacks, and returns typed summary counters. The former production
body is compiled as `jukuhost_runner.c`; `jukuhost_main.c` is now only the
five-line CLI entry adapter. Linux and DOS build the same runner.

`sync/jukuhost_runner_check.sh` verifies defaults, null-input rejection,
callback delivery, summary delivery, and immediate cooperative cancellation
without opening serial or media. The following post-extraction gates pass:

- strict core vectors under GCC/Clang, signed/unsigned `char`, and sanitizers;
- runner callback/cancellation test;
- native Linux build and self-test;
- Linux PTY N3/N4, B:, duplicate, journal, capture, console, and reconnect;
- five-stock-system co-simulation and learned identity;
- physical-failure JF15 five-second delayed-core regression;
- stock/JF15 co-simulation;
- named-PTY serial disappearance and reopen;
- Open Watcom DOS build from the shared runner;
- complete DOS reproducibility, self-test, stock, and C8 emulator gate.

The complete aggregate C11 gate subsequently passed unchanged: normal boot,
passive session discovery, periodic late-host beacon, host replacement, and
NetDisk-reset recovery. An earlier run intermittently lost an internal STATUS
substring in this busy Linux environment; the same symptom reproduced from an
untouched pre-extraction `6255a4ef` worktree. No assertion, timeout, or retry
was weakened to obtain the accepted pass.

## W2 — Win32 platform and headless parity

Status: **desk-complete to the available non-Windows boundary**

`platform_win32.c` now supplies the production runner with a Windows 4.0-safe
clock, stop handling, memory report, exclusive COM open, complete DCB setup,
applied-setting verification, bounded reads/writes/drain, line-error
accounting, purge at framing transitions, and reopen through the existing
runner. `platform_file.c` uses the Open Watcom Win32 commit primitive for
journal and media flushes.

The deterministic payload generator validates the pinned W0 source files and
emits a checked C catalog. Both stock and C11 pairs are compiled into the PE;
native tests recompute every SHA-256 and verify mode selection. A release
build therefore has no loose boot/system dependency.

`sync/jukuhost_win32_check.sh` proves:

- four exact embedded payload identities and stock/C11 option mapping;
- strict config and stable-device-selection behavior;
- Win32 COM namespace, exclusive access, complete DCB setup, partial I/O,
  line-error handling, bounded drain, stop handling, and timer wrap through a
  native API shim;
- strict warning-free Open Watcom compilation;
- two byte-identical 177,152-byte PE builds;
- PE32/i386, GUI subsystem version 4.0;
- an exact reviewed allowlist of 92 direct system imports;
- deterministic icon/version resources and normalized resource timestamps;
- an exact five-file package, complete hashes, and four-payload manifest.

The qualified implementation is `f332a2d8`; its EXE SHA-256 is
`dd79caa86fdf55f5c8ddc82166d75eb568be2e0382eb6618f3d1d979e6b33026`.

Wine is not installed in the available environment, so the compiled
`--selftest`, headless process, and simulated-COM integration could not be run
as Windows processes. The native Win32 API shim covers the platform adapter,
but no real-Windows behavior is inferred from it.

## W3 — native UI and simple configuration

Status: **desk-complete to the available non-Windows boundary**

The cross-built `JUKUWIN.EXE` is now a Windows GUI-subsystem application with
one ordinary Win32 window. It provides C11/stock selection, safe serial-device
selection and refresh, A:/B: browsing, snapshot/read-only A: policy,
auto-listen, Listen/Stop, actual runner state and boot progress, live traffic
counters, an N4 console with bounded input, and a diagnostic transcript.

The UI freezes one configuration per session and runs the shared host runner
on a worker thread. Worker callbacks copy data through posted window messages;
the serial thread never calls a control. Stop, window close, and Windows
session shutdown request cooperative cancellation. Controls that affect a
session stay disabled until the runner has closed serial, evidence, journal,
and media resources.

The simple strict-ASCII `JUKUWIN.INI` parser, canonical formatter, path
resolver, defaults, semantic validator, and deterministic working-image name
are portable and directly unit-tested. UI saves use a flushed temporary file.
Current Windows discovers `MoveFileExA` dynamically for atomic write-through
replacement; the legacy path uses a tested backup/install/restore sequence and
startup recovery, without making that API a static Windows 95 import. A:
defaults to an exclusively opened snapshot; B: remains read-only. Each run
receives a new timestamp/PID evidence folder.
Retention recognizes only the owned session-name grammar, removes only the two
known evidence files, and leaves any directory containing an unknown file
untouched.

SetupAPI enumeration is dynamically discovered to preserve the legacy import
boundary. Selection follows an exact case-insensitive device-instance ID even
when the COM number changes. One unidentified adapter may be selected
automatically; zero devices waits; multiple devices without an identity is a
hard ambiguity. Explicit `COM1` through `COM256` remains available through the
INI and works even when a port is temporarily absent.

The build also provides `--selftest`, `--headless --config PATH`, an example
INI, an operator guide, and deterministic packaging. The current package has
only `JUKUWIN.EXE`, `JUKUWIN.INI`, `README.md`, `MANIFEST.json`, and
`SHA256SUMS`; no boot payload or runtime DLL is loose.

Current automated evidence:

- strict config parse/format/path tests;
- stable-identity, explicit-port, missing-device, and ambiguity tests;
- warning-free GUI compilation;
- two byte-identical 177,152-byte GUI EXEs after deterministic PE and resource
  timestamp
  normalization;
- PE32/i386 Windows GUI subsystem 4.0, embedded icon/version, and exact
  92-import allowlist;
- exact package membership, manifest identity, and complete SHA-256
  verification.

The current GUI EXE SHA-256 is
`dd79caa86fdf55f5c8ddc82166d75eb568be2e0382eb6618f3d1d979e6b33026`.

No Windows or Wine runtime is present in the available environment, so window
rendering, message-loop automation, and the actual `--selftest` process remain
unexecuted. Those are explicit environmental limitations, not inferred from a
successful cross-link. See the desk acceptance record for the full matrix.

## W4 — physical current-Windows qualification

Status: **pending real Windows hardware and OS**

## W5 — physical legacy-Windows qualification

Status: **pending real Windows 95 hardware and OS**
