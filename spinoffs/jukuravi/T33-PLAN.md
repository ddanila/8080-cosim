# CS00015 CPU increment-fault probe

Status: **D1 FAULT CONFIRMED; REPAIR VERIFIED**

The tests used T32 version `1Bh`, CRC16 `D62B`, SHA-256
`61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2`.
The recorded setup used its loader API v2 through X3 at 2400 baud. T32 is
no longer fitted in CS00015; see the
[current service record](../../docs/cs00015-service-record.md). Reproduction
requires a compatible diagnostic-loader setup, Python 3 on a POSIX host
(the serial helper uses `termios`/`fcntl`), and NASM to build the probe.
Run the command below from the repository root.

The [T32 physical record](T32-PHYSICAL.md) retains the memory/instruction
controls, ROM WAIT-class comparisons and before/after D1 replacement evidence.
The unchanged direct-register probe confirmed the repair; no additional ROM
burn or D4/D30 rework is required for this diagnosed fault.

## Reproducing the register-increment probe

This probe copies register results to low-A12 RAM without making any
high-address memory access. Its predicted low aliases cannot be explained by
D4, D15, or external BA12 loading.

```sh
python3 spinoffs/jukuravi/probe_a12_increment.py --port /dev/ttyUSB0
```

Expected clean/fault words are stored little-endian:

| Operation | Correct | D1 increment-fault prediction |
| --- | --- | --- |
| `INX B`, `0FFFh` | `1000h` | `1000h` |
| `INX D`, `1A00h` | `1A01h` | `0A01h` |
| `INX H`, `5A00h` | `5A01h` | `4A01h` |
| `INX SP`, `9A00h` | `9A01h` | `8A01h` |
| `DAD D`, `1A00h + 1` | `1A01h` | `1A01h` in the fitted model |

The cosim integration regression checks the probe outputs against clean/fault
expectations in
`tests/jukuravi_cpu_a12_increment_test.py`.
Start the helper before RESET for a fresh T32 boot; it checks `1B/D62B`.
`--attach-loader` uses an already-resident API-v2 loader without checking that
cold-boot identity. The helper exits 0 for either recognized `CLEAN` or
`D1 FAULT CONFIRMED` output, and 2 for an unrecognized well-formed result.
Transport and malformed-result failures return other nonzero codes. Exit 0
alone does not mean the CPU passed.
