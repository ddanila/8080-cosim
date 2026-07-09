#!/usr/bin/env python3
"""Inspect the tracked К155РЕ3 factory programming-table excerpts."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "ref" / "firmware"
REPORT = ROOT / "docs" / "re3-firmware-inspection.md"
SHA_FILE = REF / "SHA256SUMS"


ARTIFACTS = [
    "BAS0.HEX",
    "BAS1.HEX",
    "BAS2.HEX",
    "BAS3.HEX",
    "JUKUROM0.HEX",
    "JUKUROM1.HEX",
    "Juku_К155РЕ3_firmware.pdf",
    "README.md",
    "re3_dgsh5.106.113.hex",
    "re3_dgsh5.106.117.hex",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_hex_table(path: Path) -> list[int]:
    values: list[int] = []
    for token in path.read_text().split():
        values.append(int(token, 16))
    if len(values) != 32:
        raise ValueError(f"{path} has {len(values)} bytes, expected 32")
    if any(value < 0 or value > 0xFF for value in values):
        raise ValueError(f"{path} contains a byte outside 0x00..0xFF")
    return values


def expected_113() -> list[int]:
    table = [0xFF] * 32
    table[0x14:0x18] = [0x07, 0x0B, 0x0D, 0x0E]
    return table


def expected_117() -> list[int]:
    table = [0xFF] * 32
    for start, value in [(0x08, 0x07), (0x0C, 0x0B), (0x10, 0x0D), (0x14, 0x0E)]:
        table[start : start + 4] = [value] * 4
    return table


def one_cold_ok(values: list[int]) -> bool:
    return all(value in {0xFF, 0x07, 0x0B, 0x0D, 0x0E} for value in values)


def row_ranges(values: list[int]) -> str:
    ranges: list[str] = []
    start = 0
    while start < len(values):
        end = start
        while end + 1 < len(values) and values[end + 1] == values[start]:
            end += 1
        if start == end:
            ranges.append(f"{start:02X}:{values[start]:02X}")
        else:
            ranges.append(f"{start:02X}-{end:02X}:{values[start]:02X}")
        start = end + 1
    return ", ".join(ranges)


def write_sha_file() -> None:
    lines = [f"{sha256(REF / name)}  {name}" for name in ARTIFACTS]
    SHA_FILE.write_text("\n".join(lines) + "\n")


def main() -> int:
    table_113 = parse_hex_table(REF / "re3_dgsh5.106.113.hex")
    table_117 = parse_hex_table(REF / "re3_dgsh5.106.117.hex")
    d8_fallback = parse_hex_table(ROOT / "ref" / "reconstructed-proms" / "d8_re3_rom_pager_reconstructed.hex")
    checks = [
        ("`.113` byte count is 32", len(table_113) == 32),
        ("`.117` byte count is 32", len(table_117) == 32),
        ("`.113` matches the scanned sparse 14h-17h one-cold walk", table_113 == expected_113()),
        ("`.117` matches the scanned 08h-17h four-row one-cold dwell", table_117 == expected_117()),
        ("Both tables use only `FF`, `07`, `0B`, `0D`, `0E`", one_cold_ok(table_113) and one_cold_ok(table_117)),
        ("The two scanned tables are distinct", table_113 != table_117),
        ("Neither scanned table matches the reconstructed D8 pager fallback", table_113 != d8_fallback and table_117 != d8_fallback),
    ]
    status = "PASS" if all(ok for _, ok in checks) else "REGRESSION"

    write_sha_file()

    rows = []
    for name in ARTIFACTS:
        path = REF / name
        rows.append((name, path.stat().st_size, sha256(path)))

    lines = [
        "# К155РЕ3 firmware inspection",
        "",
        f"Status: **{status}**",
        "",
        "This generated report preserves the tracked owner-scan РЕ3 programming",
        "tables under `ref/firmware/` and keeps their role bounded. The files are",
        "real factory programming-table excerpts, but current board evidence says",
        "they are **not** the processor-module D8 `.039` or D94 `.092` contents.",
        "",
        "## Command",
        "",
        "```sh",
        "scripts/report_re3_firmware_inspection.py",
        "sync/reference_artifact_check.sh",
        "```",
        "",
        "## Shape Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for label, ok in checks:
        lines.append(f"| {label} | {'PASS' if ok else 'FAIL'} |")

    lines.extend(
        [
            "",
            "## Tables",
            "",
            "| Programmed drawing | Primary use | Row summary | SHA256 |",
            "| --- | --- | --- | --- |",
            f"| `ДГШ5.106.113` | `ДГШ5.106.103` family | `{row_ranges(table_113)}` | `{sha256(REF / 're3_dgsh5.106.113.hex')}` |",
            f"| `ДГШ5.106.117` | `ДГШ5.106.103` family | `{row_ranges(table_117)}` | `{sha256(REF / 're3_dgsh5.106.117.hex')}` |",
            "",
            "## Artifact Hashes",
            "",
            "| File | Size | SHA256 |",
            "| --- | ---: | --- |",
        ]
    )
    for name, size, digest in rows:
        lines.append(f"| `{name}` | {size} | `{digest}` |")

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- `.113` and `.117` are tracked because they came from the owner-scan",
            "  `Juku_К155РЕ3_firmware.pdf` and are useful PROM-lineage evidence.",
            "- They are not exported as D8/D94 burnable fallbacks: the processor-module",
            "  parts list names D8 as `ДГШ5.106.039`, and the `.009` FDC revision adds",
            "  D94 as `ДГШ5.106.092`; neither table is present in these scans.",
            "- The tables' `FF` idle plus one-cold `07/0B/0D/0E` shape is consistent",
            "  with a timing/phase-select PROM family, not with the two-chip BIOS D8",
            "  socket pager required by the traced processor module.",
            "- The boot-validated D8 fallback remains",
            "  `ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.*` until a",
            "  physical D8 dump or programming-disk `.039` table appears.",
            "- Tier 3 still requires repeated physical PROM reads or programming-disk",
            "  files for D2/D6/D8/D94 and any video/DRAM timing РЕ3.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {SHA_FILE.relative_to(ROOT)}")
    if status != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
