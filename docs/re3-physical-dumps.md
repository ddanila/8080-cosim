# D8/D94 physical RE3 dumps

Status date: 2026-07-13

Status: **CROSS-MACHINE PHYSICAL CONTENT VALIDATED**

The D8 `.039` and D94 `.092` КР556РЕ3 PROMs were read independently from
two physical Juku processor boards:

- Danila Sukharev's reference board; and
- Arvutimuuseum machine `CS00015`.

Three captures were retained for every PROM on every board. The third capture
followed a power cycle. All six captures of each location are byte-identical.
They are independent physical reads, not duplicate aliases.

The Sukharev board has missing capacitors and an unrelated decapped logic IC,
probably an ЛЕ4. Its D8 and D94 PROM packages are intact.

## Reader and representation

`tools/re3_dumper/re3_dumper.ino` reads the 32 x 8 PROM with this wiring:

| РЕ3 signal | Package pin | Arduino Nano |
| --- | ---: | --- |
| A0..A4 | 10..14 | D2..D6 |
| `/E` | 15 | D7 |
| D0..D6 | 1..7 | D8..D13, A0 |
| D7 | 9 | A1 |
| GND | 8 | GND |
| +5 V | 16 | +5 V |

Each data output has a 3 kΩ pull-up to +5 V. A 100 nF bypass capacitor is
connected from pins 16 to 8. The reader's raw bytes describe electrical pin
levels; the asserted images are their bitwise complement because the PROM
outputs are active-low. `scripts/validate_re3_dump.py` checks repeated reads
and generates both forms without discarding the raw evidence.

## D8 `.039`

- raw SHA256: `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`
- asserted SHA256: `e0f5231c7b24764d729d8d9c397d78a5bf68b899911bd8946be57cd905e72617`

Asserted contents:

```text
00: 10 10 10 10 20 20 20 20 00 00 00 00 00 00 00 00
10: 00 00 00 00 00 00 00 00 10 10 10 10 20 20 20 20
```

This differs at 19 of 32 addresses from the former reconstructed fallback.
The validated physical image therefore supersedes that fallback as content
truth. HDL now preserves the reader-proved open-collector behavior: raw zero
sinks a socket-select rail, while raw one or disabled output releases it.
`docs/d8-physical-decode.md` exhaustively reduces the table to the exact D15/D16
select equations and proves the other six outputs are invariant released.

## D94 `.092`

- raw SHA256: `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`
- asserted SHA256: `6e45374f1eadd171637e4d47aa1540bd549173eb49d30260e985120f7f001095`

Asserted contents:

```text
00: 00 00 00 01 0A 0A 0A 03 06 06 06 03 00 00 00 01
10: 00 00 00 00 0A 0A 0A 0A 06 06 06 06 00 00 00 00
```

D94 differs from D8 at 25 of 32 addresses, confirming that the two locations
carry distinct programs. The dump closes D94 content truth only: the board
source of pin 15 and the far destinations or branches of outputs D3..D7 remain
continuity boundaries.

The retained serial transcripts, canonical binaries, hexadecimal views,
validation manifests, and checksums are under `ref/physical-proms/`.
