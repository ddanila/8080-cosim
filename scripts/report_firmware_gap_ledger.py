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
    d6_cell, d6_ok = reconstructed_cell(
        "ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.bin",
        256,
    )
    d8_cell, d8_ok = reconstructed_cell(
        "ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin",
        32,
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
        "No reconstructed D2 fallback is exported" in d2_text
        and (
            "Status: **D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**" in d2_text
            or "Status: **D2 RECONSTRUCTION PARTIALLY TRACED / DUMP REQUIRED**" in d2_text
            or "Status: **D2 INPUTS TRACED / DUMP REQUIRED**" in d2_text
        )
    )
    d94_ok = marker(
        "docs/d94-reconstruction-constraints.md",
        "Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**",
        "D94.10-D94.14 map to `BA11..BA15`",
        "no `.092` / `106.092` artifact",
    )
    re3_lineage_ok = marker(
        "docs/re3-firmware-inspection.md",
        "D94 `.092`",
        "neither table is present",
    )
    fallback_report_ok = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED",
        "No D2 image is exported",
        "No D94 image is exported",
    )
    rt4_validator_ok = marker(
        "docs/rt4-dump-acquisition.md",
        "HOST VALIDATION READY / PHYSICAL DUMP PENDING",
        "*.raw.bin",
        "D94 `.092` requires a",
        "separate К155РЕ3 reader",
    ) and exists("scripts/validate_rt4_dump.py")
    re3_validator_ok = marker(
        "docs/prom-dump-procedure.md",
        "scripts/validate_re3_dump.py",
        "Raw levels are the authoritative dump",
        "repeat-mismatched RE3 rows",
    ) and exists("scripts/validate_re3_dump.py")

    rows = [
        [
            "D2",
            "К556РТ4",
            "`ДГШ5.106.037`",
            "bus-arbitration/wait PROM",
            "no",
            "`docs/d2-reconstruction-constraints.md`",
            "programming-disk file or repeated physical dump",
        ],
        [
            "D6",
            "К556РТ4",
            "`ДГШ5.106.038`",
            "memory decode PROM",
            d6_cell,
            "`docs/reconstructed-prom-fallbacks.md`",
            "replace/check fallback against programming-disk file or dump",
        ],
        [
            "D8",
            "К155РЕ3",
            "`ДГШ5.106.039`",
            "ROM-socket pager PROM",
            d8_cell,
            "`docs/reconstructed-prom-fallbacks.md`",
            "replace/check fallback against programming-disk file or dump",
        ],
        [
            "D94",
            "К155РЕ3",
            "`ДГШ5.106.092`",
            "FDC control/decode PROM",
            "no",
            "`docs/d94-reconstruction-constraints.md`",
            "programming-disk file or repeated dump plus complete D94.15 and D93.2/.4 strobe-branch continuity",
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
        ("D6 fallback exists and is 256 bytes", d6_ok),
        ("D8 fallback exists and is 32 bytes", d8_ok),
        ("D15 functional image exists and is 8192 bytes", d15_ok),
        ("D16 functional image exists and is 8192 bytes", d16_ok),
        ("D15+D16 round-trip exactly to roms/ekta37.bin", eprom_roundtrip_ok),
        ("D15/D16 split and non-dump provenance are documented", eprom_report_ok),
        ("D2 no-burn boundary is constrained", d2_ok),
        ("D94 no-burn boundary is constrained", d94_ok),
        (".113/.117 RE3 scans are guarded as not D8/D94", re3_lineage_ok),
        ("Fallback report excludes D2 and D94 exports", fallback_report_ok),
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
            "- For functional bring-up without factory truth, the D6 and D8",
            "  reconstructed PROM images and the D15/D16 `ekta37` EPROM split",
            "  are currently burnable from the repo.",
            "- D15/D16 are deterministic Tier-1/2 functional images, not physical",
            "  device dumps. Program them as low/high 8 KiB respectively and",
            "  retain programmer verification records.",
            "- Do not burn any older D2-as-I/O-decode behavioral table as physical",
            "  D2; D9 is the current chip-select decoder and D2 remains a separate",
            "  `.037` bus/wait PROM with fully traced inputs but unknown contents.",
            "- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`",
            "  or D94 `.092`; they are lineage evidence, not matching processor",
            "  module programming tables.",
            "- D94 is not reconstructable from current automatic evidence: the",
            "  board identity and address inputs are known, but enable, outputs,",
            "  and contents remain absent.",
            "",
            "## Required External Closure",
            "",
            "- Locate the Baltijets programming-disk files referenced by doc 007.",
            "- Or repeatedly dump the socketed D2/D6 RT4 and D8/D94 RE3 parts from",
            "  hardware, then compare D6/D8 against `ref/reconstructed-proms/` and",
            "  replace the HDL/fallbacks only if the dump provenance is stronger.",
            "- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;",
            "  preserve raw pin-level and active-low asserted tables separately.",
            "- Validate D8/D94 serial captures with `scripts/validate_re3_dump.py`;",
            "  a sound D94 dump still requires complete enable/output continuity.",
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
