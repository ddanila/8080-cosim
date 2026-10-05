# К556РТ4 dump acquisition

Status: **READER-3 CONTROL VALIDATED / D6 CHANNEL ORDER CORRECTED**

The 2026-07-19 reader-3 session reproduced D2 byte-for-byte across three reads,
then captured D6 three times—including a separate power cycle—with zero unstable
or mismatched addresses.
Inputs and derived artifacts are under `ref/physical-proms/`.
The older D2/D6 capture aliases are preserved as provenance evidence. The
authoritative D6 artifact is derived only from the three revision-3 Sukharev
captures; the older D6 streams classify as an exact bit reversal.

`scripts/validate_rt4_dump.py` validates the line-oriented serial format emitted
by a К556РТ4 reader. It is applicable to D2 `.037` and D6 `.038`; it does not
read the different К155РЕ3 used for D8 or D94.

The original reader used Nano D13 for PROM D3/pin 9, introducing a loading
ambiguity. Reader 3 uses the wiring below; independent socket continuity fixes
pins 12..9 as D0..D3. Its D6 table is authoritative, and the original streams
remain preserved as reversed-channel captures.

The original D13 caveat does not leave D2's board-used output ambiguous. D2 D0/pin12
was sampled on Nano D10 with its own external pull-up; only D3 used Nano D13,
and D2 D3 is an intentional board no-connect. Direct continuity also places
D0 on D30.2 and R6. The executable guard `sync/d2_ready_path_check.sh` therefore
pins D2 raw `0` as READY low and raw `F`/disabled as pulled-up READY high.
The corrected-reader session exposed D6's channel-order error without changing
the already validated D2 table.

## Reader-3 wiring

Earlier revision-2 captures remain supported by the validator. Their wiring is
recorded in `tools/rt4_dumper/rt4_dumper.ino`.

`tools/re3_board_rt4_dumper/re3_board_rt4_dumper.ino` is reader revision 3.
It reuses the tracked K155RE3 Nano reader wiring after moving the four external
3 kOhm output pull-ups to RT4 pins 9-12 and adding a fifth 3 kOhm fail-safe
pull-up from RT4 /CE pin 14 to +5 V. The former RE3 pull-ups on pins 1-7 must
be removed. The firmware remaps A0-A7 to Nano D12,D13,A0,D11,D10,D9,D8,D7,
D0-D3 to Nano D4,D3,D2,A1, and the two active-low enables to Nano D5,D6.

Revision 3 checks output release three ways before reading: both enables high,
pin 14 high by itself, and pin 13 high by itself. All three checks must report
stable raw `F`. For a declared revision-3 capture, the host validator requires
this exact mapping and all three enable checks. Re-read known D2 first and require
byte identity with the validated `d2_037.raw.bin`. Then capture D6 three times,
including a separate power cycle.

Flash through USBasp ISP with `arduino-cli`, the Arduino AVR board core, and
`avrdude` installed. Remove the PROM from the reader socket before flashing.
Run the following commands from the repository root,
then disconnect USBasp and reconnect the Nano's normal USB serial interface for
the 115200-baud capture:

```sh
arduino-cli compile \
  --fqbn arduino:avr:nano:cpu=atmega328 \
  --build-path tools/re3_board_rt4_dumper/build \
  tools/re3_board_rt4_dumper
avrdude -c usbasp -p m328p \
  -U flash:w:tools/re3_board_rt4_dumper/build/re3_board_rt4_dumper.ino.hex:i
```

Require successful device identification, writing, and verification on each upload.

ISP programming may erase the Nano serial bootloader; that does not affect the
reader firmware, but later serial-port uploads require reburning the bootloader.
Do not power the Nano from USBasp and its normal USB connector simultaneously
unless the USBasp target-power jumper is disconnected.

Compare any future D6 raw image with
`ref/physical-proms/validated/d6_038.raw.bin`. A correctly packed repeat must be
an exact match. `EXACT_BIT_REVERSE` identifies the relationship of the
superseded original artifact to the corrected baseline. Any other stable
difference is a new capture/device-identity investigation, not permission to
transform the table.

The host validator performs this classification directly. When reader metadata
is detected, it requires a complete, consistent revision-2 or revision-3 record,
including the exact pin map and applicable disabled-output checks. Legacy logs
without reader metadata are also accepted; a validation pass alone does not
establish their reader revision or confirm those checks. Preserve and inspect
the metadata when qualifying a new read:

```sh
python3 scripts/validate_rt4_dump.py d6-read-1.txt d6-read-2.txt d6-read-3.txt \
  --compare-raw ref/physical-proms/validated/d6_038.raw.bin \
  --out-dir dump-output --name d6_038_reread
```

The comparison result is exactly one of `EXACT_MATCH`,
`EXACT_D0_D3_COMPLEMENT`, `EXACT_BIT_REVERSE`, or `OTHER_DIFFERENCE` with
changed-row, first-byte, and per-output flip counts. The bit-reverse result is
actionable only when independent socket-to-reader continuity fixes the physical
pin order, as it did for the 2026-07-19 revision-3 reread.
When `--out-dir` is used, the dump JSON preserves the comparison path, baseline
SHA256, and classification alongside the capture hashes.

Comparison is informational: every classification can return exit status 0
when capture validation succeeds. Require `EXACT_MATCH` explicitly when
checking a reread against the adopted baseline.

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
5. Preserve `reader_revision`, `data_map`, and `disabled_raw` metadata for
   revision-2/3 captures. Revision 3 also requires both separate enable-release
   checks. Reject any required check without stable raw `F`.

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
records above. D2 `.037` and D6 `.038` content is already validated; new reads
corroborate those artifacts without resolving untraced board output branches.
D8 `.039` and D94 `.092` also have validated physical captures, acquired with
the separate К155РЕ3 reader described in
[RE3 physical dumps](re3-physical-dumps.md). D94's hidden D0 load remains a
continuity boundary independently of its recovered contents.

Self-test:

```sh
python3 scripts/validate_rt4_dump.py --self-test
```
