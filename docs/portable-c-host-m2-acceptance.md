# Portable C host M2 acceptance

Status: **ACCEPTED ON NATIVE LINUX AND PHYSICAL CS00015**

This report closes the native-Linux parity and Python-host-retirement gate in
the [portable C host plan](portable-c-host-plan.md). Its exact Linux build has
since passed physical M2.1 on CS00015; that evidence is retained in
[portable-c-host-m2.1-physical-acceptance.md](portable-c-host-m2.1-physical-acceptance.md).
This is a revision-qualified M2 record. DOS, macOS, Wine and Windows evidence
belongs to their separate acceptance records, indexed by
[the current host contract](portable-c-host-plan.md).

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
| M2 C8/JR16 and Fastboot V16 | frozen readiness, framing, CRC and recovery expectations | complete C8 boot to CP/M, missed-ready recovery and reset-mid-stream restart | pass |
| N3 A:/B: and N4 | frozen raw/compact/read-ahead/write, duplicate and console fixtures | PTY and C8 sessions cover native B:, writes, duplicate replay, capabilities and bidirectional N4 | pass |
| Host loss and replacement | frozen reconnect and resume outcomes | named-PTY reopen, live host replacement, target reset and resumed requests | pass |
| Writable-media safety | frozen mutation and failure cases | portable crash-point matrix plus real POSIX journal rollback and cleanup | pass |
| Logs, capture and exit behavior | M0 observable-result contract | text/file logging, CRC-protected capture replay, required-evidence failures and clean SIGINT during an active reply | pass |
| Normal launchers and acceptance tooling | Python-era inventory frozen at M0 | `juku_run.py`, CP/M Plus physical acceptance, demonstration generator and VC launcher invoke only `jukuhost` | pass |

The comparison is against observable bytes, state transitions, media outcomes,
and recovery behavior. It deliberately does not preserve Python tracebacks,
object layouts, or JSON as a runtime dependency.

## Subsequent stock-ROM compatibility

Version `0.3.0-m6` added the exact JF15 stock-assisted path to the same C
executable. A retained 2026-08-22 CS00000/EK37 run qualified that native C
path through `A>` and 22 NetDisk requests with zero retries or UART errors;
see [the service record](cs00000-service-record.md) for artifact identities
and capture evidence. The five-second core-delay regression remains in
`tests/jukuhost_v15_delayed_pty_test.py`.

JF1–JF14 stages are not admitted production inputs. Current recoverable stock
sessions use JF17; see [stock bootstrap and recovery](janet-fastboot.md).

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

## Related-repository boundary

The M2 retirement moved the CP/M Plus physical runner and VC interactive
launcher to the C executable, while retaining Python-era fixtures for tests.
CP/Mish historical simulator imports likewise use frozen fixtures.
The accepted source checkpoints are `cpm-plus-juku` `e186603`, `cpmish`
`33575ef` and `vc8080` `09c381b`. Their later branch, publication and CI state
are not established by this historical acceptance record.

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

## Acceptance scope

M2 closes the Linux production-host parity and Python-host-retirement gate
for the identities above. M2.1 separately qualifies the named executable on
CS00015. DOS desk/emulator qualification is recorded in
[the M2.2 report](portable-c-host-m2.2-dos-acceptance.md); physical DOS
qualification remains open independently of Windows development. Windows
build, Wine and Windows 95 guest results are already implemented and recorded
in their platform guides, with physical serial qualification still separate.
These later results do not retroactively widen the exact M2 hardware claim.
