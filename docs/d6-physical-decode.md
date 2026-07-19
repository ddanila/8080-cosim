# Physical D6 `.038` decode

Status: **PHYSICAL TABLE CLASSIFIED AND GUARDED**

This generated report translates the preserved КР556РТ4 D6 image into
address ranges without assigning semantics that the `.009` continuity does
not support. Run `python3 scripts/report_d6_physical_decode.py` to refresh it.

## Guarded artifact

- Raw image: `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes)
- SHA256: `05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`
- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, ~PC0, ~PC1, D6.15/D105.1 boundary`
- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9

The factory programming instruction in `ref/baltijets-tech-docs/007 ROM and ROM programming.pdf`
page 16 identifies D6 `.038` as a КР556РТ4 and says its programming table
was supplied on disk. A pin-order audit retained the reader's D0/pin12 through
D3/pin9 packing: reversing the nibble would contradict the device pin assignment
and is not a permissible way to make the downstream RAM path run.

## Output words

| Raw word | Rows | D3 D2 D1 D0 | RAM_N D1 | ROM_N D0 |
| ---: | ---: | --- | ---: | ---: |
| `1` | 18 | `0001` | `0` | `1` |
| `8` | 94 | `1000` | `0` | `0` |
| `D` | 16 | `1101` | `0` | `1` |
| `F` | 128 | `1111` | `1` | `1` |

Chip-removed owner continuity proves D6 output pins 11 and 12 are
separate. D6.12 reaches D8.15, while D6.11 reaches D2.15/-WREQ and
does not reach D8.15; the earlier installed-PROM
zero-ohm reading that joined D6.11/D6.12/D13.12 is explicitly invalidated.

## Recovered `.009` sheet-1 polarity read

Two independent read passes over the native-color detail and an enhanced
high-resolution crop, cross-checked against the sheet overview, close the
critical schematic question. The guarded source frames are:

- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101754468.jpg` (SHA256 `effc98746807ef28dab97051ceba293f4433c0f3b39b86cbb55ddcaad24aeca4`)
- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101805510.jpg` (SHA256 `40a524d663dc4685a7093782165264524cd70780fb41638a8d1c0cbca0b36216`; upper-center D6/D8/D9 region)

The drawing labels D6 D0/pin 12 `ROM` and carries that conductor
uninterrupted through the R11 1 kOhm pull-up node to D8 `E`/pin 15. It
labels D6 D3/pin 9 `ROE`; that conductor passes the R14 1 kOhm pull-up
node and enters D13 pin 1 directly. D13 is the only inverter symbol on
this path, and D13 pin 2 is the drawn `RAMOUTEN` output. No additional
series inverter, off-sheet inversion, or alternate consumer is drawn on
either D6 output path.

This reviewed factory-drawing result agrees with the stronger chip-removed
D6.12-to-D8.15 and D6.9-to-D13.1 continuity measurements and with the
modeled D13 polarity. It therefore rules out an omitted *drawn* inverter
as the cause of the raw-table contradiction; it does not resolve the
electrical/provenance mismatch in the existing D6 dump. The corrected-reader
re-read or operating-level comparison remains decisive.

## Mode maps

Each address interval is inclusive. The 32-character signature is one raw
nibble per 2 KiB block from `0000` through `F800`.

| D6 A7 A6 A5 | 2 KiB signature | Inclusive address ranges |
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

- With raw `A7=1`, A5 and A6 are don't-cares: `0000-1FFF` emits `D` and
  `2000-FFFF` emits `F`.
- With raw `A7=0`, all four A6/A5 combinations are distinct. Mode `001`
  contains word `8` at `0000-3FFF` and `C000-D7FF`, word `F` in the
  middle, and word `1` at `D800-FFFF`; mode `010` extends word `8` through `D7FF`.
  Direct `.009` continuity now proves A6=`~PC1` and A5=`~PC0`; A7 joins
  D105.1 but its driver or pull source is still unresolved. The raw mode
  numbers remain useful table coordinates, not a claim about A7 semantics.
- D3/pin9 is low only in word `1`; D2/pin10 is high in words `D/F`.
- These are physical electrical facts, not yet a complete explanation of
  the downstream D8/D13/D92 memory timing. That behavior must be derived
  from the now-separate ROM/RAM conductors and their confirmed consumers.
- Runnable simulation now executes its memory map from THIS physical table
  (the `decode_prom` instance), not the former `decode_prom_functional`
  oracle, which is retired from the boot path. A provisional per-output
  polarity correction is applied to the two РТ4 outputs feeding D8 and D13
  (`rom_sel_n = ~D0`, `roe_n = ~D3`; D1/-WREQ and D2/rev used direct); it
  boots byte-identical to cosim but is a FUNCTIONAL FIT pending a reset-fetch
  level probe, since the reader/dump are faithful and `D6.12->D8.15` is
  recorded direct. The raw dump is preserved untouched; see PLAN item 1.
- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a
  full boot. At `B37A`, all eight raw A7..A5 combinations emit word `8` or
  `F`; D6.9 is therefore high in every physical row, and disabling the PROM
  also leaves it high. Mode selection and V1/V2 cannot repair the currently
  modeled D13/D37 chain's inactive D58 output. The isolated `.009` endpoint,
  polarity/function, and D58-path checks named there must resolve the boundary.
- Raw row `000` emits word `8` at both PC `0484` and RAM target `B37A`,
  but measured firmware suffix `11` and unresolved A7 prevent identifying
  that raw row as the checkpoint state.

## Model adoption guards

| Check | Result |
| --- | --- |
| Chip-removed ROM select is D6.12 to D8.15 | PASS |
| D6.11 reaches D2.15/-WREQ and stays separate from ROM select | PASS |
| D6.11 conductor also reaches D92.5/R12.2 | PASS |
| D13.12 drives the D6 enable conductor, not either output | PASS |
| HDL keeps the D6 outputs separate | PASS |
| HDL models D6 raw outputs as open collector with physical pull-up recovery | PASS |
| HDL uses measured physical D6 address order | PASS |
| RT4 reader packs D0/pin12 through D3/pin9 into raw bits 0 through 3 | PASS |
| RT4 reader revision 2 avoids Nano D13 and verifies released pull-ups | PASS |
| RT4 host validation guards revision-2 metadata and classifies the D6 re-read | PASS |
| Device commentary preserves measured mode pins and separate output conductors | PASS |
| Runnable twin executes from the physical D6 table (oracle retired from boot path) | PASS |
| Structural consumers retain separate ROM/RAM conductors | PASS |
| All-row B37A RAM-gate boundary has a reproducible diagnostic | PASS |
| Raw-row regression and corrected checkpoint suffix are documented | PASS |
| Recovered .009 sheet-1 D6 polarity evidence is checksum-guarded | PASS |
