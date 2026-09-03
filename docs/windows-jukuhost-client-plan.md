# Windows Juku host client plan

Status: **W0 COMPLETE — W1 SHARED RUNNER EXTRACTION NEXT**

Date: 2026-09-03

Implementation and qualification evidence is recorded in
[windows-jukuhost-client-implementation.md](windows-jukuhost-client-implementation.md).

## Goal

Build a small, dependable Windows application that boots and serves a Juku
with either a stock ROM or the C11 JukuNet ROM. The application must reuse the
existing portable C host implementation and preserve its admitted protocol,
media-safety, recovery, logging, and capture behavior.

The deliverable is one self-contained `JUKUWIN.EXE`, one simple editable INI
file, and user-supplied disk images. The executable contains the approved
stock-assisted and C11 boot payloads. It has no installer, DLL bundle, Python
runtime, framework runtime, registry dependency, or network dependency.

The first release is deliberately a host appliance with a basic native UI,
not a general emulator front end. An operator should be able to select the
serial adapter, choose `stock` or `c11`, mount A: and optionally B:, press
**Listen**, and understand whether the machine is waiting, booting, serving,
recovering, or stopped.

## Relationship to the portable-host plan

This work builds on the admitted portable C core described in
[portable-c-host-plan.md](portable-c-host-plan.md) and the implementation
ledger in
[portable-c-host-implementation.md](portable-c-host-implementation.md).

This document supersedes the older plan's **console-only** Win32 M3/M4 product
scope and its rule that no Win32 implementation may begin before the physical
Pocket8086 M2.3 gate. The Windows GUI work may proceed now because it is a new
operator priority. It does not waive or retroactively complete any physical
gate:

- Pocket8086 qualification remains a separate deliverable;
- Wine remains a desk test, not proof of real Windows serial timing;
- Windows 95 compatibility is retained where the chosen ANSI Win32 API subset
  permits it;
- a current physical Windows machine and serial adapter are the first release
  hardware gate;
- physical Windows 95 qualification remains separately pending until run on
  that hardware.

There will still be only one protocol implementation. Linux CLI, DOS CLI, and
the Windows GUI are front ends over the same core and session runner.

## Product contract

### Required modes

`stock` mode means:

1. listen for the stock Janet boot protocol at 9,600 baud, 8O1;
2. load the admitted JF15 stock-assisted core;
3. transfer its checked extension and embedded CP/M system at 19,200 baud,
   8N1; and
4. serve NetDisk/N4 at 19,200 baud, 8O1.

`c11` mode means:

1. listen passively at 19,200 baud, 8O1;
2. distinguish a checked C11 boot beacon from a checked live NetDisk request;
3. send the admitted JF16/system bundle only when C11 requests boot;
4. attach without disturbing an already-running CP/M session; and
5. automatically recover across a target reset or serial reconnect.

C8-C10 direct-fastboot operation and raw stock bootstrap without JF15 are not
first-release UI modes. The existing CLI keeps those diagnostic paths.

### Deployment shape

A normal portable folder contains:

```text
JUKUWIN.EXE
JUKUWIN.INI
CPM3.IMG             optional user disk
JUKEBOX.JUK          optional user disk
logs/                generated evidence, not a runtime dependency
```

The application reads no boot-stage or system binary from the deployment
folder. Approved JF15, JF16, and CP/M system bytes plus their names, versions,
sizes, SHA-256 identities, and source provenance are embedded at build time.
Disk images remain external and replaceable by the user.

The program is a 32-bit x86 native Win32 GUI executable using ANSI APIs and a
statically linked runtime. This keeps one artifact usable on Windows 95-class
systems and on current x64 Windows through normal 32-bit compatibility. A
current Windows release is the initial supported and physically qualified
environment. Windows on ARM and Wine are useful compatibility targets but are
not first-release hardware claims.

### Non-goals for the first release

- no installer, updater, service, tray agent, registry configuration, or
  shell integration;
