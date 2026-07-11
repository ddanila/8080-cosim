#!/usr/bin/env python3
"""Audit extraction of the photographed ДГШ5.109.009 СБ sheet 1."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "ref/photos/dgsh5-109-009-sb"
PHOTO_README = PHOTO_DIR / "README.md"
BODGE = ROOT / "ref/photos/juku-pcb-2/BODGE-TRIAGE.md"
PLAN = ROOT / "PLAN.md"
WIRE_TABLE_PDF = ROOT / "ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf"
WIRE_TABLE_MD = ROOT / "ref/schematics/dgsh5-109-009-sb-wire-table.md"
REPORT = ROOT / "docs/assembly-drawing-extraction.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def marker(text: str, *needles: str) -> bool:
    return all(needle in text for needle in needles)


def main() -> int:
    photos = sorted(PHOTO_DIR.glob("PXL_20260711_*.jpg"))
    photo_text = read(PHOTO_README)
    bodge_text = read(BODGE)
    plan_text = read(PLAN)
    kicad_python = subprocess.run(
        [str(ROOT / "scripts/find-kicad-python.sh")],
        cwd=ROOT, text=True, capture_output=True,
    ).stdout.strip() or "/usr/bin/python3"
    placement = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_fdc_cluster_placement.py")],
        cwd=ROOT, text=True, capture_output=True,
    )

    real_jpegs = all(path.read_bytes()[:3] == b"\xff\xd8\xff" and path.stat().st_size > 1_000_000 for path in photos)
    indexed = len(photos) == 26 and all(path.stem.replace(".MP", "")[-9:] in photo_text for path in photos)
    checks = [
        (
            "All 26 photographed sheet-1 views are local, real JPEGs, and indexed",
            indexed and real_jpegs,
            "`ref/photos/dgsh5-109-009-sb/`",
        ),
        (
            "Factory solder-side cuts/patches are protected as designed operations",
            marker(bodge_text, "Factory solder-side cuts and patches", "D56", "D15", "D14", "D11", "150", "159"),
            "`BODGE-TRIAGE.md`; Вид В photos 114626340/114633498/114638730",
        ),
        (
            "D94/D100/D98 retain the corrected horizontal assembly posture",
            placement.returncode == 0,
            "final `kicad/juku.kicad_pcb`; `kicad/check_fdc_cluster_placement.py`",
        ),
        (
            "Cable geometry is recorded from the drawing",
            marker(photo_text, "X8", "300 mm", "X9", "400 mm", "poz. 151 shielded cable"),
            "assembly-photo README",
        ),
        (
            "Factory wires 17 and 18 carry documented S1 far ends without conflation",
            marker(bodge_text, "| 17 |", "X2/D27 top band", "А:17 - S1:1", "| 18 |", "D98/D96/D99/D97 quadrant", "А:18 - S1:2", "do not conflate with wire 17"),
            "sheets 2-5 wire table rows 11/12 plus owner continuity follow-up",
        ),
        (
            "Connection-table sheets 2-6 are adopted and transcribed",
            WIRE_TABLE_PDF.exists() and WIRE_TABLE_MD.exists()
            and marker(read(WIRE_TABLE_MD), "ДУБЛИКАТ", "S1:1", "S1:2", "X9:14")
            and marker(plan_text, "sheets 2-6", "таблица соединений"),
            "`ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`; `ref/schematics/dgsh5-109-009-sb-wire-table.md`",
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = "SHEETS 1-6 ADOPTED / WIRE-TABLE PIN MAPPING PENDING" if ok else "ASSEMBLY DRAWING EXTRACTION FAILED"

    lines = [
        "# ДГШ5.109.009 СБ extraction audit",
        "",
        "Status date: **2026-07-11**.",
        "",
        f"Status: **{status}**",
        "",
        "This generated audit turns the photographed factory assembly drawing into",
        "guarded project evidence. Sheet 1 proves component posture, mounting/cable",
        "details, and factory cut/patch operations; sheets 2-6 (ДУБЛИКАТ scan)",
        "document the wire/cable connection table and change registration. Neither",
        "is promoted as a copper netlist.",
        "",
        "## Extraction checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines += [row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in checks]
    lines += [
        "",
        "## Photograph inventory",
        "",
        "| File | Bytes | SHA256 |",
        "| --- | ---: | --- |",
    ]
    for path in photos:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(row([path.name, path.stat().st_size, f"`{digest}`"]))
    if WIRE_TABLE_PDF.exists():
        digest = hashlib.sha256(WIRE_TABLE_PDF.read_bytes()).hexdigest()
        lines += [
            "",
            "## Connection-table scan (sheets 2-6)",
            "",
            "| File | Bytes | SHA256 |",
            "| --- | ---: | --- |",
            row([WIRE_TABLE_PDF.name, WIRE_TABLE_PDF.stat().st_size, f"`{digest}`"]),
            "",
            "Transcription: `ref/schematics/dgsh5-109-009-sb-wire-table.md`.",
        ]
    lines += [
        "",
        "## Release interpretation",
        "",
        "- Preserve the electrical result of the factory D56/D15/D14/D11 modifications.",
        "- Keep D94/D100/D98 horizontal during the source-PCB reroute.",
        "- Wires 17/18 far ends are documented at S1:1/S1:2; confirm continuity and pin mapping before promotion.",
        "- Map each wire-table А:N point to a package pin before board-model promotion; the table gives point numbers, not pins.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
