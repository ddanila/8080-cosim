# К556РТ4 dump acquisition

Status: **HOST VALIDATION READY / PRELIMINARY D2 READ OBSERVED**

Two matching D2 reads with zero unstable addresses were observed on
2026-07-12/13 and are documented in `d2-physical-dump-and-continuity.md`.
Because the original serial streams were not saved unchanged, a separately
power-cycled capture still needs to be preserved and passed through this
validator before exporting the preservation artifact.

`scripts/validate_rt4_dump.py` validates the line-oriented serial format emitted
by a К556РТ4 reader. It is applicable to D2 `.037` and D6 `.038`; it does not
read the different К155РЕ3 used for D8 or D94.

## Capture requirements

1. Capture at least two complete 256-address reads. Three reads after separate
   power cycles are preferred.
2. Preserve the raw serial logs unchanged. Each data row must be
   `AA,R,L,OK`, where `AA` is the address, `R` is the four physical output-pin
   levels, and `L=(~R)&0xF` is the active-low asserted view.
3. Any missing, duplicate, unstable, non-complementary, or repeat-mismatched
   row fails validation. Do not majority-vote a damaged PROM into agreement.
4. Record the socket/refdes, programmed drawing (`.037` or `.038`), reader
   wiring, pull-up values, supply voltage, board/part photographs, date, and
   operator alongside the raw logs.

Run:

```sh
python3 scripts/validate_rt4_dump.py capture-1.txt capture-2.txt capture-3.txt \
  --out-dir dump-output --name d2_037
```

The output retains both interpretations:

- `*.raw.bin` is the authoritative electrical pin-level table: 256 bytes in
  address order, low nibble significant. This is the representation to compare
  with the repository's 256-byte D6 fallback.
- `*.asserted.bin` is the bitwise low-nibble complement and is only a convenient
  active-low assertion view. It must not silently replace the raw table.
- `*.raw.hex` is one two-digit raw nibble byte per address.
- `*.dump.json` records input hashes, capture count, packing, and output hashes.

The validator proves internal capture consistency, not reader wiring, device
identity, output polarity, or historical provenance. Those require the physical
records above. A sound repeated D2 dump would close the `.037` content gap but
would not resolve any still-untraced board output branch. D94 `.092` requires a
separate К155РЕ3 reader plus the outstanding continuity work.

Self-test:

```sh
python3 scripts/validate_rt4_dump.py --self-test
```
