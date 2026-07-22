# D15/D16 EPROM programming images

Status: **ADOPTED THIRD-SOURCE EKTA 3.7 IMAGES READY**

These deterministic 2764 programming images are split from the repository's
boot-validated 16 KiB `roms/ekta37.bin`. They are functional replica inputs,
not direct reads of the photographed D15/D16 devices. Their bytes are independently
preserved as the adopted third-source archival pair; the absent `.087/.041`
filename cross-reference is provenance nuance rather than a content gate.

## Reproduce

```sh
python3 scripts/export_eprom_pair.py
cd ref/eprom-images && sha256sum -c SHA256SUMS
```

## Mapping and artifacts

| Socket | HDL mapping | Source range | Size | Programming image | SHA256 |
| --- | --- | --- | ---: | --- | --- |
| D15 | `U_D15`, `HALF=0` | `0x0000-0x1fff` | 8192 | `ref/eprom-images/d15_ekta37_low.bin` | `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596` |
| D16 | `U_D16`, `HALF=1` | `0x2000-0x3fff` | 8192 | `ref/eprom-images/d16_ekta37_high.bin` | `35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817` |

Source image: `roms/ekta37.bin` (16384 bytes), SHA256
`fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`.

The exporter verifies that concatenating D15 then D16 reproduces the source
byte-for-byte. The socket order follows `hdl/juku_top.v`: D15 is the low 8 KiB
and D16 is the high 8 KiB. Program each file into a compatible 2764/M2764 or
electrically suitable 27C64-class device after confirming programmer support,
pinout, blank check, and device voltage requirements; perform a programmer
verify pass after writing.

## Socket and device decision

Use 2764/M2764-compatible 8 KiB x 8 DIP-28 devices for D15 and D16. A 27C64
substitute is acceptable for the functional build only when its datasheet and
programmer selection match the same read-mode pinout and supply limits.

| Pin | 2764 read-mode role | Board connection |
| ---: | --- | --- |
| 1 | VPP | +5 V (`P5V`) |
| 14 | VSS | ground (`GND`) |
| 20 | /CE | per-socket D8 pager select |
| 22 | /OE | memory-read strobe |
| 26 | NC on M2764; compatibility tie | +5 V (`P5V`) |
| 27 | /PGM | +5 V (`P5V`) for read mode |
| 28 | VCC | +5 V (`P5V`) |

The exporter guards these five power/programming pins for all eight physical
D15-D22 sockets, not only the two populated devices. Pins 2-13, 15-19, 21,
23-25 retain the standard A0-A12/D0-D7 mapping recorded in
`kicad/juku.board.json`. Programming voltage and pulse requirements come from
the exact device selected in the programmer and must never be applied through
the board socket.

## Provenance boundary

- These files inherit the public preservation provenance and rights caveat in
  `roms/README.md`.
- Keep physical board reads under the separately documented
  `proms/m2764_d15.bin` and `proms/m2764_d16.bin` names, with board, socket,
  date, programmer, and repeat-read provenance.
- Compare future physical dumps with `ekta37.bin` and preserve a stable mismatch
  as a possible BIOS variant. It does not invalidate the adopted archival pair.
