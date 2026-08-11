# EktaSoft serial/RomBios lineage notes

Status: hand-written analysis of the vendored images, 2026-08-11. Every
claim below is a static observation of the pinned binaries and is
reproducible with the snippet at the end. This complements the generated
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

Serial order does not follow version order (the lowest serial carries
RomBios 3.42), so these are per-machine configuration builds rather than a
release sequence. Two RomBios lines are present: **2.43** (serials #0032
and #0043) and **3.42/3.43** (the other four). The adopted replica image is
serial #0037, RomBios 3.43m.

Consequently `ekta43.bin` — the "homebrew" image with the stale block-1
checksum — is **not built on the newer 3.43 line**. It is a 1990 build of
the *older* RomBios 2.43 line, sharing its configuration with official
serial #0032. It does not include the 3.43 line at all, despite being
chronologically the newest banner year.

## Banner-declared configurations

| Serial | RomBios | Screen | Keyboard | Disk | Second BIOS |
| --- | --- | --- | --- | --- | --- |
| #0024 | 3.42 | 53x24/+wnd | Juss' Qwerty | Fdc **1791/2** on MBoard | NetBios |
| #0031 | 3.43 | 40x24/+wnd | Juku' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0032 | 2.43 | 53x24/+wnd | Juku' Qwerty | Fdc 1793 on Card | TapeBios |
| #0035 | 3.43 | 53x24/+wnd | Juss' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0037 | 3.43m | 40x24/+wnd | Juku' Qwerty | Fdc 1793 on MBoard | NetBios |
| #0043 | 2.43m | 53x24/+wnd | **IBM AT** | Fdc 1793 on Card | TapeBios |

Every configuration axis varies independently — screen width, keyboard
family (Juku matrix, the E5103 "Juss" variant, IBM AT), FDC chip and
location, network versus tape BIOS — so no image is a feature superset of
another and "best" is only defined relative to a target machine. The
53-column screen is not a 2.43-line trait (#0035 pairs it with 3.43 and
NetBios), and #0024 even targets a different FDC chip.

The only banner-visible difference between #0043 and official #0032 is the
IBM AT keyboard. The 53x24 screen, TapeBios, and card-mounted FDC are the
2.43-line configuration, not homebrew additions. #0043 therefore offers our
`.009` board nothing over the adopted 3.43m image: the board's FDC is on
the motherboard, its keyboard is the original matrix, and the network BIOS
exists only in the 3.4x line. #0037 matches the `.009` hardware on every
axis, which independently validates its adoption. The NetBios boot path
itself is analyzed in [`ekta37-netbios-notes.md`](ekta37-netbios-notes.md).

## Content kinship

Byte-positional diffs are large against every sibling (12,328..13,814 of
16,384 bytes), so no image is a byte-patch of another. Content-addressed
comparison (fraction of #0043's non-trivial 8-byte chunks found anywhere in
the candidate) ranks its kinship: **43% with #0032** versus 35% with #0037.
Both facts together read as rebuilt/relocated images from shared source
lines, with #0043 closest to the 2.43 line — consistent with
[`fdc-bus-polarity.md`](fdc-bus-polarity.md), which already grouped serials
#0032/#0043 by their shared port-`1Ch/1Dh` bit-stream storage routine.

## Boot PIT programming across the lines and families

All six EktaSoft images boot with the **same decoded PIT write sequence**
(exact offsets: #0024 `01C3h`, #0031/#0035/#0037 `01D4h`, #0032 `01E2h`,
#0043 `01DCh`): the byte-identical D54/D55 raster values (64 us lines,
313-line frames, identical porches) that
[`video-pit-timing.md`](video-pit-timing.md) proves drive the autonomous
raster and that the CS00024 experiment replays
([`../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md`](../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md)),
plus the 2400-baud D57 counter-0 divisor (`1Fh`, BCD 32) in every image.

The Monitor family programs the same timing chain with equivalent values
and different encodings (jmon22 offset `0051h` inline; jmon33 offsets
`0026h`/`004Fh` split, with the blank/porch counts `24h/08h/72h/25h`
deferred to a later routine at `2E89h..2E98h`):

- D54 horizontal: same controls `15h/53h/93h`, same 64 us line;
- D55 vertical: control `35h` (BCD) count `0312` = **312 lines**, where
  EktaSoft uses control `34h` (binary) count `0139h` = **313** — a one-line
  frame-height/encoding difference between the families;
- D57 counter 0: same `1Fh` + BCD 32 = 2400 baud in all eight images.

The one qualitative split is D57 channel 2 (`SYNC_B`), and it tracks the
**firmware generation across both families**, not the family:

- **2.x generation** — Monitor 2.2 (jmon22), RomBios 2.43/2.43m
  (#0032/#0043): control `9Fh`, count BCD 32 — **mode 3 square wave,
  1.23 MHz / 32 = 38.4 kHz** on OUT2;
- **3.x generation** — RomBios 3.42 (#0024), 3.43/3.43m
  (#0031/#0035/#0037), Monitor 3.3 (jmon33): control `B0h`, count `FFFFh`
  — binary mode 0, a one-shot whose OUT2 rises after ~53 ms.

Every firmware generation is therefore a period-legitimate consumer of the
exact channel that is faulty on CS00024 (see
[`cs00024-t36-diagnosis.md`](cs00024-t36-diagnosis.md)). The remote
consumer of `SYNC_B` remains an unresolved drawing boundary.

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

The Monitor images share a per-block checksum convention distinct from
EktaSoft's single block-1 sum: eight stored bytes at `0003h..000Ah`, block
0 covering `0004h..07FFh` and blocks 1-7 covering their full 2 KiB. This
is the convention that diagnoses jmon22's corrupt blocks
([`jmon22-reconstruction.md`](jmon22-reconstruction.md)); jmon33 passes
all eight (byte-verified), independently validating it against a healthy
image. Monitor boot is a short in-place sequence (checksum verification,
PIT and PPI init) followed by copying ROM `3F40h..3FFFh` to
`FF40h..FFFFh` and dispatching through that vector region. Maintained
annotated disassemblies of both Monitor images live in
[`../disasm/`](../disasm/README.md).

## Checksum status

The block-1 convention (additive sum of `000Bh..07FFh` stored at `000Ah`,
verified by the boot routine at `03E0h`) is documented in
[`cosim-runtime-reference.md`](cosim-runtime-reference.md). All five
official images pass. #0043 stores stale `F2h` against computed `57h` —
the fingerprint of a post-build modification that never regenerated the
checksum. The vendored binary is preserved unmodified; `cosim/trace.c`
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
