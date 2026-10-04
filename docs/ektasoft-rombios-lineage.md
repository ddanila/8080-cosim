# EktaSoft serial/RomBios lineage notes

This analysis combines static observations of the pinned binaries with
the cited drawing and owner-photo evidence. The snippet at the end reproduces
serial/version strings, positional differences, and a selected boot-raster comparison; it does not
reproduce every analysis below or verify physical compatibility. This complements the generated
[`d15-d16-firmware-lineage.md`](d15-d16-firmware-lineage.md), which
establishes archival identity for the adopted pair; this note explains how
the vendored EktaSoft images relate to each other.

## File names are serial numbers, not versions

Each image's banner carries a per-machine serial and a separate RomBios
version. The `ektaNN.bin` names come from the serials:

| File | Banner | RomBios | SHA256 |
| --- | --- | --- | --- |
| `ekta24.bin` | EktaSoft '88, Serial #0024 | 3.42 | `e1bd9894134ee4085c14bde854780539d3b1e03cfc032c81ec352729e9d69287` |
| `ekta31.bin` | EktaSoft '88, Serial #0031 | 3.43 | `26f1f4161a547ea60312a250bde9df41c0b07a939c0b880628050eaec18ec4e4` |
| `ekta32.bin` | EktaSoft '88, Serial #0032 | **2.43** | `1826563e23b5d8bc23c61694ceccb923d6a31778077934ad0338772070671122` |
| `ekta35.bin` | EktaSoft '88, Serial #0035 | 3.43 | `e8fe5e657037b8f3203f57512cd01cc35f7eaa2a3f0dae8d0ae19378908bd518` |
| `ekta37.bin` | EktaSoft '88, Serial #0037 | **3.43m** | `fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27` |
| `ekta43.bin` | EktaSoft **'90**, Serial #0043 | **2.43m** | `39e3ca8978b369632d03c658300654445b898139009f188cb154e2f901238ba7` |