- no Qt, .NET, Electron, browser UI, or other separately installed runtime;
- no ROM programmer, disk-image editor, artifact builder, or CP/M file
  manager;
- no arbitrary system/Fastboot payload selection in the normal UI;
- no new wire protocol, speed change, or target firmware change;
- no full VT terminal emulator;
- no simultaneous service of multiple Juku machines from one process.

## User interface

Use ordinary Win32 controls and one main window. The fixed first-release
layout contains:

- mode selector: **C11** or **Stock ROM**;
- serial-device selector with **Refresh**;
- drive A image field with **Browse** and `read-only`/`snapshot` policy;
- optional read-only drive B image field with **Browse** and **Eject**;
- **Listen** / **Stop** button;
- auto-listen-at-start checkbox;
- persistent state line and compact RX/TX/request/reconnect counters;
- scrollable CP/M console transcript and an input line;
- collapsible or tabbed diagnostic log.

Only controls that affect a stopped session are editable. Once listening
starts, the worker owns a frozen configuration snapshot. A mode, serial port,
or disk change first requires a clean stop; there is no half-applied live
reconfiguration.

The state line uses the shared runner's actual state rather than guessed text:

```text
Stopped
Validating configuration
Waiting for stock ROM
Waiting passively for C11 or live CP/M
Booting: stock Janet
Booting: Fastboot 42%
Serving NetDisk
Serial device lost; reconnecting
Target reset detected; rebooting
Stopping
Failed: <actionable reason>
```

The console is intentionally small: printable bytes, CR/LF, backspace, tab,
and direct ASCII input are enough for the admitted CP/M workflow. It does not
interpret ANSI escape sequences. Console input remains a bounded N4 queue and
cannot block or run on the serial thread.

Closing the window while active requests a cooperative stop and shows the
final result. If shutdown cannot complete inside the defined bound, the UI
reports the specific pending operation; it never silently abandons a media
write.

## Simple configuration

`JUKUWIN.INI` is ASCII, line-oriented, case-insensitive, strict about unknown
or duplicate keys, and resolved relative to the INI file. It is intentionally
smaller than the existing deployment manifest because boot payload identity
is compiled into the executable.

Initial schema:

```ini
[juku]
mode=c11
serial=auto
serial_id=
auto_listen=yes

[drive_a]
image=CPM3.IMG
mode=snapshot
working=CPM3-WORK.IMG

[drive_b]
image=JUKEBOX.JUK

[evidence]
directory=logs
capture=yes
verbose=no
keep_sessions=20
```

Rules:

- `mode` is exactly `stock` or `c11`;
- `serial` is `auto` or an explicit `COM1` through `COM256`;
- `serial_id` is written by the UI when a stable device identity is available;
- an empty `image` means that drive is not mounted;
- A: is `read-only` or `snapshot`; direct writes to the selected base image are
  deliberately absent from the basic UI;
- B: is always read-only and must have native 800 KiB geometry;
- a relative working-image and evidence path is beside the INI file;
- `keep_sessions=0` means no automatic evidence deletion; otherwise cleanup
  removes only positively identified old session directories after a new
  session has closed successfully;
- missing optional keys receive documented conservative defaults;
- malformed values prevent auto-listen and are displayed with section, key,
  and line number.

The UI can save the same file atomically through a temporary file, flush, and
replace. It never stores configuration in the registry. Hand edits remain a
supported workflow. Passwords, credentials, and machine-specific secrets are
not part of the format.

An advanced command-line test switch may load the existing strict
`JUKUHOST.INI`, but the normal GUI does not expose artifact paths or weaken
the existing CLI format.

## Architecture

The current protocol primitives are already reusable, but production
orchestration, platform calls, and CLI presentation are still concentrated in
`host/src/jukuhost_main.c`. The first implementation step is therefore an
extraction, not a Windows copy of that file.

