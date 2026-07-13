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
PCB_GENERATOR = ROOT / "kicad/gen_kicad_pcb.py"
SOURCE_PCB = ROOT / "kicad/juku.kicad_pcb"
BOARD_SPEC = ROOT / "kicad/juku.board.json"
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
    fdc_row_placement = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_d28_d106_photo_placement.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    mux_placement = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_d95_d101_photo_placement.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    lower_passive_placement = subprocess.run(
        [kicad_python, str(ROOT / "kicad/report_fdc_lower_assembly_placement.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    upper_passive_placement = subprocess.run(
        [kicad_python, str(ROOT / "kicad/report_fdc_upper_assembly_placement.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    switch_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_factory_switch_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    r94_landing = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_r94_landing.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    x9_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x9_offboard_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    x8_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x8_offboard_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    x3_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x3_offboard_landings.py")],
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
            "D106/D28/D96 row follows registered owner-photo spacing",
            fdc_row_placement.returncode == 0,
            "two-sided D106/D28 fits; D96 component fit; `kicad/check_d28_d106_photo_placement.py`",
        ),
        (
            "D101 follows its registered package-centre offset from D95",
            mux_placement.returncode == 0,
            "shared component photo; D95/D101 fits; `kicad/check_d95_d101_photo_placement.py`",
        ),
        (
            "Lower FDC passive identities follow the registered factory drawing",
            lower_passive_placement.returncode == 0,
            "five photo-fitted IC anchors; `kicad/report_fdc_lower_assembly_placement.py`",
        ),
        (
            "Upper-row C12/C9 placements follow adjacent fitted IC centres",
            upper_passive_placement.returncode == 0,
            "D94/D100/D98 drawing interpolation; `kicad/report_fdc_upper_assembly_placement.py`",
        ),
        (
            "Cable geometry is recorded from the drawing",
            marker(photo_text, "X8", "300 mm", "X9", "400 mm", "poz. 151 shielded cable"),
            "assembly-photo README",
        ),
        (
            "Factory wires 17 and 18 carry documented S1 far ends without conflation",
            marker(bodge_text, "| 17 |", "200358952", "A17.1", "| 18 |", "Validated component and solder fits", "А:18 - S1:2", "do not conflate with wire 17"),
            "sheets 2-5 wire table rows 11/12 plus accepted two-sided/photo-package evidence",
        ),
        (
            "Bracket-mounted S1 is distinguished from PCB wire landings А:17/А:18",
            marker(bodge_text, "S1 itself is mounted on the top connector bracket", "two-pin PCB header", "А:17", "А:18")
            and marker(read(WIRE_TABLE_MD), "S1 is bracket-mounted", "D98.7", "former generated two-pin", "S1 header"),
            "sheet-1 top-bracket view; owner photo 200402344; sheets 2-5 rows 11/12",
        ),
        (
            "Bracket-mounted S1 is excluded from generated PCB footprints",
            marker(read(PCB_GENERATOR), "OFF_BOARD = {", "'S1'", "must never become a PCB header footprint")
            and '(property "Reference" "S1"' not in read(SOURCE_PCB)
            and marker(plan_text, "excluded from", "generated PCB", "fictitious on-board S1 header", "is removed"),
            "`kicad/gen_kicad_pcb.py`; generated `kicad/juku.kicad_pcb`; PLAN source-PCB correction",
        ),
        (
            "Dedicated А:17 landing is present on RES_RC in the board spec and source PCB",
            marker(read(BOARD_SPEC), '"ref": "A17"', '"A17",', '"RES_RC"')
            and switch_landings.returncode == 0,
            "two-sided owner photos; `kicad/juku.board.json`; `kicad/check_factory_switch_landings.py`",
        ),
        (
            "R94 is modeled as 220 ohms from D98.3 with its far endpoint unresolved",
            marker(read(BOARD_SPEC), '"ref": "R94"', '"value": "220"', '"D98_Y1_R94"')
            and r94_landing.returncode == 0,
            "`.009` assembly drawing; owner component photo; `kicad/check_r94_landing.py`",
        ),
        (
            "X9 is schematic-only and its reversed ribbon uses PCB landings A45-A58",
            x9_landings.returncode == 0
            and marker(read(WIRE_TABLE_MD), "X9 row is now promoted", "A45", "A58", "schematic-only"),
            "sheets 4-5 X9 wire table; `kicad/check_x9_offboard_landings.py`",
        ),
        (
            "X8 is schematic-only and its six-conductor cable uses PCB landings A59-A62",
            x8_landings.returncode == 0
            and marker(read(WIRE_TABLE_MD), "X8 cable is now promoted", "A59", "A62", "schematic-only"),
            "sheet 2 X8 power-cable table; `kicad/check_x8_offboard_landings.py`",
        ),
        (
            "X3 is schematic-only and its cable uses photo-fitted PCB landings A21-A32",
            x3_landings.returncode == 0
            and marker(read(WIRE_TABLE_MD), "X3 is now promoted", "A21", "A32", "schematic-only"),
            "sheet 1 circuit; sheets 4-5 cable table; owner photos; `kicad/check_x3_offboard_landings.py`",
        ),
        (
            "X4 first five legacy circuit exits are explicitly dispositioned",
            marker(
                read(WIRE_TABLE_MD),
                "1 / 401", "D28.8", "2 / 402", "D28.10", "3 / 403", "D28.12",
                "4 / 404", "D28.4", "5 / 405", "D28.2",
                "does not yet promote", "X4.6-X4.23",
            ),
            "`.006` sheet-1 exit codes 401-405; `.009` target continuity still required",
        ),
        (
            "D26 PC2-PC6 retain the five source-drawn D28 sections and the sixth is unused",
            marker(
                read(BOARD_SPEC),
                '"MEM_MODE0"', "directly into D28 input pin11",
                '"MEM_MODE1"', "directly into D28 input pin13",
                '"FDC_DDEN"', "directly into D28 input pin9",
                '"D26_PC5_RN_IN"', '[["D26", "12"], ["D28", "3"]]',
                '"D26_PC6_STOP_IN"', '[["D26", "11"], ["D28", "1"]]',
                "the D28 output destination remains a target-board continuity boundary",
                "The D28.4 target-board output destination remains a separate continuity boundary",
                "The D28.2 target-board output destination remains a separate continuity boundary",
                '"D28", "5"', '"D28", "6"',
                "omits the sixth section pins5/6 as explicit NCs",
            ),
            "`.006` sheet-1 direct conductors + К155ЛН3 pin contract + pinned MAME Port-C roles",
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
        "- Wire 17 is promoted as A17.1/А:17 to S1:1; wire 18 is promoted as D98.7/А:18 to S1:2.",
        "- S1 remains an off-board bracket component and is excluded from generated PCB footprints.",
        "- Map each wire-table А:N point to a package pin before board-model promotion; the table gives point numbers, not pins.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
