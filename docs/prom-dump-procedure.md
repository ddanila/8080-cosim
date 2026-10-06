# PROM and EPROM acquisition

Validated physical D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` tables are
preserved under `ref/physical-proms/validated/`. New board-qualified captures
or recovered factory programming-disk files could provide independent corroboration. Raw pin-level files
are authoritative; active-low asserted complements remain separately named.
The old D8 reconstruction is historical comparison evidence.

D15/D16 use the adopted third-source archive-37 RomBios 3.43m split. The
photographed EPROMs have not supplied its contents. See [programming images](eprom-programming-images.md).
PROM capture consistency does not close circuit continuity or timing holds;
see [D94 constraints](d94-reconstruction-constraints.md) for the FDC boundary.

Factory programmed-part drawings are indexed in `ref/baltijets-tech-docs/`.
The `.037/.038/.039/.092` small-PROM tables are not printed in that packet;
its relevant table references are marked `на диске`. The optional
[community request](community-prom-media-request.md) covers independent dumps
and `JUKU-1` media.

## Devices

Label each device by board and socket before removal.

| Chip | Where | Type | Organization | Dump method |
|---|---|---|---|---|
| К155РЕ3 (D94; record socket identity) | serial/FDC corner socket | bipolar PROM, 74188/82S23 class | 32 × 8 | MCU sweep (below) |
| К155РЕ3 (D8; record socket identity) | CPU-cluster socket | same | 32 × 8 | MCU sweep |
| КР556РТ4А (D6) | CPU cluster, socketed | bipolar PROM, 74S287/387 class | 256 × 4 | MCU sweep |
| КР556РТ4А (D2) | CPU cluster, socketed | same | 256 × 4 | MCU sweep |
| M2764AF1 ×2 (D15/D16) | ROM sockets | standard 2764 EPROM | 8K × 8 | programmer supporting the exact device |

**Handling:** photograph each socket before pulling, note pin-1 orientation,
use normal ESD precautions, and remove devices gently with an IC extractor so
old sockets and pins are not bent.

## M2764A reads

A programmer whose current device list explicitly supports the exact 2764/M2764
variant can read these EPROMs; verify the selected device and orientation before
insertion. Dump both twice, then compare the combined result with the documented
D15/D16 split of `roms/ekta37.bin`. A difference is evidence for either a BIOS
variant, a split/order issue, or a bad read—not a conclusion by itself.

## Bipolar PROMs — verify programmer support or use an MCU sweep

Do not assume a general EPROM programmer supports these bipolar PROMs; check its
current device list and any required adapter. A 5 V MCU setup is the fallback.
Outputs are open-collector. The tracked Nano readers use plain input pins
and require an individual external 3 kΩ pull-up from each data output to
+5 V. Use the device-specific wiring linked below, including the RT4
enable pull-up; the firmware does not enable internal pull-ups.

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
validator. See [RE3 acquisition](re3-physical-dumps.md) for the complete wiring,
115200-baud capture setup, and repeat command. Run validation from the repository
root with Python 3; `--out-dir` writes tables and a manifest:

```sh
python3 scripts/validate_re3_dump.py read-1.txt read-2.txt read-3.txt \
  --out-dir dump-output --name d94_092
```

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
repeat-mismatched RE3 rows. It parses only two-digit address/value CSV rows
ending in `OK` or `UNSTABLE`; other lines are ignored. Any explicit independent
read count is caller-supplied provenance, not independently verified.
It proves capture consistency, not socket identity,
wiring, polarity, or the unresolved D94 D0 hidden branch. Exact `.009` sheets
close the `CS7` shared-enable source.

## Corroboration boundaries

The adopted capture counts, aliases, and hashes belong to the manifests under
`ref/physical-proms/validated/`; filename aliases are not extra read events.
D6's corrected channel order and D2's READY polarity are described in
[RT4 acquisition](rt4-dump-acquisition.md). D2 is the bus/wait PROM;
D9 К555ИД7 is the I/O chip-select decoder.

A new dump corroborates content or identifies a candidate board variant. It
does not close D94's hidden D0 load, powered timing, or other circuit holds.
Do not substitute `.113/.117` tables from the `.106.103` family for the
adopted `.009` programs. Preserve any differing image with repeated reads and
socket provenance before deciding whether it represents a board variant.

## Drawing cross-reference — ДГШ 3.031.006 ВС

The index lists **eleven programmed-microcircuit drawings, ДГШ 5.106.037 …
5.106.047**, each marked as used by processor module `ДГШ5.109.006`. The `.009`
applicability material separately identifies D94 `.092`; do not infer that its
bytes are present in the `.037-.047` index. Label every dump by board and socket
first, then associate a drawing number only when the factory paper trail or
repeated hardware evidence supports it. The exact `.009` electrical sheet 3
covers the FDC support circuit. Its source connections do not prove owner-board
copper or powered behavior; the remaining physical boundaries are listed in
[the FDC handoff](fdc-hardware-handoff.md).