```text
                       admitted portable C protocol core
                 Janet / Fastboot / N3 / N4 / media / session
                                      |
                            shared host runner API
              lifecycle / callbacks / counters / cancellation
                         /                         \
             existing CLI adapter             Windows GUI adapter
           POSIX and DOS platforms       Win32 platform + window thread
                         \                         /
                    identical logs and binary captures
```

### Shared runner

Create a public application-level runner that owns one complete host session.
Its inputs are values, artifact views, media specifications, a platform
transport, and callbacks; it does not parse command lines or manipulate UI
controls.

The API must provide:

- immutable start options;
- caller-supplied stock/C11 artifact views with size and SHA-256 identity;
- state, progress, log-event, console-output, and final-summary callbacks;
- bounded console-input enqueue;
- cooperative cancellation safe at every session phase;
- final typed result matching current exit classes;
- request, byte, retry, reset, reconnect, read, and write counters;
- no global frontend state.

The existing Linux/DOS CLI becomes a thin adapter over this runner. Its
options, exit codes, log/capture bytes, serial behavior, and accepted tests
must remain unchanged. Extraction is complete only after the current core,
Linux PTY, stock, C8/C11 co-simulation, reconnect, and DOS checks pass without
golden-output drift.

### Platform boundary

Extend `platform.h` only with operations required by both front ends. UI
messages, HWNDs, Windows headers, and COM discovery never enter the portable
core or runner.

Add a Win32 platform implementation for:

- monotonic millisecond deadlines with wrap-safe comparison;
- bounded sleep/wait;
- serial open/configure/read/write/drain/close/reopen;
- file identity, media, journal, log, capture, flush, and atomic config save;
- process/window stop notification;
- optional serial-device enumeration in a separate Win32-only module.

All protocol execution occurs on one worker thread. The UI thread only owns
windows and messages. Worker callbacks copy bounded event data and use
`PostMessage`; they never call a control directly. UI console input is copied
into a locked bounded queue consumed by the runner. Stop uses an event checked
at every bounded I/O wait.

No normal serial or disk operation may wait forever. Long-lived listening is
implemented as repeated bounded waits plus state checks, not an uninterruptible
API call.

### Embedded payload catalog

Build tooling imports one explicitly approved artifact set and generates a C
payload catalog compiled into the executable. The catalog contains one shared
system image where stock and C11 use identical bytes, plus exact JF15 and JF16
bundles. Each entry contains:

- stable symbolic name and semantic role;
- payload bytes and length;
- SHA-256;
- source repository revision;
- source manifest path and artifact filename;
- target mode and protocol version.

The generator fails if an input differs from its pinned size or hash. A clean
build never selects "latest" by directory order or modification time. Runtime
self-test recomputes every embedded digest before enabling **Listen**, and the
About/status view plus session log records the complete catalog identity.

Generated byte sources may be omitted from review only if both their compact
manifest and deterministic generator are reviewed and the CI build proves the
resulting EXE identity. The final package has no loose payload files.

## Serial-device behavior

Serial configuration is explicit and complete on every open:

- 8 data bits, one stop bit;
- odd or no parity according to the active phase;
- no hardware or software flow control;
- checked 9,600 and 19,200 baud;
- stale input/output purge only at admitted phase transitions;
- bounded partial reads and writes;
- transmit-drain semantics measured and logged;
- `ClearCommError` line-error accounting;
- exclusive port ownership.

Open `COM10` and above through the `\\.\COMn` namespace internally while
showing ordinary `COMn` names to the user.

Modern Windows enumeration records display name, COM name, device-instance
identity, and hardware identity when available. When `serial=auto`:

1. an exact saved `serial_id` match wins even if its COM number changed;
2. otherwise one compatible present serial device may be selected;
3. zero matches remains in a visible waiting state;
4. multiple plausible matches is an ambiguity, not permission to guess;
5. unplug/replug re-enumerates and reopens the same identity within bounded
   recovery windows.

