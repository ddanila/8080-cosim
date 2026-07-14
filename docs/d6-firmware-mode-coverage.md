# D6 firmware mode coverage

Status: **A6/A5 SUFFIXES 11/10 OBSERVED / A7 SOURCE UNRESOLVED**

This generated report traces authentic ROMBIOS Port-C writes and separates
the measured physical D6 inputs A6=`/PC1`, A5=`/PC0` from the historical
emulator's non-inverted `PC1..PC0` banking convention. D6 A7 joins D105.1,
but its driver or pull source remains unresolved.

## Reproduction

```sh
python3 scripts/report_d6_firmware_modes.py
```

The generator builds the C trace harness, runs `ekta37` through 32,000 video
writes with `JUKU_TRACE_IO=1`, and replays every PPI0 port `06/07` update.

## Early ROM trace

- Port-C events: `24`
- Physical D6 A6/A5 suffixes observed (`/PC1,/PC0`): `10, 11`
- Legacy emulator modes observed (`PC1..PC0`): `00, 01`

| Cycle | PC | VRAM writes | Port/value | Port C before -> after | D6 A6/A5 | Legacy view |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 123 | `01A8` | 0 | `0x07=0x82` | `0x00->0x00` | `011` | `00` |
| 140 | `01AC` | 0 | `0x07=0x0F` | `0x00->0x80` | `011` | `00` |
| 1970003 | `026D` | 30160 | `0x07=0x0E` | `0x80->0x00` | `011` | `00` |
| 3038115 | `0299` | 30200 | `0x07=0x0E` | `0x00->0x00` | `011` | `00` |
| 3064197 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3064555 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3064788 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3064961 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `010` | `01` |
| 3065377 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3065949 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3066209 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3066428 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3066601 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `010` | `01` |
| 3066951 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3067985 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3068245 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3068464 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3068637 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `010` | `01` |
| 3069053 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3069625 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3069885 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |
| 3070104 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `010` | `01` |
| 3070277 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `010` | `01` |
| 3070627 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `011` | `00` |

ROMBIOS toggles `0x00/0x01` sixteen times around its high-ROM transition.
Those writes change PC0 and therefore toggle physical D6 A5 after the D3
inverter. The structural table row is `?11` or `?10`; A7 cannot be inferred
from Port C and remains a measured continuity boundary.

## Later FDC/EKDOS evidence

The guarded long-run/checkpoint reports below all finish with Port C `0x04`,
which sets PC2 but leaves PC1/PC0 clear. It therefore retains A6/A5=`11`:

| Evidence | Port C | D6 A6/A5 |
| --- | ---: | --- |
| `docs/juku-top-fdc-alignment.md` | `0x04` | `11` |
| `docs/juku-top-fdc-verilator-probe.md` | `0x04` | `11` |
| `docs/juku-top-jbasic-verilator-probe.md` | `0x04` | `11` |

## Coverage boundary

- Physical A6/A5 suffixes `11` and `10` have firmware execution evidence.
- A7 is not a Port-C bit on the measured board. Until its source is traced,
  firmware writes cannot identify complete three-bit D6 table rows.
- This trace guards firmware writes, not the unresolved downstream meaning of
  every D6 output word; see `docs/d6-physical-decode.md`.
