# К556РТ4 dump acquisition

Status: **CAPTURE CONSISTENCY VALIDATED / D6 ELECTRICAL RE-READ QUEUED**

Three preserved D2 captures and three preserved D6 captures—each set including
a separate power cycle—validate with zero unstable or mismatched addresses.
Inputs and derived artifacts are under `ref/physical-proms/`.
Provenance-labelled D2 aliases and the first two D6 aliases are also preserved,
but byte identity proves they are copies of the canonical serial streams rather
than additional independent measurements. The D6 CS00015 power-cycled stream
has no earlier counterpart and is the adopted third read.

`scripts/validate_rt4_dump.py` validates the line-oriented serial format emitted
by a К556РТ4 reader. It is applicable to D2 `.037` and D6 `.038`; it does not
read the different К155РЕ3 used for D8 or D94.

The original Nano wiring used D13 for PROM D3/pin 9. Although the D2 capture
proves that channel observed both released-high and driven-low states in lockstep
with D0-D2, D13's on-board LED is an unnecessary load and cannot remain in the
decisive D6 polarity experiment. Reader revision 2 moves D3 to A0 and drives
PROM /CE pin 14 from A1. Before each dump it disables the PROM and requires all
four externally pulled-up data inputs to read stable `F`; a failed self-test
aborts the capture. This removes the loading ambiguity without presuming that
it caused the existing D6 table.

## Revision-2 wiring and D6 discriminator

- PROM A0-A7/pins 5,6,7,4,3,2,1,15 -> Nano D2-D9.
- PROM D0-D3/pins 12,11,10,9 -> Nano D10,D11,D12,A0. Leave Nano D13 open.
- PROM /CE pin 13 -> GND; /CE pin 14 -> Nano A1.
- PROM pin 8 -> GND and pin 16 -> regulated +5 V. Fit an individual external
  1k-4.7k pull-up from every data output to +5 V.
- Require `# disabled_raw=F,stable=OK` before accepting a dump. First re-read
  known D2 and require byte identity with `d2_037.raw.bin`; then capture D6
  three times including a power cycle.

Compare the new D6 raw image with
`ref/physical-proms/validated/d6_038.raw.bin`. An exact match eliminates the
Nano-D13 theory. An exact D0/D3-only complement is the result predicted by the
byte-identical boot experiment and permits a provenance-reviewed replacement.
Any other stable difference is a new capture/device-identity investigation,
not permission to transform the table.

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
5. For revision-2 captures, preserve the `reader_revision`, `data_map`, and
   `disabled_raw` lines. Reject a stream without a stable disabled value of `F`.

Run:

```sh
python3 scripts/validate_rt4_dump.py capture-1.txt capture-2.txt capture-3.txt \
  --out-dir dump-output --name d2_037
```

The output retains both interpretations:

- `*.raw.bin` is the authoritative electrical pin-level table: 256 bytes in
  address order, low nibble significant. This is the representation to compare
  with the repository's validated physical RT4 images.
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