Adapters without a unique serial identity can only be followed by their
available device-instance information. If Windows changes that identity, or
two indistinguishable adapters are connected, the application stops at
**Select serial device**. The UI never silently moves a live session to a
different adapter merely because it inherited the old COM number.

On legacy Windows where extended device enumeration is unavailable, explicit
COM selection remains supported and `auto` is limited to unambiguous present
COM names. Optional modern discovery APIs must be loaded dynamically if a
static import would break the reviewed Windows 95 import contract.

## Durability and safety contract

The GUI inherits rather than reimplements these existing properties:

- strict frame validation and parser resynchronization;
- duplicate request replay without duplicate write side effects;
- C11 passive discovery and already-running-session attachment;
- explicit target-reset recovery;
- bounded serial reopen;
- read-only B: enforcement;
- snapshot A: with immutable base, checked working-copy size, CRC journal,
  synchronous record update, and startup recovery;
- required log/capture failure as a visible fatal result;
- stable result classes and final counters.

The Windows layer adds these controls:

- exclusive writable-media access and refusal when another process owns it;
- exclusive serial access with the owning COM name in the error;
- one immutable config snapshot per run;
- embedded payload verification before opening the target port;
- disk geometry and write-policy validation before listening;
- evidence directory created and proven writable before boot;
- timestamped per-session evidence so a new run never truncates an old run;
- bounded, post-session retention cleanup that cannot match disk-image paths;
- orderly Windows logoff/shutdown and window-close handling;
- no forced thread termination as a normal stop mechanism;
- no automatic retry after artifact, media, journal, or evidence corruption.

If the host is started in C11 mode while CP/M is silently playing music, it
sends nothing until a checked target frame arrives. A reassuring **Waiting
passively; target may already be running** state is not treated as a timeout
or failure.

## Build and packaging

Use the repository-pinned Open Watcom V2 toolchain for the primary Win32 x86
artifact, matching the existing DOS/Windows portability decision. Add one
owned build script that:

1. verifies the compiler archive and identity;
2. verifies and generates the embedded payload catalog;
3. compiles strict C with warnings as errors;
4. links the GUI subsystem and static runtime into `JUKUWIN.EXE`;
5. embeds version information and the application icon without external
   runtime files;
6. audits the PE machine, subsystem version, imports, sections, size, and
   SHA-256;
7. rebuilds in a clean directory and checks reproducibility;
8. runs the EXE self-test under an isolated Wine prefix.

The checked package manifest contains the EXE hash, embedded payload hashes,
compiler identity, source commit, supported OS baseline, and known physical
qualification status. `JUKUWIN.INI` is shipped as a documented example, not
compiled defaults disguised as user configuration.

The executable supports hidden/automation-safe switches for `--selftest`,
`--headless`, and `--config FILE`. These exercise the same runner and Win32
platform layer; they are not a second host implementation. Normal double-click
startup shows only the GUI.

## Verification strategy

### Gate W0 — freeze the Windows product contract

- approve this scope and INI schema;
- select and pin exact stock/C11 embedded payload identities;
- inventory all orchestration currently private to `jukuhost_main.c`;
- freeze current CLI logs, captures, exit results, and co-simulation outcomes
  used to judge the extraction;
- record the current Windows version, adapter identity, and driver used for
  first physical qualification.

Exit: no payload or behavior is selected implicitly during implementation.

### Gate W1 — shared runner extraction

- move lifecycle orchestration behind a frontend-neutral API;
- adapt the Linux and DOS CLIs without changing their public operation;
- add cancellation, event, console, progress, and summary callbacks;
- run strict GCC/Clang signed/unsigned-char and sanitizer tests;
- pass all current Linux PTY, stock, C8/C11, reconnect, media, and DOS gates;
- compare retained logs/captures and account for every intentional metadata
  difference.

Exit: `jukuhost_main.c` is a CLI adapter and Windows has no reason to fork the
host state machine.

### Gate W2 — Win32 platform and headless runner

- implement Win32 serial, clock, stop, filesystem, media, journal, log, and
  capture operations;
