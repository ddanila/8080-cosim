#!/usr/bin/env python3
"""Reconstruct the photographed ДГШ5.106.106 Д1 2 KiB ROM table."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "ref/firmware/BAS0.HEX"
JBASIC = ROOT / "roms/jbasic11.bin"
OUT_DIR = ROOT / "ref/reconstructed-firmware"
OUT_BIN = OUT_DIR / "dgsh5-106-106-d1.bin"
OUT_HEX = OUT_DIR / "dgsh5-106-106-d1.hex"
OUT_SUMS = OUT_DIR / "SHA256SUMS"
REPORT = ROOT / "docs/dgsh5-106-106-rom-table.md"

EXPECTED = {
    ARCHIVE: "fc8514a64e9524738936e65dffd48f90d17762576a743a1fb84f1dbe65b9a34e",
    JBASIC: "ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60",
    ROOT / "ref/photos/dgsh5-106-106-d1/sheet1_PXL_20260718_122548761.jpg": "a20fc8d7ce66e4ab8814a75a8951893ec8989c0a58905eed8e12dff910c97f33",
    ROOT / "ref/photos/dgsh5-106-106-d1/sheet2_PXL_20260718_122557171.jpg": "3c27e3f5af18d9db36bfc6725f679ec8cfe09ebbc3b28e9173d2712bf48b5453",
    ROOT / "ref/photos/dgsh5-106-106-d1/sheet3_PXL_20260718_122601894.jpg": "b966e2039bac3646aa2c8242276d657381430256f3dc8c915935d75038e5f76b",
}
EXPECTED_IMAGE_SHA256 = "2cd7398b167ceebc256614b9de4cd8953b858e4f35722e57723559d990fc80a6"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_archive() -> bytes:
    tokens = ARCHIVE.read_text(encoding="ascii", errors="ignore").split()
    values = [int(token, 16) for token in tokens if len(token) == 2]
    if len(values) != 2048:
        raise SystemExit(f"BAS0 archive has {len(values)} bytes, expected 2048")
    return bytes(values)


def main() -> int:
    for path, expected in EXPECTED.items():
        actual = sha256(path.read_bytes())
        if actual != expected:
            raise SystemExit(f"source changed: {path.relative_to(ROOT)}: {actual}")

    archive = parse_archive()
    jbasic = JBASIC.read_bytes()[:2048]
    differences = [
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(archive, jbasic))
        if old != new
    ]
    if differences != [(0x021A, 0xA1, 0x21)]:
        raise SystemExit(f"BAS0/JBASIC divergence changed: {differences}")

    # Factory sheet 1 row 0210, column A visibly reads 21. The two digital
    # artifacts agree everywhere else, so this single primary-source decision
    # yields the complete printed 0000-07FF image.
    image = bytearray(archive)
    image[0x021A] = 0x21
    image = bytes(image)
    if image != jbasic or sha256(image) != EXPECTED_IMAGE_SHA256:
        raise SystemExit("reconstructed table does not equal jbasic11 first 2 KiB")
    if image[:3] != bytes((0xC3, 0x07, 0x01)):
        raise SystemExit("factory reset vector is not JMP 0107h")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIN.write_bytes(image)
    OUT_HEX.write_text(
        "\n".join(
            f"{address:04X}: " + " ".join(f"{value:02X}" for value in image[address:address + 16])
            for address in range(0, len(image), 16)
        ) + "\n",
        encoding="ascii",
    )
    OUT_SUMS.write_text(
        f"{sha256(OUT_BIN.read_bytes())}  {OUT_BIN.name}\n"
        f"{sha256(OUT_HEX.read_bytes())}  {OUT_HEX.name}\n",
        encoding="ascii",
    )

    context = image[0x0210:0x0220]
    lines = [
        "# `ДГШ5.106.106 Д1` ROM-table reconstruction", "",
        "Status: **FACTORY 2 KiB IMAGE RECONSTRUCTED / ONE ARCHIVE TYPO CORRECTED**", "",
        "The three photographed factory sheets cover `0000-07FF`. An existing",
        "archive transcription, `ref/firmware/BAS0.HEX`, supplies all 2,048",
        "candidate bytes. The independent `roms/jbasic11.bin` cartridge image",
        "agrees at 2,047 positions. The only difference is resolved directly from",
        "the photographed factory row, producing a byte-exact 2 KiB image.", "",
        "## Reproduce", "", "```sh", "python3 scripts/reconstruct_dgsh5_106_106.py", "```", "",
        "## Output", "",
        f"- Binary: `ref/reconstructed-firmware/dgsh5-106-106-d1.bin` ({len(image)} bytes)",
        f"- Readable hex: `ref/reconstructed-firmware/dgsh5-106-106-d1.hex`",
        "- Manifest: `ref/reconstructed-firmware/SHA256SUMS`",
        f"- SHA256: `{sha256(image)}`",
        "- Reset vector: `C3 07 01` = 8080 `JMP 0107h`", "",
        "The result equals `roms/jbasic11.bin[0000:0800]` exactly. This identifies",
        "the printed `.106.106` program as the first 2 KiB page of the preserved",
        "Juku BASIC 1.1 cartridge image; it is not one of the main-board D15/D16",
        "EktaSoft BIOS halves or a small D2/D6/D8/D94 PROM table.", "",
        "## Single divergence adjudication", "",
        "| Address | `BAS0.HEX` | `jbasic11.bin` | Factory photograph | Adopted |",
        "| ---: | ---: | ---: | ---: | ---: |",
        "| `021A` | `A1` | `21` | `21` | `21` |", "",
        "Factory sheet 1 (`sheet1_PXL_20260718_122548761.jpg`), row `0210`,",
        "column A visibly reads `21`. Its complete adopted row is:", "",
        "```text", "0210: " + " ".join(f"{value:02X}" for value in context), "```", "",
        "This is exactly the plan's diff-first method: matching bytes need no",
        "second manual transcription; the sole disagreement is hand-verified",
        "against primary evidence. The source hashes and exact one-byte mismatch",
        "are executable guards, so a changed archive cannot silently pass.", "",
        "## Guarded sources", "",
    ]
    lines.extend(
        f"- `{path.relative_to(ROOT)}` — SHA256 `{expected}`"
        for path, expected in EXPECTED.items()
    )
    lines += [
        "", "## Provenance boundary", "",
        "The factory listing is authoritative printed programming data, while the",
        "generated binary is a reconstruction rather than a physical-device read.",
        "A repeatable read of a device marked `.106.106` would be independent",
        "corroboration; any stable disagreement must be preserved as a variant.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_BIN.relative_to(ROOT)}")
    print(f"Wrote {OUT_HEX.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("DGSH5-106-106-RECONSTRUCTION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
