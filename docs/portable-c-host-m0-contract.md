# Portable C host M0 contract

Status: **FROZEN PYTHON-ERA BASELINE**

This record pins the Python-era baseline used to verify the C replacement.
The Python production commands have been removed; current behavior and platform
qualification live in the [portable C host contract](portable-c-host-plan.md).
The pinned revision and retained fixtures identify the compatibility baseline.

## Baseline identity

The baseline is commit
[`81f64f76e56c3dd56cffbb4a6a89a4094dafbda6`](https://github.com/ddanila/8080-cosim/commit/81f64f76e56c3dd56cffbb4a6a89a4094dafbda6).
Historical production modules and tests can be recovered from that revision.
The retained implementations at `tests/fixtures/legacy_janet_*.py` serve as
non-runnable PTY regression/diagnostic fixtures. The five archived stock-system
inputs and their identities are maintained in the
[system binary catalog](../media/system/README.md).

`tests/fixtures/jukuhost/python-era-v1.txt` is the compact, standalone wire
oracle. `tests/jukuhost_contract_test.py` proves that it still agrees with the
non-runnable archived Python implementation. C tests consume the same fixture
directly; it remains the wire baseline after Python host retirement.

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

The production C runtime admits JF15 for stock-assisted compatibility,
JF16 for direct network-ROM boot, and JF17 for stock reset recovery.
Fastboot V1–V14 remain historical builders and regression inputs. Stock reset
recovery uses JF17 at 9,600/8O1.
Artifact validation requires exact magic, layout, length, metadata and CRCs.
See the [stock recovery guide](janet-fastboot.md) for current operation.

## Observable result contract

All protocol parsing is incremental and must survive fragmentation, joined
frames, leading noise, bad checksums, target resets, serial EOF, and bounded
timeouts. Invalid target-controlled lengths or disk addresses produce a
defined rejection or error reply and never an out-of-bounds access.

Normal logs record version, requested and applied serial settings, learned
identity, phase changes, artifact identities, retries, reconnects, media
writes, failures, and final counters. Optional capture records preserve exact
TX/RX bytes with monotonic timestamps. Complete records must remain independently
decodable when the final record is truncated. The C decoder reports
`JH_NEED_MORE` for that incomplete record; the current
[JSON converter](portable-c-host-implementation.md#capture-conversion) rejects
the truncated capture rather than exporting its complete prefix.
The current C runner declares these exit codes in
[`jukuhost_runner.h`](../host/include/jukuhost_runner.h):

| Code | Meaning |
| ---: | --- |
| `0` | Success or clean stop |
| `2` | Command/configuration error |
| `3` | Missing or invalid artifact |
| `4` | Serial failure |
| `5` | Protocol or timeout failure |
| `6` | Unsafe media state or media failure |
| `7` | Required log/capture evidence failure |

Inspect the log for the failing operation; a clean stop does not independently
prove target diagnostics or physical acceptance.

M0 does not bless accidental formatting of Python tracebacks, Python object
layout, JSON as a runtime dependency, or arbitrary experimental command-line
flags. The accepted wire bytes, state transitions, recovery outcomes, media
mutations, and useful evidence are the compatibility contract.

## Baseline verification

Run:

```sh
python3 tests/jukuhost_contract_test.py
sync/janet_netboot_check.sh
```

The first command compares selected wire and checksum vectors with the
retained Python fixtures. It does not hash-check the historical files or
prove complete behavioral parity. The second runs that comparison, the C
core gate, and Fastboot, disk-server and archived-system simulator
regressions. The complete current platform and physical acceptance matrix
requires the separate guards in the production contract.
