# Portable C host M0 contract

Status: **FROZEN PYTHON-ERA BASELINE**

This document closes M0 of the
[portable C host plan](portable-c-host-plan.md). It identifies the last Python
production-host baseline and the behavior that the C host must reproduce before
the Python server is removed.

## Baseline identity

The baseline is the repository state containing this document. Its production
modules and direct regression tests are pinned below so later changes cannot
silently redefine parity:

| File | SHA-256 |
| --- | --- |
| `tools/janet_netboot.py` | `17b362c09f2af548a81a9f86b855c4a3ab9803406f7dcc91810c6151b921f20f` |
| `tools/janet_fastboot.py` | `8a23c014fc969367f47833e9235354af41b75165a884bffbf558e8ece432f538` |
| `tools/janet_disk_server.py` | `05e637db7d33dbda9c2177055809a5f190248d7f9b71fce34374aa3be8887236` |
| `tests/janet_netboot_test.py` | `4e2847ec3e7a05661576bba64fa2720d30451814cd4db82aace62aca9fd3ea07` |
| `tests/janet_fastboot_protocol_test.py` | `1f7f4a524bb2d069b52895961f13be0a7643523d3ba28f84a7caed69561b10e4` |
| `tests/janet_disk_server_test.py` | `3b1a7ff1dc1c8b9523bee9d2b9bf39a7d214f15d27bfaae088355527397cc7e2` |

The five archived stock-system inputs remain byte-identical:

| System | SHA-256 |
| --- | --- |
| `CPM22.BIN` | `b9665d9af00f66bf51a5deda02fad3149b8fd3820c020e252d49f607362fee79` |
| `CPM231E.BIN` | `230aa5952cd62596ac8a71bfd5addbb840a51ec51987d882fda958d2f9817939` |
| `EKDOS229.BIN` | `496473a0461e2c09546d0587fc83292e78e9e57e5ef19e1565ac3a602dc3677e` |
| `EKDOS230.BIN` | `819d0ab7a30fbb8e87ebe42eddc2da599816f21b131f96bab2bd8f7cdc4f96d8` |
| `EKDOSVSW.BIN` | `8c70eda07c2cde8e73a0e664d7ff51356b4559649fad6df24f45784f3076e994` |

The module paths and hashes above identify the immutable M0 repository state.
At M2 their implementations moved to `tests/fixtures/legacy_janet_*.py` and
lost all runnable entry points. They remain PTY regression/diagnostic fixtures;
the original `tools/janet_*.py` production commands no longer exist.

`tests/fixtures/jukuhost/python-era-v1.txt` is the compact, standalone wire
oracle. `tests/jukuhost_contract_test.py` proves that it still agrees with the
pinned Python implementation while that implementation exists. The C tests
will consume the same fixture directly. After retirement, the fixture—not a
runnable Python server—is authoritative.

## Required production parity

The C host must reproduce all behavior used by the accepted operational path:

- stock Janet discovery at 9,600 baud, including learned client/server station
  identities, rejected frames, bounded retries, and all five archived system
  images;
- plain 0100h executables, JUKUSYS resident images, and the self-describing
  `JUKURM1` RAM-system container;
- C8/JR16 direct readiness and Fastboot V16 at 19,200 baud, including the
  missed-ready probe path, metadata and CRC validation, compressed streaming,
  acknowledgement handling, and the accepted no-resend timing policy;
- the exact JF15 stock-assisted compatibility path: one 128-byte Janet record
  at 9,600/8O1, followed by the checked extension and compressed system at
  19,200/8N1;
- N3 raw, compact, read-ahead, legacy write, and V3 write operations, duplicate
  request handling, 80-track A: and native 160-track B: geometry, and B:
  read-only enforcement;
- N4 console polling, single and block output, time get/set, status, diagnostic
  and boot reports, and capability negotiation;
- boot-slot manifests and fallback/recovery policy, writable A: working-copy
  safety, host replacement and reconnect, clean shutdown, human-readable logs,
  counters, and optional raw byte capture.

Fastboot V1 through V14 were valuable hardware experiments and remain valid
historical builders and regression inputs. They are not separate admitted
production protocols for the new runtime. JF15 is the sole legacy-format
exception because it provides the current stock-ROM-assisted CP/M Plus path;
JF16 remains the direct network-ROM path. Both parsers require their exact
magic, layout, length, metadata, and CRCs and fail clearly on every other
legacy bundle.

## Observable result contract

All protocol parsing is incremental and must survive fragmentation, joined
frames, leading noise, bad checksums, target resets, serial EOF, and bounded
timeouts. Invalid target-controlled lengths or disk addresses produce a
defined rejection or error reply and never an out-of-bounds access.

Normal logs record version, requested and applied serial settings, learned
identity, phase changes, artifact identities, retries, reconnects, media
writes, failures, and final counters. Optional capture records preserve exact
TX/RX bytes with monotonic timestamps and remain parseable when the final
record is truncated. Exit meanings are stable: success/clean stop, command or
configuration error, missing or invalid artifact, serial failure, protocol or
timeout failure, and unsafe media state are distinguishable.

M0 does not bless accidental formatting of Python tracebacks, Python object
layout, JSON as a runtime dependency, or arbitrary experimental command-line
flags. The accepted wire bytes, state transitions, recovery outcomes, media
mutations, and useful evidence are the compatibility contract.

## M0 exit evidence

Run:

```sh
python3 tests/jukuhost_contract_test.py
sync/janet_netboot_check.sh
```

The first command proves the immutable compact oracle. The second runs that
oracle plus the existing Fastboot, disk-server, and five-system simulator
regressions. M1 may begin only with both green.
