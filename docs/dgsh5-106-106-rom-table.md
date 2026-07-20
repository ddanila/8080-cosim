# `ДГШ5.106.106 Д1` ROM-table reconstruction

Status: **FACTORY 2 KiB IMAGE RECONSTRUCTED / ONE ARCHIVE TYPO CORRECTED**

The three photographed factory sheets cover `0000-07FF`. An existing
archive transcription, `ref/firmware/BAS0.HEX`, supplies all 2,048
candidate bytes. The independent `roms/jbasic11.bin` cartridge image
agrees at 2,047 positions. The only difference is resolved directly from
the photographed factory row, producing a byte-exact 2 KiB image.

## Reproduce

```sh
python3 scripts/reconstruct_dgsh5_106_106.py
```

## Output

- Binary: `ref/reconstructed-firmware/dgsh5-106-106-d1.bin` (2048 bytes)
- Readable hex: `ref/reconstructed-firmware/dgsh5-106-106-d1.hex`
- Manifest: `ref/reconstructed-firmware/SHA256SUMS`
- SHA256: `2cd7398b167ceebc256614b9de4cd8953b858e4f35722e57723559d990fc80a6`
- Reset vector: `C3 07 01` = 8080 `JMP 0107h`

The result equals `roms/jbasic11.bin[0000:0800]` exactly. This identifies
the printed `.106.106` program as the first 2 KiB page of the preserved
Juku BASIC 1.1 cartridge image; it is not one of the main-board D15/D16
EktaSoft BIOS halves or a small D2/D6/D8/D94 PROM table.

## Single divergence adjudication

| Address | `BAS0.HEX` | `jbasic11.bin` | Factory photograph | Adopted |
| ---: | ---: | ---: | ---: | ---: |
| `021A` | `A1` | `21` | `21` | `21` |

Factory sheet 1 (`sheet1_PXL_20260718_122548761.jpg`), row `0210`,
column A visibly reads `21`. Its complete adopted row is:

```text
0210: E3 CD 7A 18 E1 2B CD 59 01 CA 21 02 FE 2C C2 82
```

This is exactly the plan's diff-first method: matching bytes need no
second manual transcription; the sole disagreement is hand-verified
against primary evidence. The source hashes and exact one-byte mismatch
are executable guards, so a changed archive cannot silently pass.

## Guarded sources

- `ref/firmware/BAS0.HEX` — SHA256 `fc8514a64e9524738936e65dffd48f90d17762576a743a1fb84f1dbe65b9a34e`
- `roms/jbasic11.bin` — SHA256 `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60`
- `ref/photos/dgsh5-106-106-d1/sheet1_PXL_20260718_122548761.jpg` — SHA256 `a20fc8d7ce66e4ab8814a75a8951893ec8989c0a58905eed8e12dff910c97f33`
- `ref/photos/dgsh5-106-106-d1/sheet2_PXL_20260718_122557171.jpg` — SHA256 `3c27e3f5af18d9db36bfc6725f679ec8cfe09ebbc3b28e9173d2712bf48b5453`
- `ref/photos/dgsh5-106-106-d1/sheet3_PXL_20260718_122601894.jpg` — SHA256 `b966e2039bac3646aa2c8242276d657381430256f3dc8c915935d75038e5f76b`

## Provenance boundary

The factory listing is authoritative printed programming data, while the
generated binary is a reconstruction rather than a physical-device read.
A repeatable read of a device marked `.106.106` would be independent
corroboration; any stable disagreement must be preserved as a variant.
