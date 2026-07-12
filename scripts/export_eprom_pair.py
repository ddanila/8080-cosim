#!/usr/bin/env python3
"""Export the verified 16 KiB BIOS as distinct D15/D16 2764 images."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "roms" / "ekta37.bin"
OUT_DIR = ROOT / "ref" / "eprom-images"
D15 = OUT_DIR / "d15_ekta37_low.bin"
D16 = OUT_DIR / "d16_ekta37_high.bin"
MANIFEST = OUT_DIR / "SHA256SUMS"
REPORT = ROOT / "docs" / "eprom-programming-images.md"
HALF_SIZE = 8192


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    source = SOURCE.read_bytes()
    if len(source) != 2 * HALF_SIZE:
        raise SystemExit(
            f"{SOURCE.relative_to(ROOT)} must be 16384 bytes, got {len(source)}"
        )

    d15 = source[:HALF_SIZE]
    d16 = source[HALF_SIZE:]
    if d15 + d16 != source:
        raise SystemExit("internal split/round-trip check failed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    D15.write_bytes(d15)
    D16.write_bytes(d16)
    MANIFEST.write_text(
        "\n".join(
            [
                f"{sha256(d15)}  {D15.name}",
                f"{sha256(d16)}  {D16.name}",
                f"{sha256(source)}  ../../roms/{SOURCE.name}",
                "",
            ]
        ),
        encoding="ascii",
    )

    report = f"""# D15/D16 EPROM programming images

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
| D15 | `U_D15`, `HALF=0` | `0x0000-0x1fff` | {len(d15)} | `ref/eprom-images/{D15.name}` | `{sha256(d15)}` |
| D16 | `U_D16`, `HALF=1` | `0x2000-0x3fff` | {len(d16)} | `ref/eprom-images/{D16.name}` | `{sha256(d16)}` |

Source image: `roms/{SOURCE.name}` ({len(source)} bytes), SHA256
`{sha256(source)}`.

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
"""
    REPORT.write_text(report, encoding="utf-8")
    print(
        f"Wrote {D15.relative_to(ROOT)}, {D16.relative_to(ROOT)}, "
        f"{MANIFEST.relative_to(ROOT)}, and {REPORT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
