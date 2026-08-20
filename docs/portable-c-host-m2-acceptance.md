# Portable C host M2 acceptance

Status: **ACCEPTED ON NATIVE LINUX — READY FOR PLATFORM PORTS**

This report closes the native-Linux parity and Python-host-retirement gate in
the [portable C host plan](portable-c-host-plan.md). It does not qualify
macOS, Wine, Win32, or physical Windows 95; those begin at M3 and use the same
admitted C core.

## Accepted identities

- C host source and retirement checkpoint: `8080-cosim` commit `6724d33b`.
- Native command: `build/jukuhost`, reporting `jukuhost 0.1.0-m2`.
- Frozen Python-era baseline: commit `81f64f76` and
  `tests/fixtures/jukuhost/python-era-v1.txt`.
- Linux smoke kit v2: commit `6724d33b`, OCI digest
  `sha256:579e79e9fc801266f439e5a62ec2579e474ba64642cfe6da72390826a06f64c8`.
- CP/M Plus CI image built from that kit: digest
  `sha256:245934e74520c45bb5702fa3948b4da165c80e4c1b6957fd266ed09c1916941f`.

## Baseline-to-C comparison

| Required behavior | Frozen Python-era evidence | Native C evidence | Result |
| --- | --- | --- | --- |
| Stock Janet bootstrap and retry behavior | `sync/janet_netboot_check.sh`: all five archived systems and automatic identity | `sync/jukuhost_stock_cosim_check.sh`: the same five images and learned identity through `jukuhost` | pass |
| Checksums, frame parsing, image preparation, Fastboot and disk semantics | immutable M0 vector plus frozen Fastboot and disk fixture tests | strict-C99 core test under signed/unsigned `char`, GCC, Clang and sanitizers | pass |
| Current C8/JR16 and Fastboot V16 | frozen readiness, framing, CRC and recovery expectations | complete C8 boot to CP/M, missed-ready recovery and reset-mid-stream restart | pass |
| N3 A:/B: and N4 | frozen raw/compact/read-ahead/write, duplicate and console fixtures | PTY and C8 sessions cover native B:, writes, duplicate replay, capabilities and bidirectional N4 | pass |
| Host loss and replacement | frozen reconnect and resume outcomes | named-PTY reopen, live host replacement, target reset and resumed requests | pass |
| Writable-media safety | frozen mutation and failure cases | portable crash-point matrix plus real POSIX journal rollback and cleanup | pass |
| Logs, capture and exit behavior | M0 observable-result contract | text/file logging, CRC-protected capture replay, required-evidence failures and clean SIGINT during an active reply | pass |
| Normal launchers and acceptance tooling | Python-era inventory frozen at M0 | `juku_run.py`, CP/M Plus physical acceptance, demonstration generator and VC launcher invoke only `jukuhost` | pass |

The comparison is against observable bytes, state transitions, media outcomes,
and recovery behavior. It deliberately does not preserve Python tracebacks,
object layouts, or JSON as a runtime dependency.

## Reproducible gate

Run the complete local gate with:

```sh
sync/jukuhost_m2_check.sh
```

It runs the frozen Python-era oracle and five-system suite, portable/native C
tests, PTY media/evidence/reconnect tests, stock and C8 end-to-end simulator
workloads, operational-wrapper checks, and the current network-ROM ABI/fault
matrix. On 2026-08-20 it completed with:

```text
JUKUHOST-M2-CHECK: PASS (Linux parity; C-only production host)
```

The structural UART/ROM checks also passed separately:

```sh
sync/network_first_rom_hdl_check.sh
sync/serial_check.sh
```

GitHub CI was green for `8080-cosim` commit `6724d33b`, including generic,
report, HDL, and smoke-kit workflows. CP/M Plus commit `e186603` passed its
digest-pinned distribution and network-smoke CI.

## Related-repository closure

| Repository | Accepted change | Publication |
| --- | --- | --- |
| `cpm-plus-juku` | physical acceptance invokes C; obsolete C4 runner removed; simulator imports frozen fixtures; CI consumes smoke-kit v2 | `master` through `e186603`, pushed |
| `cpmish` | operational documentation invokes C; historical cosim imports frozen fixtures | `juku` through `33575ef`, pushed |
| `vc8080` | interactive launcher invokes C; system regression imports frozen fixtures | local `main` through `09c381b`; this checkout has no configured remote |

The CP/M Plus network smoke reached `A>`, executed `DIR`, and verified `VER`.
The CP/Mish 51K RAM-BIOS smoke passed its polled-keyboard `DIR` workload. The
focused VC system session passed through the fixture import after its launcher
had already moved to C.

## Single-host audit

The former `tools/janet_netboot.py`, `tools/janet_fastboot.py`, and
`tools/janet_disk_server.py` commands do not exist. Their implementations are
non-executable modules under `tests/fixtures/`, have no `__main__`, and are
admitted only for historical regression/fault injection. Imports are guarded:
they may occur in tests or the four explicitly retained BAUD/UART diagnostic
laboratories, never in an operational wrapper. Repository documentation has no
runnable command using the retired paths, and there is no Python fallback.

The independent Jukuravi probe/upload laboratory remains Python by explicit
plan scope; it is a different diagnostic protocol and is not an alternative
Janet/Fastboot/NetDisk/N4 production host.

## Exit decision

M2 is complete. The C executable is the sole supported production network
host on Linux, and its frozen specifications, vectors, captures, and test
fixtures no longer require a runnable Python server. The next permissible
implementation work is M3: the pinned Open Watcom Windows 95 build and
headless Wine self-test. No M3 code is included in this acceptance state.
