# Windows Juku host client desk acceptance

Date: 2026-09-03

Qualified implementation: `f332a2d885f09e3fbae7b6e2609bfc0ac7fd78fb`

Result: **PASS at the available non-Windows desk boundary**

This accepts the implementation and all verification possible in the
available environment. It does not claim execution on Windows, physical COM
timing, CS00000 interoperability from the Windows binary, or Windows 95
support. Those remain plan gates W4 and W5.

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
all package hashes, matched the EXE identity in the manifest, and verified the
four embedded stock/C11 boot payload records. No boot payload or runtime DLL
is loose in the package.

## Accepted checks

The following commands passed without source or assertion changes between a
failing and accepted run:

```text
sync/jukuhost_core_check.sh
sync/jukuhost_runner_check.sh
sync/jukuhost_linux_check.sh
python3 tests/jukuhost_serial_reconnect_test.py
python3 tests/jukuhost_v15_delayed_pty_test.py
python3 tests/jukuhost_stock_v15_cosim_test.py
sync/jukuhost_stock_cosim_check.sh
sync/jukuhost_c11_cosim_check.sh
sync/jukuhost_dos_check.sh
sync/jukuhost_win32_check.sh
```

Together these cover strict GCC/Clang core vectors, runner callbacks and
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

## Explicitly unavailable

The test host was Ubuntu 26.04 LTS with Linux 7.0.0, GCC 15.2.0, Clang 21.1.8,
and GNU binutils. Neither Windows nor Wine was installed. Therefore:

- `JUKUWIN.EXE --selftest` was compiled but not executed as a Windows process;
- the GUI was not rendered or driven in a Windows message loop;
- Wine PTY-to-COM stock/C11 integration was not available;
- no Windows driver/device-instance behavior was observed for the Prolific
  `067B:2303` adapter;
- no physical Windows-to-CS00000 boot, disk, N4, reconnect, shutdown, or
  endurance run was performed;
- no Windows 95 execution or physical serial qualification was performed.

The accepted outcome is consequently: **implementation and non-Windows desk
testing complete; ready for W4 physical current-Windows qualification**. A
successful W4 result is required before calling the client ready for ordinary
use on that Windows machine. Only W5 can establish Windows 95 support.
