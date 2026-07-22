# Physical D6 `.038` decode

Status: **PHYSICAL TABLE CLASSIFIED AND GUARDED**

This generated report translates the preserved КР556РТ4 D6 image into
address ranges without assigning semantics that the `.009` continuity does
not support. Run `python3 scripts/report_d6_physical_decode.py` to refresh it.

## Guarded artifact

- Raw image: `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes)
- SHA256: `c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489`
- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, ~PC0, ~PC1, D7.8 IO_CYCLE_H`
- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9

The factory programming instruction in `ref/baltijets-tech-docs/007 ROM and ROM programming.pdf`
page 16 identifies D6 `.038` as a КР556РТ4 and says its programming table
was supplied on disk. The 2026-07-19 reader-3 control first reproduced D2
byte-for-byte, then three D6 reads including a power cycle exposed the old
capture as an exact nibble bit reversal. Direct continuity confirms reader-3
D0/pin12 through D3/pin9 packing.

## Output words

| Raw word | Rows | D3 D2 D1 D0 | RAM_N D1 | ROM_N D0 |
| ---: | ---: | --- | ---: | ---: |
| `1` | 94 | `0001` | `0` | `1` |
| `8` | 18 | `1000` | `0` | `0` |
| `B` | 16 | `1011` | `1` | `1` |
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
as the cause of the former raw-table contradiction. The corrected reader
instead proved that the original capture labels reversed all four channels.

## Mode maps

Each address interval is inclusive. The 32-character signature is one raw
nibble per 2 KiB block from `0000` through `F800`.

| D6 A7 A6 A5 | 2 KiB signature | Inclusive address ranges |
| --- | --- | --- |
| `000` | `11111111111111111111111111111111` | `0000-FFFF` -> `1` |
| `001` | `11111111FFFFFFFFFFFFFFFF11188888` | `0000-3FFF` -> `1`; `4000-BFFF` -> `F`; `C000-D7FF` -> `1`; `D800-FFFF` -> `8` |
| `010` | `11111111111111111111111111188888` | `0000-D7FF` -> `1`; `D800-FFFF` -> `8` |
| `011` | `88888888111111111111111111111111` | `0000-3FFF` -> `8`; `4000-FFFF` -> `1` |
| `100` | `BBBBFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `B`; `2000-FFFF` -> `F` |
| `101` | `BBBBFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `B`; `2000-FFFF` -> `F` |
| `110` | `BBBBFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `B`; `2000-FFFF` -> `F` |
| `111` | `BBBBFFFFFFFFFFFFFFFFFFFFFFFFFFFF` | `0000-1FFF` -> `B`; `2000-FFFF` -> `F` |

## Direct observations

- With raw `A7=1`, A5 and A6 are don't-cares: `0000-1FFF` emits `B` and
  `2000-FFFF` emits `F`.
- With raw `A7=0`, all four A6/A5 combinations are distinct. Mode `001`
  contains word `1` at `0000-3FFF` and `C000-D7FF`, word `F` in the
  middle, and word `8` at `D800-FFFF`; mode `010` extends word `1` through `D7FF`.
  Direct continuity proves A6=`~PC1`, A5=`~PC0`, and A7 is the
  D7.8-to-D105.1 `IO_CYCLE_H` qualifier. The raw mode
  numbers remain useful table coordinates, not a claim about A7 semantics.
- D3/pin9 is low only in word `1`; D2/pin10 is high in words `B/F`.
- These are physical electrical facts, not yet a complete explanation of
  the downstream D8/D13/D92 memory timing. That behavior must be derived
  from the now-separate ROM/RAM conductors and their confirmed consumers.
- Runnable simulation now executes its memory map from THIS physical table
  (the `decode_prom` instance), not the former `decode_prom_functional`
  oracle, which is retired from the boot path. All four physical outputs
  now execute directly with no per-output transform and pass the 6,000-write
  byte-identical boot guard.
- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a
  full boot. The corrected table emits word `1` at both low-ROM `0484` and
  RAM target `B37A` for raw row `000`, aligning the direct ROM and ROE paths
  with the runnable behavior without inventing an inverter.
- Raw row `000` emits word `1` at both PC `0484` and RAM target `B37A`,
  but the firmware suffix `11` identifies a different checkpoint row.

## Model adoption guards

| Check | Result |
| --- | --- |
| Chip-removed ROM select is D6.12 to D8.15 | PASS |
| D6.11 reaches D2.15/-WREQ and stays separate from ROM select | PASS |
| D6.11 conductor also reaches D92.5/R12.2 | PASS |
| D13.12 drives the D6 enable conductor, not either output | PASS |
| D7.8 drives D105.1 and D6 A7 as IO_CYCLE_H | PASS |
| D6 package provenance names the adopted table and current A7 net | PASS |
| HDL keeps the D6 outputs separate | PASS |
| HDL models D6 raw outputs as open collector with physical pull-up recovery | PASS |
| HDL uses measured physical D6 address order | PASS |
| RT4 reader packs D0/pin12 through D3/pin9 into raw bits 0 through 3 | PASS |
| RT4 reader revision 3 has continuity-confirmed channel order and verifies both enables | PASS |
| RT4 host validation guards revision-3 metadata and the old bit reversal | PASS |
| Device commentary preserves measured mode pins and separate output conductors | PASS |
| Runnable twin executes corrected physical D6 outputs directly | PASS |
| Structural consumers retain separate ROM/RAM conductors | PASS |
| Corrected mode path has a reproducible diagnostic | PASS |
| Raw-row regression and corrected checkpoint suffix are documented | PASS |
| Recovered .009 sheet-1 D6 polarity evidence is checksum-guarded | PASS |
