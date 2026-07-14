#!/usr/bin/env python3
"""Generate the firmware/PROM gap ledger."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "firmware-gap-ledger.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def reconstructed_cell(path: str, expected_size: int) -> tuple[str, bool]:
    artifact = ROOT / path
    if not artifact.exists():
        return "missing", False
    size_ok = artifact.stat().st_size == expected_size
    return f"`{path}` ({artifact.stat().st_size} bytes, SHA256 `{sha256(artifact)}`)", size_ok


def marker(path: str, *needles: str) -> bool:
    text = read(path)
    return all(needle in text for needle in needles)


def main() -> int:
    d2_cell, d2_image_ok = reconstructed_cell(
        "ref/physical-proms/validated/d2_037.raw.bin", 256
    )
    d6_cell, d6_ok = reconstructed_cell(
        "ref/physical-proms/validated/d6_038.raw.bin",
        256,
    )
    d8_cell, d8_ok = reconstructed_cell(
        "ref/physical-proms/validated/d8_039.raw.bin",
        32,
    )
    d94_cell, d94_image_ok = reconstructed_cell(
        "ref/physical-proms/validated/d94_092.raw.bin", 32
    )
    d15_cell, d15_ok = reconstructed_cell(
        "ref/eprom-images/d15_ekta37_low.bin", 8192
    )
    d16_cell, d16_ok = reconstructed_cell(
        "ref/eprom-images/d16_ekta37_high.bin", 8192
    )
    bios = ROOT / "roms/ekta37.bin"
    d15 = ROOT / "ref/eprom-images/d15_ekta37_low.bin"
    d16 = ROOT / "ref/eprom-images/d16_ekta37_high.bin"
    eprom_roundtrip_ok = (
        d15_ok
        and d16_ok
        and bios.exists()
        and d15.read_bytes() + d16.read_bytes() == bios.read_bytes()
    )
    eprom_report_ok = marker(
        "docs/eprom-programming-images.md",
        "TIER-1/2 FUNCTIONAL IMAGES READY / PHYSICAL DUMPS PENDING",
        "`U_D15`, `HALF=0`",
        "`U_D16`, `HALF=1`",
        "not dumps of the original D15/D16 devices",
    ) and exists("scripts/export_eprom_pair.py")
    d2_text = read("docs/d2-reconstruction-constraints.md")
    d2_ok = (
        "Status: **D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**" in d2_text
        and d2_image_ok
    )
    d94_ok = marker(
        "docs/d94-reconstruction-constraints.md",
        "Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**",
        "all five address inputs are explicit continuity boundaries",
        "validated/d94_092.raw.bin",
    ) and d94_image_ok
    re3_lineage_ok = marker(
        "docs/re3-firmware-inspection.md",
        "D94 `.092`",
        "neither scanned table represents those parts",
    )
    fallback_report_ok = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "HISTORICAL D8 FALLBACK RETAINED / PHYSICAL PROM TABLES ADOPTED",
        "05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39",
        "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0",
    )
    rt4_validator_ok = marker(
        "docs/rt4-dump-acquisition.md",
        "PHYSICAL D2/D6 TABLES VALIDATED",
        "*.raw.bin",
        "D94 `.092` requires a",
        "separate К155РЕ3 reader",
    ) and exists("scripts/validate_rt4_dump.py")
    re3_validator_ok = marker(
        "docs/prom-dump-procedure.md",
        "scripts/validate_re3_dump.py",
        "Raw levels are the authoritative dump",
        "repeat-mismatched RE3 rows",
    ) and exists("scripts/validate_re3_dump.py") and exists("tools/re3_dumper/re3_dumper.ino")

    rows = [
        [
            "D2",
            "К556РТ4",
            "`ДГШ5.106.037`",
            "READY/bus-control PROM",
            d2_cell,
            "`docs/d2-reconstruction-constraints.md`; `docs/d2-physical-dump-and-continuity.md`",
            "programming-disk comparison or independent future read",
        ],
        [
            "D6",
            "К556РТ4",
            "`ДГШ5.106.038`",
            "memory decode PROM",
            d6_cell,
            "`ref/physical-proms/README.md`",
            "independent-reader or programming-disk comparison",
        ],
        [
            "D8",
            "К155РЕ3",
            "`ДГШ5.106.039`",
            "ROM-socket pager PROM",
            d8_cell,
            "`ref/physical-proms/README.md`",
            "programming-disk comparison or independent future read",
        ],
        [
            "D94",
            "К155РЕ3",
            "`ДГШ5.106.092`",
            "FDC control/decode PROM",
            d94_cell,
            "`docs/d94-reconstruction-constraints.md`",
            "programming-disk comparison plus D4-D7 destinations, D104.10 receiver-output continuity, pull-up resistor identities, and the guarded D29.4/IORD recheck",
        ],
        [
            "D15",
            "M2764/2764",
            "repository EktaSoft BIOS split",
            "BIOS low 8 KiB",
            d15_cell,
            "`docs/eprom-programming-images.md`",
            "repeat physical D15 dump for Tier-3 truth",
        ],
        [
            "D16",
            "M2764/2764",
            "repository EktaSoft BIOS split",
            "BIOS high 8 KiB",
            d16_cell,
            "`docs/eprom-programming-images.md`",
            "repeat physical D16 dump for Tier-3 truth",
        ],
    ]

    checks = [
        ("D2 validated physical raw image exists and is 256 bytes", d2_image_ok),
        ("D6 validated physical raw image exists and is 256 bytes", d6_ok),
        ("D8 validated physical raw image exists and is 32 bytes", d8_ok),
        ("D94 validated physical raw image exists and is 32 bytes", d94_image_ok),
        ("D15 functional image exists and is 8192 bytes", d15_ok),
        ("D16 functional image exists and is 8192 bytes", d16_ok),
        ("D15+D16 round-trip exactly to roms/ekta37.bin", eprom_roundtrip_ok),
        ("D15/D16 split and non-dump provenance are documented", eprom_report_ok),
        ("D2 physical table and continuity are guarded", d2_ok),
        ("D94 physical table is adopted while continuity stays guarded", d94_ok),
        (".113/.117 RE3 scans are guarded as not D8/D94", re3_lineage_ok),
        ("Historical fallback report adopts all physical PROM tables", fallback_report_ok),
        ("Repeated RT4 dump validation procedure is available", rt4_validator_ok),
        ("Repeated RE3 dump validation procedure is available", re3_validator_ok),
    ]
    status = "PROM GAP LEDGER READY / DUMP TRUTH PENDING" if all(ok for _, ok in checks) else "PROM GAP LEDGER FAILED"

    lines = [
        "# Firmware gap ledger",
        "",
        f"Status: **{status}**",
        "",
        "This generated ledger is the single-page burnability view for the",
        "small PROMs that still matter to replica and Tier-3 preservation work.",
        "It separates boot-validated functional fallbacks from dumped factory",
        "truth. A reconstructed fallback may be useful for Tier 1/2 bring-up,",
        "but a programming-disk file or repeated physical dump wins when it",
        "arrives.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_firmware_gap_ledger.py",
        "```",
        "",
        "## PROM Matrix",
        "",
        "| Ref | Part | Programmed drawing | Role | Burnable repo fallback | Guard | Next truth source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in rows)
    lines.extend(
        [
            "",
            "## Evidence Checks",
            "",
            "| Check | Result |",
            "| --- | --- |",
        ]
    )
    lines.extend(table_row([name, "PASS" if ok else "FAIL"]) for name, ok in checks)
    lines.extend(
        [
            "",
            "## Practical Burn Rule",
            "",
            "- D2, D6, D8, and D94 have validated physical raw tables; D15/D16",
            "  still use the deterministic `ekta37` EPROM split.",
            "- D2 is preservation-strength within current evidence: three captures",
            "  validate identically and include a separate power cycle. D6 also has three",
            "  matching preserved captures including a separate power cycle.",
            "- D15/D16 are deterministic Tier-1/2 functional images, not physical",
            "  device dumps. Program them as low/high 8 KiB respectively and",
            "  retain programmer verification records.",
            "- Never substitute the older D2-as-I/O-decode behavioral table; D9 is",
            "  the chip-select decoder and D2 is the separate `.037` READY/wait PROM.",
            "- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`",
            "  or D94 `.092`; they are lineage evidence, not matching processor",
            "  module programming tables.",
            "- D94 content and all A0-A4 input destinations are owner-closed. Its",
            "  enable source, D4-D7 far destinations, D104.10, pull-up identities, guarded D29.4/IORD recheck, and apparently pull-up-only D0 resistor identity remain unresolved",
            "  connectivity boundaries and still block an FDC hardware release.",
            "",
            "## Required External Closure",
            "",
            "- Locate the Baltijets programming-disk files referenced by doc 007.",
            "- Compare the validated D2/D6 tables against Baltijets programming files",
            "  if recovered; use it as independent corroboration of D8/D94 as well.",
            "- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;",
            "  preserve raw pin-level and active-low asserted tables separately.",
            "- Preserve future D8/D94 serial captures with `scripts/validate_re3_dump.py`;",
            "  the adopted D94 table still requires complete input/enable/output continuity.",
            "- Repeatedly read physical D15/D16 and compare their concatenation",
            "  with `roms/ekta37.bin`; preserve any stable mismatch as a variant.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {rel(REPORT)}")
    return 0 if status.startswith("PROM GAP LEDGER READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
