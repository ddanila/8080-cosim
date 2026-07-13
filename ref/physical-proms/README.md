# Physical PROM captures

These files preserve serial reads made from socketed PROMs on the owner's
`.009` processor board using `tools/rt4_dumper/rt4_dumper.ino` and an Arduino
Nano 3. The reader used 3 kOhm output pull-ups, a 100 nF Vishay MKT bypass
capacitor, Nano USB 5 V, and the pin mapping documented in
`docs/d2-physical-dump-and-continuity.md`.

## D2 `.037`

`captures/d2_037_20260713_capture1.txt`, `capture2.txt`, and
`capture3_powercycled.txt` are complete unchanged serial streams. The third
capture followed a full USB power cycle. `scripts/validate_rt4_dump.py` accepts
all three with no missing, unstable, non-complementary, or repeat-mismatched
rows.

The three `d2_037_arvutimuuseum_CS00015_*` files are byte-identical archival
aliases of those same streams. `d2_037_sukharev_reference_20260713_verify1.txt`
has identical rows and differs from capture 1 only by one trailing blank line.
These files preserve the supplied board/source labels, but are deliberately not
counted as independent captures.

The authoritative raw electrical artifact is `validated/d2_037.raw.bin`:

```text
SHA256 953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b
```

`d2_037.asserted.bin` is the convenient active-low complement and must not
silently replace the raw table.

## D6 `.038`

`captures/d6_038_20260713_capture1.txt`, `capture2.txt`, and
`d6_038_arvutimuuseum_CS00015_20260713_capture3_powercycled.txt` are three
complete matching reads with zero unstable addresses; the third followed a
full power cycle. PROM pins 9-12 were confirmed isolated on the breadboard, and
the high level on pin 9 (the Nano D13 input) measured 4.4 V. The two matching
`d6_038_arvutimuuseum_CS00015_*capture1/2.txt` files are byte-identical aliases
of the first two streams and preserve the supplied board label without being
counted as additional reads.

The preservation-grade raw table is `validated/d6_038.raw.bin`:

```text
SHA256 05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39
```

The D6 files retain the reader's explicit address-pin sweep order. After
reordering addresses to the repository fallback's D6 convention, 252 of 256
bytes differ from `d6_rt4_memory_decode_reconstructed.bin`. The captured and
fallback nibble populations also cannot be reconciled by output-bit
permutation or whole-nibble inversion, so the mismatch is not merely a naming
or polarity change. Preserve both as distinct evidence; the physical D6 table
now has a separately power-cycled repeat, but still benefits from an independent
reader or programming-disk comparison.

Run validation with:

```sh
python3 scripts/validate_rt4_dump.py \
  ref/physical-proms/captures/d2_037_20260713_capture1.txt \
  ref/physical-proms/captures/d2_037_20260713_capture2.txt \
  ref/physical-proms/captures/d2_037_20260713_capture3_powercycled.txt \
  --out-dir /tmp/d2-validated --name d2_037

python3 scripts/validate_rt4_dump.py \
  ref/physical-proms/captures/d6_038_20260713_capture1.txt \
  ref/physical-proms/captures/d6_038_20260713_capture2.txt \
  ref/physical-proms/captures/d6_038_arvutimuuseum_CS00015_20260713_capture3_powercycled.txt \
  --out-dir /tmp/d6-validated --name d6_038
```

Verify all committed files with `sha256sum -c SHA256SUMS` from this directory.