Serial order does not follow banner version order: #0032 carries 2.43
between two serials carrying 3.43. The banners identify **2.43/2.43m**
(serials #0032 and #0043) and **3.42/3.43/3.43m** (the other four); they
do not establish the release sequence. The adopted replica image is serial
#0037, RomBios 3.43m.

## S21 read versus the `.009` E8 bridge

Five archived images read PPI Port B and mask PB5 during their configuration
scan. The byte sequence `DB 05 2F FB E6 20` begins at `1200h` in #0024,
`120Ah` in #0032, and `1211h` in #0031, #0035, and #0037. These bytes mean
`IN 05h`, complement, enable interrupts, then `ANI 20h`; all five select
PB5. The #0043 image lacks that sequence: its `1214h` read begins
`DB 05 07 D0` and tests a different condition, consistent with its separate
RomBios 2.43m line. No archived image in this set supplies evidence for a
PB4 S21 scan.

The exact `.009 Э3` E8.3/E8.4 drawing, `.009 СБ` 3–4 bridge, and surviving
board's fitted white wire select PB4 for `CONTRDAT`. The five PB5-reading
ROMs therefore do not explain S21 operation through that fitted bridge.
The original board's installed firmware and powered PB4/PB5 behavior remain
the necessary discriminators; this is a revision boundary, not a reason to
reinterpret the E8 terminal numbers.

The 1990 `ekta43.bin` banner identifies RomBios 2.43m, while #0032 identifies
2.43. Banner year alone does not establish code ancestry or feature coverage.

## Banner-declared configurations

| Serial | RomBios | Screen | Keyboard | Disk | Second BIOS |
| --- | --- | --- | --- | --- | --- |
| #0024 | 3.42 | 53x24/+wnd | Juss' Qwerty | Fdc **1791/2** on MBoard | NetBios |
| #0031 | 3.43 | 40x24/+wnd | Juku' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0032 | 2.43 | 53x24/+wnd | Juku' Qwerty | Fdc 1793 on Card | TapeBios |
| #0035 | 3.43 | 53x24/+wnd | Juss' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0037 | 3.43m | 40x24/+wnd | Juku' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0043 | 2.43m | 53x24/+wnd | **IBM AT** | Fdc 1793 on Card | TapeBios |

The banners describe different screen, keyboard, FDC, and secondary-BIOS
configurations; they do not establish that one image is a feature superset.
The 53-column screen is not a 2.43-line trait (#0035 pairs it with 3.43 and
NetBios), and #0024 even targets a different FDC chip.

Compared with #0032, #0043 changes the banner-declared keyboard to IBM AT;
its 53x24 screen, TapeBios and card-mounted FDC remain the 2.43-line
configuration. For the `.009` board, #0037's motherboard FDC, original
matrix keyboard and NetBios are the closer banner-declared match. This
supports its adoption without proving complete firmware-to-board compatibility:
the PB4/PB5 S21 boundary remains unresolved. The NetBios boot path is analyzed
in [the network BIOS notes](ekta37-netbios-notes.md).

## Binary comparison

Comparing #0043 with the other five EktaSoft images gives 12,328–13,814
unequal byte positions out of 16,384 (reproduced below). This measures
positional differences; it does not establish source ancestry or distinguish
changed code from relocated code. The [FDC bus analysis](fdc-bus-polarity.md)
identifies a shared port-`1Ch/1Dh` bit-stream routine in #0032/#0043 and
Monitor 2.2.

## Boot PIT programming across the lines and families

All six EktaSoft images boot with the **same decoded PIT write sequence**
(exact offsets: #0024 `01C3h`, #0031/#0035/#0037 `01D4h`, #0032 `01E2h`,
#0043 `01DCh`): the byte-identical D54/D55 raster values (64 us lines,
313-line frames, identical porches) that
[`video-pit-timing.md`](video-pit-timing.md) proves drive the autonomous
raster and that the CS00024 experiment replays
([`../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md`](../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md)),
plus the D57 counter-0 control `1Fh` and count `32h` (BCD 32)
for 2400 baud in every image.

The Monitor family programs the same timing chain with equivalent values
and different encodings (jmon22 offset `0051h` inline; jmon33 offsets
`0026h`/`004Fh` split, with the blank/porch counts `24h/08h/72h/25h`
deferred to a later routine at `2E89h..2E98h`):

- D54 horizontal: same controls `15h/53h/93h`, same 64 us line;
- D55 vertical: control `35h` (BCD) count `0312` = **312 lines**, where
  EktaSoft uses control `34h` (binary) count `0139h` = **313** — a one-line
  frame-height/encoding difference between the families;
- D57 counter 0: control `1Fh`, count `32h` (BCD 32), giving 2400 baud
  in all eight images.

The one qualitative split is D57 channel 2 (`SYNC_B`), and it tracks the
**firmware generation across both families**, not the family:

- **2.x generation** — Monitor 2.2 (jmon22), RomBios 2.43/2.43m
  (#0032/#0043): control `9Fh`, count `32h` (BCD 32) — mode 3;
- **3.x generation** — RomBios 3.42 (#0024), 3.43/3.43m
  (#0031/#0035/#0037), Monitor 3.3 (jmon33): control `B0h`, count `FFFFh`
  — binary mode 0.

These bytes show use of channel 2 across both generations. They do not
establish a 38.4 kHz output or a 53 ms timeout: the exact `.009` topology
clocks D57.18 from D55.13 `/VER RTR` at approximately 49.92 Hz, independently
of the 1.23 MHz channel-0 clock. With that input, enabled counting and no
reprogramming, count 32 gives a nominal mode-3 period of about 0.641 s;
65535 clocks in mode 0 take about 21.9 minutes. Actual OUT2 behavior also
depends on its gate and later firmware writes.

The remote consumer of `SYNC_B` remains an unresolved drawing boundary.
Legacy CS00024 channel-2 samples did not wait for the frame clock and do not
prove a fault. The corrected probe passed on CS00015 and remains pending on
CS00024; see [the timing correction](cs00024-t36-diagnosis.md#d57-channel-2-timing-correction).

All six EktaSoft images also carry the same pair of later D54/D55
parameter routines (near `0EFCh..0F39h`): one alternative set
(`16h→11h`, `02h` or `04h`→`12h`, `0112h→15h`, `45h→16h`) and one
restoring the boot set. They appear in the 40-column and 53-column
configurations alike, so they are shared runtime code, not the wide-screen
mode. The alternative set's D54 channel-2 byte is `02h` in #0024 and
#0043 and `04h` in #0031/#0032/#0035/#0037; no version pattern or
interpretation is attached.

Related bootstrap identity strings (each `ESC L`-prefixed): #0037 carries
`BOOTSTRAP v4.1 - 1793 on Main board` (ROM `23C4h`), jmon33 carries
`BOOTSTRAP v3.3 - 1791 on Main board` (ROM `20A4h`), and jmon22 contains
no bootstrap banner as dumped.

## Monitor family notes

The Monitor images share a per-block checksum layout: eight stored bytes at
`0003h..000Ah`, block
0 covering `0004h..07FFh` and blocks 1-7 covering their full 2 KiB. This
is distinct from EktaSoft's eight checksums across two header regions,
described in [the remix guide](../spinoffs/jukuravi/remix/README.md#checksum-convention).
The Monitor convention diagnoses jmon22's corrupt blocks
([`jmon22-reconstruction.md`](jmon22-reconstruction.md)); jmon33 passes
all eight (byte-verified). This makes it a checksum-consistent comparison
image, not an independent proof of every byte's correctness. Monitor boot is
a short in-place sequence (checksum verification,
PIT and PPI init) followed by copying ROM `3F40h..3FFFh` to
`FF40h..FFFFh` and dispatching through that vector region. Maintained
annotated disassemblies of both Monitor images live in
[`../disasm/`](../disasm/README.md).

## Checksum status

The block-1 convention (additive sum of `000Bh..07FFh` stored at `000Ah`,
verified by the boot routine at `03E0h`) is documented in
[`cosim-runtime-reference.md`](cosim-runtime-reference.md). All five
official images pass. #0043 stores stale `F2h` against computed `57h` —
a checksum inconsistency whose cause is not established by the sum alone. The vendored binary is preserved unmodified; `cosim/trace.c`
applies an explicitly logged `F2h -> 57h` load-time compatibility patch so
the image can boot in simulation.

## Reproduction

```sh
python3 - <<'EOF'
import re
from pathlib import Path
roms = {n: Path(f"roms/{n}.bin").read_bytes()
        for n in ("ekta24","ekta31","ekta32","ekta35","ekta37","ekta43")}
for n, b in roms.items():
    print(n, [s.decode() for s in re.findall(rb"[ -~]{5,}", b)
              if b"Serial" in s or b"RomBios" in s])
reference = roms["ekta43"]
for n, b in roms.items():
    assert len(b) == len(reference) == 16384
    if n != "ekta43":
        print("ekta43 versus", n, "unequal byte positions:",
              sum(x != y for x, y in zip(reference, b)))
def runs(rom):
    out, i, cur = [], 0, []
    while i < len(rom) - 3:
        if rom[i] == 0x3E and rom[i+2] == 0xD3 and 0x10 <= rom[i+3] <= 0x1B:
            cur.append((rom[i+3], rom[i+1])); i += 4
        elif rom[i] == 0xD3 and 0x10 <= rom[i+1] <= 0x1B and cur:
            cur.append((rom[i+1], None)); i += 2
        else:
            if len(cur) >= 5: out.append(cur)
            cur = []; i += 1
    return out
raster = lambda r: [(p, v) for p, v in r[0] if 0x10 <= p <= 0x17]
print("boot raster identical:",
      raster(runs(roms["ekta32"])) == raster(runs(roms["ekta43"]))
      == raster(runs(roms["ekta37"])))
EOF
```
