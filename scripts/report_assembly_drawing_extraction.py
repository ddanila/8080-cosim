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
    placement = subprocess.run(
        ["/usr/bin/python3", str(ROOT / "kicad/check_fdc_cluster_placement.py")],
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
            marker(bodge_text, "Factory solder-side cuts and patches", "D56", "D15", "D4", "D11", "150", "159"),
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
            "Wire 17/18 reset-chain endpoint remains explicitly unresolved",
            marker(bodge_text, "17/18", "far endpoint unread", "reset-chain endpoint remains a boundary"),
            "owner continuity follow-up; no invented endpoint",
        ),
        (
            "Missing connection-table sheets 2-6 remain on the owner request list",
            marker(plan_text, "sheets 2-6", "таблица соединений", "Ask the owner"),
            "`PLAN.md` external evidence",
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = "SHEET 1 ADOPTED / CONNECTION TABLE SHEETS 2-6 REQUESTED" if ok else "ASSEMBLY DRAWING EXTRACTION FAILED"

    lines = [
        "# ДГШ5.109.009 СБ extraction audit",
        "",
        "Status date: **2026-07-11**.",
        "",
        f"Status: **{status}**",
        "",
        "This generated audit turns the photographed factory assembly drawing into",
        "guarded project evidence. Sheet 1 proves component posture, mounting/cable",
        "details, and factory cut/patch operations; it is not promoted as a copper",
        "netlist. The referenced connection table is on missing sheets 2-6.",
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
    lines += [
        "",
        "## Release interpretation",
        "",
        "- Preserve the electrical result of the factory D56/D15/D4/D11 modifications.",
        "- Keep D94/D100/D98 horizontal during the source-PCB reroute.",
        "- Do not infer the wire 17/18 destination from the assembly view alone.",
        "- Request sheets 2-6 before claiming factory wire-table closure.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
