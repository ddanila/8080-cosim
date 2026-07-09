#!/usr/bin/env python3
"""Export boot-validated reconstructed PROM fallback images."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "ref" / "reconstructed-proms"
REPORT = ROOT / "docs" / "reconstructed-prom-fallbacks.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def d6_byte(row: int) -> int:
    """D6 К556РТ4 reconstructed memory decode row.

    Bit convention follows the HDL output comments in hdl/devices.v:
    D0=ROM_N, D1=RAM_N, D2=REV, D3=ROE_N.
    """
    ba15_14 = (row >> 6) & 0x3
    ba15_13 = (row >> 5) & 0x7
    ba15_11 = (row >> 3) & 0x1F
    mode0 = (row >> 2) & 0x1
    rom_region = ba15_14 == 0 if mode0 == 0 else ba15_11 >= 0x1B
    rom_n = 0 if rom_region else 1
    ram_n = 0 if not rom_region else 1
    rev = 0 if ba15_13 == 0 else 1
    roe_n = 0
    return rom_n | (ram_n << 1) | (rev << 2) | (roe_n << 3)


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
            "d6_rt4_memory_decode_reconstructed",
            bytes(d6_byte(row) for row in range(256)),
            "D6 К556РТ4 memory decode; low nibble uses D0=ROM_N, D1=RAM_N, D2=REV, D3=ROE_N.",
        ),
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
        "Status: **BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED**",
        "",
        "These files are programming fallbacks, not dumped factory truth. They are",
        "derived from the current boot-validated HDL/cosim behavior and should be",
        "replaced or checked against Baltijets programming-disk files or physical",
        "PROM dumps when those become available.",
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
            "- `d6_rt4_memory_decode_reconstructed.*` covers only the D6 memory decode",
            "  fallback. Its reset-mode overlay selects ROM for `0x0000..0x3FFF`.",
            "  It does not claim to be the dumped factory byte table.",
            "- `d8_re3_rom_pager_reconstructed.*` covers only the D8 ROM-socket pager",
            "  fallback for programmed drawing family `ДГШ5.106.039`.",
            "- No D2 image is exported. Current board metadata identifies D2 as a",
            "  К556РТ4 bus-arbitration/wait PROM (`ДГШ5.106.037`, dump pending) with",
            "  deferred nets. Older functional I/O-decode stand-ins must not be burned",
            "  as a physical D2 programming image.",
            "- No D94 image is exported. The current `re3_prom_092` HDL block is an",
            "  all-high inert stub for the unknown `ДГШ5.106.092` content.",
            "- No video/DRAM timing РЕ3 image is exported. The exact slot/state timing",
            "  remains a dump/programming-disk dependency.",
            "- Use these only for Tier 1/2 functional bring-up if no programming disk",
            "  or dump is available. Tier 3 still requires real dumps.",
            "",
            "## Non-exported PROMs",
            "",
            "| PROM | Programmed drawing | Reason no fallback is emitted |",
            "| --- | --- | --- |",
            "| D2 К556РТ4 | `ДГШ5.106.037` | Physical nets are deferred and current evidence treats it as a bus/wait PROM, not the functional I/O decoder. |",
            "| D94 К155РЕ3 | `ДГШ5.106.092` | Content is unknown; HDL uses an unconnected all-high placeholder. |",
            "| Video/DRAM timing РЕ3 | `ДГШ5.106.009` family | Timing truth is not derivable from current schematic/MAME evidence; needs dump or programming-disk table. |",
            "",
            "## HDL Consistency Guard",
            "",
            "`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the",
            "current `hdl/devices.v` modules and compares every exported row against the",
            "actual `decode_prom` and `re3_prom` logic. A passing guard means the files in",
            "`ref/reconstructed-proms/` still match the boot-validated HDL fallback logic.",
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