- cross-build the single EXE reproducibly;
- audit its PE imports against the legacy-safe allowlist;
- pass embedded-payload, config, hash, file, snapshot, journal-recovery,
  cancellation, timer-wrap, and malformed-input self-tests under Wine;
- map Wine `COM1` to a simulator PTY and pass stock and C11 boot, A:/B:, N4,
  target-reset, and host-reconnect workloads;
- compare exact wire capture and final media with the admitted Linux run.

Exit: all automatable Win32 host behavior works before UI or physical serial
timing can hide defects.

### Gate W3 — basic UI

- implement the fixed control set and worker/UI message boundary;
- load, validate, edit, and atomically save the simple INI;
- prove auto-listen, manual Listen/Stop, close-during-each-phase, and clean
  restart in one process;
- prove bounded console input/output under heavy disk and log activity;
- test missing images, bad geometry, locked media, corrupt journals, missing
  ports, ambiguous adapters, evidence failure, and malformed config;
- run a scripted UI smoke test on a clean Windows virtual machine.

Exit: every failure is actionable in the window and no UI action can bypass a
runner safety check.

### Gate W4 — physical current-Windows qualification

Use the exact packaged EXE and the intended USB-to-serial adapter on the real
Windows host. Retain configuration, package manifest, logs, captures, driver
identity, and machine/OS version. Exercise:

- repeated cold stock-ROM boots to CP/M;
- repeated cold C11 boots and late-host passive discovery;
- attach to already-running C11 CP/M;
- A:/B: directory/read, Jukebox playback, N4 input/output, status, time, warm
  boot, and a controlled snapshot-A: write;
- target reset during boot and NetDisk;
- host Stop/Listen replacement;
- adapter unplug/replug with the same COM number and with a changed COM
  number;
- two plausible adapters connected, proving ambiguity is reported;
- window close and Windows shutdown while idle and while serving;
- a long unattended serving run with bounded evidence growth.

Compare request counts, retries, media hashes, timing, and wire capture with
the accepted Linux/C11 baseline. Any unexplained retry growth, corruption,
misidentified adapter, or UI hang fails the gate.

Exit: the application is ready for ordinary use on that Windows machine and
adapter combination.

### Gate W5 — legacy Windows qualification

- start the exact W4 executable on physical Windows 95-compatible hardware;
- verify its imports, UI creation, INI handling, filesystem behavior, timer
  resolution, physical COM configuration, drain, and clean close;
- run stock and C11 boot/NetDisk/N4 with a physical UART;
- document discovery limitations where legacy Windows lacks stable modern
  device identity.

Exit: only this gate permits an unqualified **Windows 95 supported** claim.
Failure here does not invalidate the already qualified current-Windows
release unless the fix touches shared behavior.

## Release artifacts

The first release is complete when the repository can produce and retain:

- deterministic `JUKUWIN.EXE`;
- example `JUKUWIN.INI`;
- package manifest with executable, payload, source, and compiler identities;
- concise operator guide covering stock/C11 choice, disks, Listen/Stop,
  recovery states, evidence, and safe writable-image handling;
- Wine/headless test report;
- physical current-Windows acceptance report and captures;
- explicit legacy-Windows status rather than an inferred compatibility claim.

## Completion criteria

The task is complete only when all of the following are true:

- the GUI and existing CLIs use one shared host runner and protocol core;
- stock and C11 boot/service behavior pass simulator and physical Windows
  gates;
- the release folder needs no loose boot/system artifacts or runtime DLLs;
- the simple INI fully describes mode, serial selection, automounts, policies,
  auto-listen, and evidence preferences;
- changing COM numbers is handled by stable identity when Windows and the
  adapter expose one, with safe ambiguity handling otherwise;
- snapshot media and crash recovery pass fault injection;
- auto-listen and every stop/close path are bounded and deterministic;
- the package identities and qualification limits are recorded;
- no durability regression is hidden behind the UI.
