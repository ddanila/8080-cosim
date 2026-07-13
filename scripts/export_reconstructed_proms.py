#!/usr/bin/env python3
"""Preserve the historical D8 reconstruction for comparison."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "ref" / "reconstructed-proms"
REPORT = ROOT / "docs" / "reconstructed-prom-fallbacks.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def d8_byte(row: int) -> int:
    """D8 К155РЕ3 reconstructed ROM-socket pager row."""
    if 0x00 <= row <= 0x03:
        return 0xEF
    if 0x04 <= row <= 0x07:
        return 0xDF
    if 0x08 <= row <= 0x0B:
        return 0xF7
    if 0x0C <= row <= 0x0F:
        return 0xFB
    if 0x10 <= row <= 0x13:
        return 0xFD
    if 0x14 <= row <= 0x17:
        return 0xFE
    if row == 0x1B:
        return 0xEF
    if 0x1C <= row <= 0x1F:
        return 0xDF
    return 0xFF


def write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def write_hex(path: Path, data: bytes) -> None:
    path.write_text("".join(f"{byte:02X}\n" for byte in data))


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    images = [
        (
            "d8_re3_rom_pager_reconstructed",
            bytes(d8_byte(row) for row in range(32)),
            "D8 К155РЕ3 ROM-socket pager; byte values are active-low output rails.",
        ),
    ]

    rows: list[tuple[str, int, str, str]] = []
    for stem, data, _ in images:
        bin_path = OUTDIR / f"{stem}.bin"
        hex_path = OUTDIR / f"{stem}.hex"
        write_bytes(bin_path, data)
        write_hex(hex_path, data)
        rows.append((stem, len(data), sha256(data), sha256(hex_path.read_bytes())))

    sums = []
    for stem, data, _ in images:
        sums.append(f"{sha256(data)}  {stem}.bin")
        sums.append(f"{sha256((OUTDIR / f'{stem}.hex').read_bytes())}  {stem}.hex")
    (OUTDIR / "SHA256SUMS").write_text("\n".join(sums) + "\n")

    lines = [
        "# Reconstructed PROM fallback images",
        "",
        "Status: **HISTORICAL D8 FALLBACK RETAINED / PHYSICAL PROM TABLES ADOPTED**",
        "",
        "The D8 file records the former boot-oriented reconstruction for historical",
        "comparison only. Validated physical D2, D6, D8, and D94 tables under",
        "`ref/physical-proms/` now drive HDL and are the burnable PROM truth.",
        "",
        "## Command",
        "",
        "```sh",
        "scripts/export_reconstructed_proms.py",
        "sync/prom_fallback_check.sh",
        "```",
        "",
        "## Files",
        "",
        "| Stem | Size | BIN SHA256 | HEX SHA256 | Role |",
        "| --- | ---: | --- | --- | --- |",
    ]
    roles = {stem: role for stem, _, role in images}
    for stem, size, bin_sha, hex_sha in rows:
        lines.append(f"| `{stem}` | {size} | `{bin_sha}` | `{hex_sha}` | {roles[stem]} |")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- D2 `.037` has three validated captures including a separate power cycle;",
            "  authoritative raw SHA256 is",
            "  `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`.",
            "- D6 `.038` has three validated captures including a separate power cycle;",
            "  authoritative raw SHA256 is",
            "  `05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`.",
            "  This physical table supersedes the old reconstructed D6 image.",
            "- D8 `.039` physical raw SHA256 is",
            "  `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`.",
            "  It differs from `d8_re3_rom_pager_reconstructed.*` at 19 rows and",
            "  supersedes that artifact.",
            "- D94 `.092` physical raw SHA256 is",
            "  `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`.",
            "  HDL adopts its open-collector table; D94 enable/output continuity",
            "  remains a separate board-evidence boundary.",
            "- No video/DRAM timing РЕ3 image is exported. The exact slot/state timing",
            "  remains a dump/programming-disk dependency.",
            "- Do not program the historical reconstruction now that repeated physical",
            "  D8 reads exist.",
            "",
            "## Non-exported PROMs",
            "",
            "| PROM | Programmed drawing | Reason no fallback is emitted |",
            "| --- | --- | --- |",
            "| Video/DRAM timing РЕ3 | `ДГШ5.106.009` family | Timing truth is not derivable from current schematic/MAME evidence; needs dump or programming-disk table. |",
            "",
            "## HDL Consistency Guard",
            "",
            "`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the",
            "current `hdl/devices.v` modules and compares every exported row against the",
            "physical-table-backed D2/D6/D8/D94 logic. A passing guard means the",
            "validated physical files still match HDL; it does not validate the retained",
            "historical D8 reconstruction.",
            "",
            "CI also reruns `scripts/export_reconstructed_proms.py` and fails if the",
            "generated files or this report are stale.",
            "",
            "## Diff Procedure",
            "",
            "When a dump arrives, compare size and SHA256 first, then byte-diff against",
            "the matching `.bin` file. A mismatch is not automatically an error: the",
            "dump wins if its provenance and repeated reads are sound, and the HDL",
            "model should then be updated to match the silicon.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {OUTDIR.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
