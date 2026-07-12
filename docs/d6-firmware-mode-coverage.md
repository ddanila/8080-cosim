# D6 firmware mode coverage

Status: **PHYSICAL MODES 000/001 OBSERVED / 010-111 UNEXERCISED**

This generated report traces authentic ROMBIOS Port-C writes and separates
the physical D6 inputs `PC4..PC2` from the historical emulator's unrelated
two-bit banking convention `PC1..PC0`.

## Reproduction

```sh
python3 scripts/report_d6_firmware_modes.py
```

The generator builds the C trace harness, runs `ekta37` through 32,000 video
writes with `JUKU_TRACE_IO=1`, and replays every PPI0 port `06/07` update.

## Early ROM trace

- Port-C events: `24`
- Physical D6 modes observed (`PC4..PC2`): `000`
- Legacy emulator modes observed (`PC1..PC0`): `00, 01`

| Cycle | PC | VRAM writes | Port/value | Port C before -> after | Physical D6 | Legacy view |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 123 | `01A8` | 0 | `0x07=0x82` | `0x00->0x00` | `000` | `00` |
| 140 | `01AC` | 0 | `0x07=0x0F` | `0x00->0x80` | `000` | `00` |
| 1970003 | `026D` | 30160 | `0x07=0x0E` | `0x80->0x00` | `000` | `00` |
| 3038115 | `0299` | 30200 | `0x07=0x0E` | `0x00->0x00` | `000` | `00` |
| 3064197 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3064555 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3064788 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3064961 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `000` | `01` |
| 3065377 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3065949 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3066209 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3066428 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3066601 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `000` | `01` |
| 3066951 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3067985 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3068245 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3068464 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3068637 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `000` | `01` |
| 3069053 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3069625 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3069885 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |
| 3070104 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `000` | `01` |
| 3070277 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `000` | `01` |
| 3070627 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `000` | `00` |

ROMBIOS toggles `0x00/0x01` sixteen times around its high-ROM transition.
Those writes change PC0 and the emulator view, but they do not change any
physical D6 address input. The structural `juku_top` therefore remains in
physical mode `000` throughout this trace and still boots byte-identically.

## Later FDC/EKDOS evidence

The guarded long-run/checkpoint reports below all finish with Port C `0x04`,
which sets PC2 and therefore exercises physical D6 mode `001`:

| Evidence | Port C | Physical D6 mode |
| --- | ---: | --- |
| `docs/juku-top-fdc-alignment.md` | `0x04` | `001` |
| `docs/juku-top-fdc-verilator-probe.md` | `0x04` | `001` |
| `docs/juku-top-jbasic-verilator-probe.md` | `0x04` | `001` |

## Coverage boundary

- Physical modes `000` and `001` have firmware execution evidence.
- Modes `010` through `111` are truth-table guarded but not observed in the
  current ROM/EKDOS/BASIC paths. Their functions must not be assigned from
  the legacy emulator's `PC1..PC0` mode numbers.
- This trace guards firmware writes, not the unresolved downstream meaning of
  every D6 output word; see `docs/d6-physical-decode.md`.
