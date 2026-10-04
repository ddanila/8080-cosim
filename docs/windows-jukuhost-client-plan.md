# Windows Juku host product contract

The portable host package contains `JUKUWIN.EXE`, `JUKUWIN.INI`, `README.md`,
`MANIFEST.json` and `SHA256SUMS`. The published floppy transfer bundle adds
the CP/M development disk and its license, uses `README.TXT`, `MANIFEST.JSN`
and `SHA256.TXT`, and preselects Stock ROM. Boot payloads are embedded in
the executable; disk images remain separate files. The current operator guide is
[windows-jukuhost-client.md](windows-jukuhost-client.md), and qualification is
tracked in
[windows-jukuhost-client-implementation.md](windows-jukuhost-client-implementation.md).

## Product requirements

- A Windows 95-compatible ANSI Win32 GUI uses the shared C protocol/media
  core and runner. Linux, macOS and DOS remain frontends of that same core.
- C12, C11 and stock modes use the checked embedded catalog. Configuration
  defaults and the source INI select C12; the floppy package writes a Stock ROM
  INI for its bundled development disk.
- Listen/Stop, adapter selection, A:/B: image selection, N4 console and visible
  diagnostics are available without a command shell.
- Serial/device ambiguity is reported; the host does not guess among identical
  adapters. Explicit COM selection remains supported.
- A: defaults to a private snapshot with journaled writes; B: remains read-only.
- Payload hashes, configuration and filesystem access are checked before
  serial service. A failed evidence write stops the run.
- Stop and close request bounded cooperative shutdown. Session settings stay
  fixed until the worker releases serial and media resources.
- Startup diagnostics and per-session captures make failures inspectable.
- Packaging uses the pinned compiler, reproducible PE/resources, reviewed
  legacy imports and a manifest identifying the exact artifacts.

## Release acceptance

The build must pass `sync/jukuhost_win32_check.sh`. The actual executable must
pass the stock/C11/C12 Wine-to-simulator matrix with the recorded parity
emulation boundary. The current wrapper tests one boot and timed disk service
per mode; it does not reset the target, replace the host, disconnect serial,
or exercise GUI Stop/close. Reset and reconnect remain release requirements
requiring separate evidence; a Wine matrix pass does not satisfy them.

Native API shims, Wine and the successful Windows 95 guest C12 run establish
separate desk/guest results. Physical qualification still requires the real
Windows OS, adapter and board combination: cold boot, A:/B:, N4, target reset,
host replacement, writes, journal recovery, GUI stop/close and endurance.
A physical Windows 95 release uses the native COM-port contract; current
Windows USB-adapter qualification is a separate result.

The incomplete DOS/Pocket8086 physical matrix remains governed by
[portable-c-host-plan.md](portable-c-host-plan.md) and does not prevent Windows
implementation work.
