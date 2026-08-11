# ekta37 ROM layout map

Status: hand-written analysis, 2026-08-11, of the pinned `roms/ekta37.bin`
(EktaSoft '88 Serial #0037, RomBios 3.43m, SHA256
`fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`).
Regions were attributed from four independent signals: filtered I/O-port
clustering, the monitor vector-table targets, byte-verified strings, and the
font identified by rendering its bytes as glyphs. Labels live in
[`../disasm/ekta37/ekta37.ctl`](../disasm/ekta37/ekta37.ctl).

Two boundaries organize the image. The **physical split** at `2000h` is the
D15/D16 chip edge. The **execution split** at `1800h` ends the in-place
code: everything above executes at `D800h..FFFFh` through memory-mode
banking, not a copy — MAME's driver shows modes 1/2 hardware-map ROM
`1800h-3FFFh` at `D800h-FFFFh` for reads while writes fall through to the
RAM underneath, which is the framebuffer (`D800h..FDA7h` for the 40x24
screen). The console code executes from mapped ROM at the very addresses
whose underlying RAM it paints.

| ROM range | Size | Share | Region |
| --- | ---: | ---: | --- |
| `0000-0016` | 23 B | 0.1% | Reset header: entry jump, block-1 checksum byte at `000Ah` |
| `0017-048F` | 1,145 B | 7.0% | Boot, banner & self-test: PIT raster init (`01D4h`), PPI setup, config screen, checksum verify |
| `0490-16FF` | 4,720 B | 28.8% | Console, keyboard & interrupt core: bitmap screen renderer, key-matrix decode, console device switching |
| `1700-17FF` | 256 B | 1.6% | **Free** (`FFh` fill, top of the in-place half) |
| `1800-1CFF` | 1,280 B | 7.8% | ROM monitor: service dispatcher (`1854h`), 15 commands `F D S X G M C E K T B R W P A`, prompt + dispatch tables (see [`juku-rom-monitor-commands.md`](juku-rom-monitor-commands.md)) |
| `1D02-2321` | 1,568 B | 9.6% | Character font: 196 glyphs x 8 bytes, crossing the chip boundary |
| `2325-29FF` | 1,755 B | 10.7% | Disk subsystem: Bootstrap v4.1 (banner `23C4h`), VG93/FDC driver (ports `1Ch-1Fh` cluster in `25xx-27xx`), FLOPPY/START/RWFLOPPY vector targets (`2565h/2482h/280Bh`), RamDisk service entry (`29B3h`) |
| `2A00-35FF` | 3,072 B | 18.8% | NetBios (Janet 1.2): entry `2AA2h`, protocol + prompts (`2C22h`), 8251 driver and handler install (`34xx-35xx`); see [`ekta37-netbios-notes.md`](ekta37-netbios-notes.md) |
| `3600-38FF` | 768 B | 4.7% | Expansion-bus device driver: off-board ports `F0h+` (sites `29B0h`, `357Ch-359Ch`, `36xx-38xx`); plausibly serves the RamDisk hardware — **hedged attribution** |
| `3900-3EB9` | 1,466 B | 8.9% | **Free** (`FFh` fill — usable at zero RAM cost: the relocated half already owns its runtime window) |
| `3EBA-3F4F` | 150 B | 0.9% | Tail, unattributed |
| `3F50-3FFF` | 176 B | 1.1% | Monitor vector table (runtime `FF50h`, the `EKDOS30.ASM` contract; boot-prompt `D` jumps here) |

Headlines: the school network is the largest single feature (~3 KiB, 19%),
half again the size of the whole disk subsystem (~1.8 KiB, 11%). The console
core dominates overall (~4.6 KiB, 29%) because a bitmap machine pays for its
own text rendering, including the 1.5 KiB font. Free space totals 1,722 B
(10.5%).

Precision: edges are exact where a landmark pins them (font, free fills,
vector table, disk/net entries); the console-core interior and the
network-region interior are aggregates rounded to page boundaries. The
expansion-driver attribution is the one hedged call. The command parser
references its dispatch table through a single `LXI H,D977h` at ROM `1923h`.

## Reproduction

```sh
# port clustering (region evidence)
python3 - <<'EOF'
rom = open("roms/ekta37.bin","rb").read()
THREE = {0xC3,0xC2,0xCA,0xD2,0xDA,0xE2,0xEA,0xF2,0xFA,0xCD,0xC4,0xCC,0xD4,
         0xDC,0xE4,0xEC,0xF4,0xFC,0x01,0x11,0x21,0x31,0x22,0x2A,0x32,0x3A}
TWO = {0x3E,0x06,0x0E,0x16,0x1E,0x26,0x2E,0x36,0xC6,0xCE,0xD6,0xDE,0xE6,
       0xEE,0xF6,0xFE,0xDB,0xD3}
for lo, hi, name in ((0x1C,0x1F,"FDC"), (0x08,0x0B,"USART"), (0xF0,0xFF,"expansion")):
    pages = sorted({i >> 8 for i in range(2, len(rom)-1)
                    if rom[i] in (0xD3, 0xDB) and lo <= rom[i+1] <= hi
                    and rom[i-1] not in THREE | TWO and rom[i-2] not in THREE})
    print(name, [f"{p:02X}" for p in pages])
EOF
```
