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
to `cpm-plus-juku` revision `d2e5b31` and these exact artifacts:

| Mode | Role | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| stock | system | 16,896 | `254f940e36501dcf3f46c5ba23b2b6cb3b1b7f3a13b1e42ae9786f2fa337a4a4` |
| stock | JF15 | 9,670 | `881befd8ebd306ae7313b2dff8b83cb8d964988e17627d76efedaa49e6a19a5d` |
| C11 | system | 18,432 | `923be9c41068b7de6f14d93dd7fd28e31bbefbf2fd68609c0483597092becd5f` |
| C11 | JF16 | 7,914 | `fc4fa48ef7c96064d7879782c293c740e30f73f50e06db2ad6fc09bbb0dd2d31` |
| C12 | system | 18,432 | `74abab89c14e8429eec943c8b7c77ad33675cbf411fde5190d4657a3d28bdb79` |
| C12 | JF16 | 7,914 | `51788bc93dac1e03a541239eb7f2837e3e03ef2519c3703aa052fe15b248f202` |

The stock pair is the exact JF15/system pair retained in
`tests/fixtures/jukuhost-v15` and physically accepted on CS00000. The C11 pair
is the exact system/JF16 pair from the accepted C11 manifest and the physical
CS00000 session. The C12 pair adds ABI 1.5 runtime-console control while the
C11 pair remains selectable and byte-identical to its accepted release. The
pinned C12 source revision also carries the active-state-aware VIDTEST disk
utility and manifest-bound cold/runtime/full physical acceptance workflows;
disk images remain external to the executable as required by the product
contract.

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
runner. `platform_file.c` flushes Open Watcom streams and their native Win32
handles with `FlushFileBuffers` for journal, snapshot, and media durability.

The deterministic payload generator validates the pinned W0 source files and
emits a checked C catalog. The stock, C11, and C12 pairs are compiled into the
PE; native tests recompute every SHA-256 and verify mode selection. A release
build therefore has no loose boot/system dependency.

`sync/jukuhost_win32_check.sh` proves:

- six exact embedded payload identities and stock/C11/C12 option mapping;
- strict config and stable-device-selection behavior;
- Win32 COM namespace, exclusive access, complete DCB setup, partial I/O,
  line-error handling, bounded drain, stop handling, and timer wrap through a
  native API shim;
- strict warning-free Open Watcom compilation;
- two byte-identical 204,800-byte PE builds;
- PE32/i386, GUI subsystem version 4.0;
- an exact reviewed allowlist of 92 direct system imports;
- deterministic icon/version resources and normalized resource timestamps;
- an exact five-file package, complete hashes, and six-payload manifest.

The current C12-capable EXE SHA-256 is
`a93c97580d2af23dfda77d84736b0618e8ac97820d7bb06aaddb7f7a04bb2e25`.

At the 2026-09-03 W2 acceptance boundary Wine was unavailable, so the compiled
process and simulated COM path remained unexecuted. The later W3.1 result below
supersedes that environmental limitation without claiming real Windows.

## W3 — native UI and simple configuration

Status: **desk-complete to the available non-Windows boundary**

The cross-built `JUKUWIN.EXE` is now a Windows GUI-subsystem application with
one ordinary Win32 window. It provides C12/C11/stock selection, safe serial-device
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
- two byte-identical 204,800-byte GUI EXEs after deterministic PE and resource
  timestamp
  normalization;
- PE32/i386 Windows GUI subsystem 4.0, embedded icon/version, and exact
  92-import allowlist;
- exact package membership, manifest identity, and complete SHA-256
  verification.

The current GUI EXE SHA-256 is
`a93c97580d2af23dfda77d84736b0618e8ac97820d7bb06aaddb7f7a04bb2e25`.

At the 2026-09-03 W3 acceptance boundary no Windows or Wine runtime was
present. The later W3.1 result below executes self-test and all three headless
protocol paths, but does not automate or qualify the GUI message loop.

## W3.1 — local Wine protocol end-to-end

Status: **desk-complete**

Implementation `244d38addcee4b862a2556c1146ab2b09e1d05ea` introduced the
explicit, local-only Wine harness; the C12 host milestone extends it to the new
mode. It creates an isolated 32-bit prefix, maps Wine `COM1` to a `socat` PTY
pair, and runs the actual GUI-subsystem PE in bounded headless mode against the
stock, C11, and C12 co-simulations. The ordinary Windows gate runs only the
fast compiled self-test when Wine is available; the longer protocol run is not
wired into CI.

The accepted Wine run covered the stock Janet bootstrap and V15 transition at
9,600/19,200 baud, the C11 and C12 passive beacons and their independently
pinned V16/NetDisk paths at 19,200 baud, A: snapshot creation, C11/C12 B:
mounting, disk reads, clean bounded shutdown,
capture generation, independent capture decoding, and unchanged base-image
hashes. All three sessions ended with zero retries and UART errors. See
[windows-jukuhost-client-wine-acceptance.md](windows-jukuhost-client-wine-acceptance.md)
for exact evidence.

Wine 10's PTY serial backend accepts odd parity but reports `NOPARITY` through
`GetCommState`. The Win32 backend therefore recognizes Wine dynamically and
allows only that exact parity readback mismatch, with an explicit warning.
All other DCB checks remain strict, and native Windows still rejects any
parity mismatch. This validates byte-level protocol behavior, not physical
parity, adapter identity, Windows scheduling, the visible UI, or CS00000.

## W4 — physical current-Windows qualification

Status: **pending real Windows hardware and OS**

## W5 — physical legacy-Windows qualification

Status: **pending real Windows 95 hardware and OS**
