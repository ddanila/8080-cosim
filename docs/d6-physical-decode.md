# Physical D6 `.038` decode

Status: **PHYSICAL TABLE CLASSIFIED AND GUARDED**

This generated report translates the preserved КР556РТ4 D6 image into
address ranges without assigning semantics that the `.009` continuity does
not support. Run `python3 scripts/report_d6_physical_decode.py` to refresh it.

## Guarded artifact

- Raw image: `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes)
- SHA256: `05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`
- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, PC2, PC3, PC4`
- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9

## Output words

| Raw word | Rows | D3 D2 D1 D0 | Joined D1/D0 conductor |
| ---: | ---: | --- | --- |
| `1` | 18 | `0001` | `0` |
| `8` | 94 | `1000` | `0` |
| `D` | 16 | `1101` | `0` |
| `F` | 128 | `1111` | `1` |

D6 pins 11 and 12 are open-collector outputs joined by direct owner
continuity on the `.009` board. Their electrical wired-low result is `0`
for words `1`, `8`, and `D`, and `1` only for word `F`. Consequently the
older-sheet names `RAM_N` and `ROM_N` must not be interpreted as independent
`.009` nets even though they remain useful physical pin-role labels.

## Mode maps

Each address interval is inclusive. The 32-character signature is one raw
nibble per 2 KiB block from `0000` through `F800`.

| PC4 PC3 PC2 | 2 KiB signature | Inclusive address ranges |
| --- | --- | --- |
| `000` | `88888888888888888888888888888888` | `0000-FFFF` -> `8` |
| `001` | `88888888FFFFFFFFFFFFFFFF88811111` | `0000-3FFF` -> `8`; `4000-BFFF` -> `F`; `C000-D7FF` -> `8`; `D800-FFFF` -> `1` |
| `010` | `88888888888888888888888888811111` | `0000-D7FF` -> `8`; `D800-FFFF` -> `1` |
| `011` | `11111111888888888888888888888888` | `0000-3FFF` -> `1`; `4000-FFFF` -> `8` |
| `100` | `DDDDFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `D`; `2000-FFFF` -> `F` |
| `101` | `DDDDFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `D`; `2000-FFFF` -> `F` |
| `110` | `DDDDFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `D`; `2000-FFFF` -> `F` |
| `111` | `DDDDFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `D`; `2000-FFFF` -> `F` |

## Direct observations

- With `PC4=1`, PC2 and PC3 are don't-cares: `0000-1FFF` emits `D` and
  `2000-FFFF` emits `F`.
- With `PC4=0`, all four PC3/PC2 combinations are distinct. Mode `001`
  contains word `8` at `0000-3FFF` and `C000-D7FF`, word `F` in the
  middle, and word `1` at `D800-FFFF`; mode `010` extends word `8` through `D7FF`.
  Firmware coverage is reported separately; do not equate these physical
  mode numbers with the emulator's PC1/PC0 banking convention.
- D3/pin9 is low only in word `1`; D2/pin10 is high in words `D/F`; the
  joined D1/D0 conductor is high only in word `F`.
- These are physical electrical facts, not yet a complete explanation of
  the downstream D8/D13/D92 memory timing. That behavior must be derived
  from the joined conductor and its consumers rather than resurrecting
  separate RAM/ROM selects as physical claims.
- Runnable simulation therefore uses a separately named, non-LVS
  `decode_prom_functional` oracle for the established EKTA/EKDOS memory
  map. The physical table and joined conductor remain instantiated and
  guarded; the compatibility path must be retired when downstream timing
  continuity is sufficient to execute directly from the physical topology.
- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a
  full boot. At `B37A`, all eight PC4..PC2 combinations emit word `8` or
  `F`; D6.9 is therefore high in every physical row, and disabling the PROM
  also leaves it high. Mode selection and V1/V2 cannot repair the currently
  modeled D13/D37 chain's inactive D58 output. The isolated `.009` endpoint,
  polarity/function, and D58-path checks named there must resolve the boundary.
- At checkpoint mode `000`, D6 emits the same word `8` at PC `0484` and
  RAM target `B37A`; no D6 output bit can distinguish those reads. D8's
  pager output changes from `EF` (D15 selected) to `FF` (all sockets released),
  but its modeled output nets only reach the eight socket CEs. An authentic
  address-sensitive RAM qualifier remains missing rather than inferred.

## Model adoption guards

| Check | Result |
| --- | --- |
| Board source joins D6.11/D6.12 to D13.12 and D8.15 | PASS |
| HDL drives both D6 outputs onto the joined conductor | PASS |
| HDL uses physical D6 address order | PASS |
| Runnable compatibility decode is explicit and excluded from LVS | PASS |
| Structural consumers retain the measured joined D6 conductor | PASS |
| All-mode B37A RAM-gate boundary has a reproducible diagnostic | PASS |
| Mode-000 D6 indistinguishability and D8 pager distinction are reproduced | PASS |
