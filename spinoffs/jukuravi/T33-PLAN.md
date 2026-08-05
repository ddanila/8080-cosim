# Remaining T32 serial probes for CS00015

Status: **COMPLETED 2026-08-05; no re-burn was required**

The already-burned T32 ROM is version `1Bh`, CRC16 `D62B`, SHA-256
`61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2`.
All commands use its loader API v2 through X3 at 2400 baud.

## Established physical signature

Correct absolute-address initialization has already covered:

- LHLD in all four A15:A14 regions: every high-A12 second byte aliases low;
- all four A10:A9 address classes in all-RAM mode: every class aliases;
- POP H: the second stack read aliases;
- SHLD: the second write aliases;
- `0FFF -> 1000` and `2FFF -> 3000`: carry can assert A12 correctly.

The earlier `ram-a12-alias-regions-4000.asm` run is not a valid seeded-memory
matrix because setup used `INX D`. It instead provides the strongest D1 clue:
after INX, the odd byte was stored at the A12-low alias in all four regions,
despite intervening CALL, stack, instruction-fetch, and RET cycles.

## 1. Direct register-increment result — completed

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

CS00015 returned exactly:

```text
1000 0A01 4A01 8A01 1A01
```

The result confirms the fitted D1 fault. BC carry from `0FFFh` asserted A12;
INX on DE, HL, and SP lost an already-high A12; DAD retained A12. The exact
`1B/D62B` boot had zero transport mismatches and returned normally with the
loader still active. Evidence is under
`sessions/t32-ram-a12-increment-registers-physical/`.

The source and clean/fault expectations are guarded by
`tests/jukuravi_cpu_a12_increment_test.py`.
The helper handles a fresh T32 boot by default; pass `--attach-loader` only
when the board is already silent with loader API v2 resident.

## 2. Exact ROM WAIT comparison — completed

The exact ROM-mode pairs close the documentation caveat that all-RAM mode
changes WREQ. `rom-read-pair-4000.asm` was run at `1000`, `1100`, `1200`, and
`1400`.

| Target | Correct | Predicted physical pair |
| --- | --- | --- |
| `1000h` | `00 C0` | `00 0B` |
| `1100h` | `3E 11` | `3E 17` |
| `1200h` | `3E 12` | `3E 02` |
| `1400h` | `3E 14` | `3E E6` |

All sixteen samples in every row returned the predicted alias:

| Target | D2 class | Physical pair |
| --- | --- | --- |
| `1000h` | CAS-gated | `00 0B` |
| `1100h` | CAS-gated | `3E 17` |
| `1200h` | no wait | `3E 02` |
| `1400h` | always wait | `3E E6` |

Evidence is under `sessions/t32-rom-read-pair-{1000,1100,1200,1400}-physical/`.
No reconstructed wait class masks the CPU fault.

## Hardware repair confirmation

Preferred order:

1. substitute a known-good D1 if the socket can be handled safely;
2. rerun `probe_a12_increment.py` and require the clean five-word result;
3. use D1.37/D4.15 capture only if a known-good D1 does not clear it.

No D4/D30 rework and no new diagnostic ROM are justified before D1 is tested.
