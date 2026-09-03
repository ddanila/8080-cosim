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

Status: **implementation complete; C11 aggregate co-sim requalification open**

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

The aggregate C11 co-simulation is not yet recorded as requalified. Its first
STATUS transcript intermittently loses an internal N4 substring in this busy
Linux environment. The exact same failures reproduce from an untouched
`6255a4ef` worktree, at different transcript offsets, proving this is not
specific to the runner extraction. It remains an open qualification item
rather than being hidden behind the passing C11 boot and NetDisk activity.

## W2 — Win32 platform and headless parity

Status: **platform/build complete; runtime and serial qualification open**

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

`sync/jukuhost_win32_check.sh` currently proves:

- four exact embedded payload identities and stock/C11 option mapping;
- strict warning-free Open Watcom compilation;
- two byte-identical 150,016-byte PE builds;
- PE32/i386, console subsystem version 4.0;
- an exact reviewed allowlist of 53 direct KERNEL32/USER32 imports.

The current artifact SHA-256 is
`8a5e6243e1e5932083dbd66de6335dd5eeccfde6f88dfaa19bc68195523f17cc`.
It is an intermediate headless artifact, not the GUI release identity.

Wine is not installed in the available environment, so its self-test and COM
integration are still open. A native Win32-API shim test is also required
before this gate can be called desk-complete. No real-Windows behavior is
claimed.

## W3 — native UI and simple configuration

Status: **not started**

## W4 — physical current-Windows qualification

Status: **pending real Windows hardware and OS**

## W5 — physical legacy-Windows qualification

Status: **pending real Windows 95 hardware and OS**
