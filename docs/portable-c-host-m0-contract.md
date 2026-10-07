# Frozen Python-era host baseline (M0)

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
oracle. `tests/jukuhost_contract_test.py` checks selected wire and checksum vectors
against the non-runnable archived Python implementation. C tests consume the same fixture
directly; it remains the wire baseline after Python host retirement.

## Production contract

Current protocol support, artifact admission, recovery policy and platform
acceptance are maintained in the [portable C host contract](portable-c-host-plan.md)
and [stock recovery guide](janet-fastboot.md). The frozen vectors below
preserve the selected Python compatibility baseline; they do not define the
complete current feature or acceptance matrix.

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
Current runner exit codes are maintained in the
[production contract](portable-c-host-plan.md#runner-exit-codes).

## Baseline verification

Run from the repository root with Python 3, Bash, a C compiler and
materialized archived-system assets:

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
