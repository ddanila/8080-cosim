# PROM dump procedure — the 4 socketed chips (+2 EPROMs)

Validated physical D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` tables are
preserved under `ref/physical-proms/validated/`. Further captures and factory
programming-disk files provide independent corroboration. Raw pin-level files
are authoritative; active-low asserted complements remain separately named.
The old D8 reconstruction is historical comparison evidence.

D15/D16 use the adopted third-source EktaSoft 3.7 split, rather than direct
reads of the photographed EPROMs. See [programming images](eprom-programming-images.md).
PROM capture consistency does not close circuit continuity or timing holds;
see [D94 constraints](d94-reconstruction-constraints.md) for the FDC boundary.

Factory programmed-part drawings are indexed in `ref/baltijets-tech-docs/`,
but their programming tables are marked `на диске`. The optional
[community request](community-prom-media-request.md) covers independent dumps
and `JUKU-1` media.

## What to pull (label each with its socket refdes + board # before removing!)
| Chip | Where | Type | Organization | Dump method |
|---|---|---|---|---|
| К155РЕ3 (D94; record socket identity) | serial/FDC corner socket | bipolar PROM, 74188/82S23 class | 32 × 8 | MCU sweep (below) |
| К155РЕ3 (D8; record socket identity) | CPU-cluster socket | same | 32 × 8 | MCU sweep |
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
- A0..A7 = pins 5,6,7,4,3,2,1,15; D0..D3 = pins 12,11,10,9.
- Active-low enables are pins 13 and 14. Confirm device identity and wiring
  against the validated reader before powering; do not identify pins by trial.
- Store 256 raw nibbles as 256 bytes, using the low nibble.

Use reader-3 firmware at
`tools/re3_board_rt4_dumper/re3_board_rt4_dumper.ino`. Both enables are controlled;
all disabled-output checks must release the four external pull-ups to raw `F`.
Follow [RT4 acquisition](rt4-dump-acquisition.md) for the exact wiring, flashing,
D2 control, and repeated-capture validation commands.

## Capture deliverables

Preserve raw serial logs, repeat-read results, board/socket photographs, and
reader/device settings with each acquisition. Use a new capture name for a new
board or device; keep differing images as candidates instead of overwriting the
adopted tables. RE3 images are 32 bytes, RT4 images are 256 low-nibble bytes,
and each D15/D16 EPROM is 8 KiB. Validated PROM artifacts and manifests live
under `ref/physical-proms/validated/`; the adopted EPROM split is under
`ref/eprom-images/`.

Host validation rejects missing, duplicate, out-of-range, unstable, or
repeat-mismatched RE3 rows. It proves capture consistency, not socket identity,
wiring, polarity, or the unresolved D94 D0 hidden branch. Exact `.009` sheets
close the `CS7` shared-enable source.

## What each dump unlocks
1. **РЕ3 dumps**: socket/refdes identification is essential. D8 `.039` and
   D94 `.092` repeated reads are adopted; new reads corroborate or identify a
   board variant. D94's D0 hidden load still defines a physical FDC control
   boundary; its `CS7` enable source is drawing-closed.
   Do not substitute the `.113/.117` tables from the `.106.103` family.
2. **РТ4 D6 → memory-decode corroboration**: three revision-3 captures including
   a power cycle agree. They prove the old artifact was an exact reversal of all
   four data bits; the corrected `.038` table is adopted directly. Compare an
   independent reader or programming-disk artifact only as optional provenance.
3. **РТ4 D2 → bus/wait corroboration**: compare another physical `.037` read
   with the three matching adopted captures. It does **not** replace the I/O
   decoder; board evidence puts the functional I/O chip-select decoder at D9
   К555ИД7.
4. **M2764 ×2**: optionally corroborates (or forks) the adopted Ekta 3.7 pair
   against another physical board.

If a future owner dump differs from `ref/physical-proms/validated/*.bin`, keep
it as a candidate board variant until repeated reads and socket provenance are
sound. The old D8 reconstruction is historical comparison material only.

## Drawing cross-reference — ДГШ 3.031.006 ВС
The index lists **eleven programmed-microcircuit drawings, ДГШ 5.106.037 …
5.106.047**, each marked as used by processor module `ДГШ5.109.006`. The `.009`
applicability material separately identifies D94 `.092`; do not infer that its
bytes are present in the `.037-.047` index. Label every dump by board and socket
first, then associate a drawing number only when the factory paper trail or
repeated hardware evidence supports it. The retained exact `.009` electrical sheet 3 now covers the FDC support
circuit. Its source connections do not prove owner-board copper or powered
behavior; the remaining physical boundaries are listed in
[the FDC handoff](fdc-hardware-handoff.md).
