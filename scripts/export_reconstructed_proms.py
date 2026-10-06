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
            "Historical D8 pager hypothesis; retained for byte comparison, not programming.",
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
        "`ref/physical-proms/validated/` now supply the HDL table contents.",
        "For physical programming, confirm the device, programmer, and bit",
        "representation using [the PROM procedure](prom-dump-procedure.md).",
        "",
        "## Command",
        "",
        "Run from the repository root. Check retained files before the exporter",
        "rewrites the historical image and its checksum manifest.",
        "",
        "```sh",
        "(cd ref/reconstructed-proms && sha256sum -c SHA256SUMS)",
        "python3 scripts/export_reconstructed_proms.py",
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
            "- Adopted D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` hashes and",
            "  capture provenance belong to [the physical-PROM record](../ref/physical-proms/README.md).",
            "- Physical D8 differs from the historical reconstruction at 19 rows.",
            "  Physical D6 supersedes its earlier reconstructed image.",
            "- HDL models raw zero as an open-collector sink and raw one or disabled",
            "  output as release into the consumer pull-up/TTL environment.",
            "- D94's exact .009 CS7 enable source is drawing-closed; its D0 hidden",
            "  load remains a [board-evidence boundary](d94-reconstruction-constraints.md).",
            "- No video/DRAM timing image is exported. The remaining shared-DRAM",
            "  slot schedule requires traced control paths; D94 is FDC control, not",
            "  a missing video PROM. See [the timing audit](video-slot-timing-audit.md).",
            "- Do not program the historical reconstruction now that repeated physical",
            "  D8 reads exist.",
            "",
            "## HDL Consistency Guard",
            "",
            "`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the",
            "current `hdl/devices.v` modules. With modeled pull-ups and enables asserted,",
            "it compares all 256 D2/D6 rows and all 32 D8/D94 rows against the retained",
            "`.raw.hex` tables. Separate D6/D8 probes check disabled release and the",
            "row-0 sink pattern. It does not sweep every enable combination or measure",
            "physical voltage/timing. D2/D6 models and the test read the same retained",
            "tables; D8/D94 models use decode cases checked against those tables.",
            "Independent dump identity and BIN/HEX agreement require the physical-PROM",
            "guards. This test does not validate the historical D8 reconstruction.",
            "",
            "CI also reruns `scripts/export_reconstructed_proms.py` and fails if the",
            "generated files or this report are stale.",
            "",
            "## Diff Procedure",
            "",
            "When a dump arrives, compare size and SHA256 first, then byte-diff against",
            "the matching validated physical table. Preserve raw reads and provenance",
            "before interpreting a mismatch. A stable different table may identify a",
            "board variant; do not replace the adopted target-board table until socket",
            "identity, address/output mapping and electrical compatibility are verified.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {OUTDIR.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
