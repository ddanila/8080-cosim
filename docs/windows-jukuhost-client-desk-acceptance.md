# Windows Juku host client desk acceptance

Date: 2026-09-03

Qualified implementation: `f332a2d885f09e3fbae7b6e2609bfc0ac7fd78fb`

Result: **PASS at the available non-Windows desk boundary**

This historical pre-Wine/C12 record qualifies build/API/package behavior for
the named revision. Later binaries and runtime results have separate acceptance
records linked below.

## Artifact

The pinned Open Watcom V2 compiler source is `cf43271464fdd57065d3d72de8ca917c55c6a887`;
the verified bootstrap identity is
`f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85`.
Two independent builds produced the same artifact:

| Property | Accepted value |
| --- | --- |
| File | `JUKUWIN.EXE` |
| Size | 177,152 bytes |
| SHA-256 | `dd79caa86fdf55f5c8ddc82166d75eb568be2e0382eb6618f3d1d979e6b33026` |
| Format | PE32/i386 |
| Subsystem | Windows GUI 4.0 |
| Direct imports | 92, exact reviewed allowlist |
| Resources | deterministic application icon and version 0.1.0 |

The package checker accepted exactly five files: `JUKUWIN.EXE`,
`JUKUWIN.INI`, `README.md`, `MANIFEST.json`, and `SHA256SUMS`. It recomputed
all package hashes, matched the EXE identity in the manifest, and checked that
the payload catalog contained four records with the stock/C11 mode set. That
check did not inspect embedded payload bytes inside the EXE. No boot payload
or runtime DLL is loose in the package.

## Accepted checks

The accepted checks covered strict GCC/Clang core vectors, runner callbacks and
cancellation, Linux PTY protocol/media/evidence behavior, serial loss and
reopen, delayed stock startup, the JF15 stock path, five stock systems, all C11
boot/passive/replacement/reset scenarios, and the complete reproducible DOS
build/emulator matrix.

The Windows gate additionally passed portable payload/config/device-selection
tests and a Win32 API shim covering `COM10+` names, exclusive open, DCB parity
and flow-control settings, bounded reads, partial writes, line errors, drain,
stop events, error mapping, and 32-bit timer wrap. The configuration-store shim
also exercised both dynamic atomic replacement and the legacy
backup/install/restore failure path. `MoveFileExA` is therefore dynamically
discovered when available and is absent from the legacy static import set.
Open Watcom compiled every Windows translation unit with warnings as errors.
PE audit confirmed the icon and version resources, zeroed build/resource
timestamps, GUI subsystem, and the exact import allowlist. Package membership
and hashes then passed.

## Qualification boundary

The accepted binary was compiled and audited, but not executed on Windows or
Wine. API shims do not establish driver behavior, physical serial timing or
Windows-to-board interoperability.

Current runtime evidence belongs to
[Wine acceptance](windows-jukuhost-client-wine-acceptance.md) and
[Windows 95 guest acceptance](windows-jukuhost-client-win95-acceptance.md).
Their named binaries and environments differ from this pre-C12 artifact;
neither substitutes for physical serial qualification. Use
[the operator guide](windows-jukuhost-client.md) for the current package and
[the platform contract](portable-c-host-plan.md) for remaining gates.
