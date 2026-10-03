# Portable Juku host contract

The production network host is implemented in portable C under `host/`.
Linux and macOS use the POSIX backend; DOS and Windows use Open Watcom V2.
The Windows product is the GUI described in
[windows-jukuhost-client.md](windows-jukuhost-client.md).

## Runtime requirements

- One shared core implements Janet, Fastboot, NetDisk, N4, checksums, media
  bounds, and recovery. Frontends use `jukuhost_runner.h`.
- Serial operations, protocol waits, and cancellation are bounded. Applied
  framing must be verified; simulator PTY and Wine exceptions must be explicit.
- Disk images remain file-backed. Snapshot A: preserves the input image;
  writable operations use the CRC-protected transaction journal. B: is read-only.
- Human logs and optional byte captures record protocol and recovery failures.
- Production callers use the C executable. The retired Python implementations
  are non-runnable test fixtures; Python remains supported for analysis and tests.
- Stock/JF17 uses 9,600/8O1 throughout bootstrap and NetDisk. C11/C12 use their
  authenticated V16 payloads and 19,200-baud recovery profiles.
- Configuration and payload identities are validated before starting a session.
  See [jukuhost-config.md](jukuhost-config.md).

## Platform qualification

| Platform | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Linux | Native protocol, fault, media and PTY checks; physical CS00015 qualification | Requalify when a platform or protocol change affects the accepted workload |
| macOS | Native arm64 C8 cold boot and focused CS00015 workload | Full reconnect, reset, media and endurance matrix |
| DOS / Pocket8086 | Reproducible 16-bit executable; DOSBox-X serial-to-simulator checks | Physical Pocket8086-to-CS00015 UART, latency, memory and endurance matrix |
| Windows | Reproducible PE, native API shims, Wine stock/C11/C12 matrix; Windows 95 guest C12 boot and reset recovery | Current Windows and physical Windows 95 serial hardware, GUI and endurance qualification |

A simulator, Wine, or VM result does not establish physical adapter behavior.
The DOS physical gate remains open independently of Windows implementation.

## Verification

```sh
sync/jukuhost_core_check.sh
sync/jukuhost_runner_check.sh
sync/jukuhost_linux_check.sh
sync/jukuhost_dos_check.sh
sync/jukuhost_win32_check.sh
sync/jukuhost_win32_wine_e2e.sh
```

The platform scripts document required compilers, emulators and adjacent
payload sources. Additional simulator guards are listed in
[portable-c-host-implementation.md](portable-c-host-implementation.md).

## Physical evidence

- [Linux CS00015 qualification](portable-c-host-m2.1-physical-acceptance.md)
- [DOS artifact and emulator qualification](portable-c-host-m2.2-dos-acceptance.md)
- [macOS focused physical result](portable-c-host-macos-physical-check.md)
- [Windows 95 guest result](windows-jukuhost-client-win95-acceptance.md)
- [Frozen byte and behavior contract](portable-c-host-m0-contract.md)
