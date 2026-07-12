# D15/D16 EPROM programming images

Status: **TIER-1/2 FUNCTIONAL IMAGES READY / PHYSICAL DUMPS PENDING**

These deterministic 2764 programming images are split from the repository's
boot-validated 16 KiB `roms/ekta37.bin`. They are functional replica inputs,
not dumps of the original D15/D16 devices and not Tier-3 factory truth.

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

## Provenance boundary

- These files inherit the public preservation provenance and rights caveat in
  `roms/README.md`.
- Keep physical board reads under the separately documented
  `proms/m2764_d15.bin` and `proms/m2764_d16.bin` names, with board, socket,
  date, programmer, and repeat-read provenance.
- A repeatable physical dump wins over these generated images for Tier-3
  historical claims. Compare its D15+D16 concatenation against `ekta37.bin`;
  preserve a mismatch as a possible BIOS variant until independently checked.
