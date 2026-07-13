# PROM dump procedure — the 4 socketed chips (+2 EPROMs)

D8 `.039` and D94 `.092` now have validated repeated physical captures, as do
D2 `.037` and D6 `.038`. Further reads and programming-disk copies are
independent corroboration rather than missing content inputs. D94's complete
control-strobe continuity is still needed for FDC-era reconstruction; its
proved D0-D2 paths terminate at D93 and are not video-slot timing evidence.

Update 2026-07-06: Baltijets doc 007 was fetched and triaged in
`ref/baltijets-tech-docs/`. It confirms programmed-part drawings for the small
PROMs, but the relevant programming tables are marked `на диске` rather than
printed in the PDF. Unless those disk files surface, this dump procedure remains
the practical path to truth.

The ready-to-send community request packet is
`docs/community-prom-media-request.md`; it names the same chips, expected dump
sizes, and the `JUKU-1` media request in one owner-friendly message.

PROM update: validated physical D2/D6/D8/D94 raw tables are preserved under
`ref/physical-proms/`. The D8 reconstruction is retained only as historical
diff evidence. Raw pin-level files are authoritative; asserted complements
remain separately named.

EPROM programming update: `scripts/export_eprom_pair.py` deterministically
splits the boot-validated `roms/ekta37.bin` into low D15 and high D16 8 KiB
images under `ref/eprom-images/`, with SHA256 and concatenation guards. These
are Tier-1/2 functional programming images, not physical-device dumps; see
`docs/eprom-programming-images.md`.

## What to pull (label each with its socket refdes + board # before removing!)
| Chip | Where | Type | Organization | Dump method |
|---|---|---|---|---|
| К155РЕ3 (candidate D94; confirm refdes) | serial/FDC corner socket (board #2; loosely seated already) | bipolar PROM, 74188/82S23 class | 32 × 8 | MCU sweep (below) |
| К155РЕ3 (candidate D8; confirm refdes) | CPU-cluster socket | same | 32 × 8 | MCU sweep |
| КР556РТ4А (D6) | CPU cluster, socketed | bipolar PROM, 74S287/387 class | 256 × 4 | MCU sweep |
| КР556РТ4А (D2) | CPU cluster, socketed | same | 256 × 4 | MCU sweep |
| M2764AF1 ×2 (D15/D16) | ROM sockets | standard 2764 EPROM | 8K × 8 | any programmer (TL866 etc.) |

**Handling:** photograph each socket before pulling, note pin-1 orientation,
use normal ESD precautions, and remove devices gently with an IC extractor so
old sockets and pins are not bent.

## M2764A (easy, do first)
A programmer whose current device list explicitly supports the exact 2764/M2764
variant can read these EPROMs; verify the selected device and orientation before
insertion. Dump both twice, then compare the combined result with the documented
D15/D16 split of `roms/ekta37.bin`. A difference is evidence for either a BIOS
variant, a split/order issue, or a bad read—not a conclusion by itself.

## Bipolar PROMs — verify programmer support or use an MCU sweep
Do not assume a general EPROM programmer supports these bipolar PROMs; check its
current device list and any required adapter. A 5 V MCU setup is the fallback.
Outputs are open-collector →
**pull-ups needed: 4.7k from each output pin to +5V** (or enable internal pull-ups and read
open-collector as-is — external 4.7k is more reliable for S-series).

### К155РЕ3 (= 74188/82S23, DIP-16) pinout
- VCC = 16, GND = 8 *(confirmed by the board's own power table)*
- Outputs O1..O8 = pins 1,2,3,4,5,6,7,9 (open-collector)
- Address A0..A4 = pins 10,11,12,13,14
- /CE = 15 (tie to GND)
Sweep: for A in 0..31: set address pins, delay ≥1µs, read 8 outputs → 32 bytes. Read the whole
array **twice**, require identical; also sanity-check the dump isn't all-0x00/all-0xFF.

Capture each row as `AA,RR,OK`, where `AA` is the two-digit address and `RR`
is the raw two-digit output-pin byte (`D0..D7` = bits 0..7). Validate repeated
logs with the tracked Nano reader at `tools/re3_dumper/re3_dumper.ino` and host
validator:

```sh
python3 scripts/validate_re3_dump.py read-1.txt read-2.txt read-3.txt \
  --out-dir dump-output --name d94_092
```

The validator emits both raw pin levels and a separately named active-low
asserted complement. Raw levels are the authoritative dump and the format used
by the validated 32-byte tables; do not replace them silently with asserted bits.

### КР556РТ4А (74S287/387 class, DIP-16, 256×4)
- VCC = 16, GND = 8 *(power table)*
- **Verify the А/О pin order against a КР556РТ4А datasheet before wiring** — Soviet sources vary;
  the 74S287 layout (A0..A7 = 5,6,7,4,3,2,1,15; O1..O4 = 12,11,10,9; /CS = 13,14 to GND) is the
  starting hypothesis, but confirm VCC/GND with a multimeter continuity to the socket's power
  traces first, then identify /CS by trying both candidates.
Sweep: 256 nibbles → store as 256 bytes (low nibble). Twice + compare, sanity-check.

## Deliverables → repo
`proms/re3_1.bin` (32B), `proms/re3_2.bin` (32B), `proms/rt4_d6.bin` (256B, nibbles),
`proms/rt4_d2.bin` (256B), `proms/m2764_d15.bin` + `_d16.bin` (8KB each) + a provenance README
(board #, socket, date, method). 

Host validation rejects missing, duplicate, out-of-range, unstable, or
repeat-mismatched RE3 rows. It proves capture consistency, not socket identity,
wiring, polarity, or the unresolved D94 input/enable/output branches.

## What each dump unlocks
1. **РЕ3 dumps**: socket/refdes identification is essential. D8 `.039` and
   D94 `.092` repeated reads are adopted; new reads corroborate or identify a
   board variant. D94's missing input/enable/output continuity still defines the
   physical FDC control boundary.
   Do not substitute the `.113/.117` tables from the `.106.103` family.
2. **РТ4 D6 → memory-decode corroboration**: a separately power-cycled third
   read now matches the adopted physical `.038` table. Compare an independent
   reader or programming-disk artifact next; preserve any stable difference as
   a board variant.
3. **РТ4 D2 → bus/wait corroboration**: compare another physical `.037` read
   with the three matching adopted captures. It does **not** replace the I/O
   decoder; board evidence puts the functional I/O chip-select decoder at D9
   К555ИД7.
4. **M2764 ×2**: validates (or forks) our ekta37 ROM image against this physical board.

If a future owner dump differs from `ref/physical-proms/validated/*.bin`, keep
it as a candidate board variant until repeated reads and socket provenance are
sound. The old D8 reconstruction is historical comparison material only.

## Drawing cross-reference (found 2026-07-03, drawing index ДГШ 3.031.006 ВС)
The index lists **eleven programmed-microcircuit drawings, ДГШ 5.106.037 …
5.106.047**, each marked as used by processor module `ДГШ5.109.006`. The `.009`
applicability material separately identifies D94 `.092`; do not infer that its
bytes are present in the `.037-.047` index. Label every dump by board and socket
first, then associate a drawing number only when the factory paper trail or
repeated hardware evidence supports it. The available electrical schematic
does not contain the complete `.009` FDC support circuit, so continuity evidence
is still required.
