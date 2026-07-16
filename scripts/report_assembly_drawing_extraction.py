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
    d94_pullups = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_d94_pullups.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    d105_h = subprocess.run(
        [kicad_python, str(ROOT / "kicad/report_d105_h_boundary.py")],
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
    x6_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x6_offboard_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    x3_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x3_offboard_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    x4_landings = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_x4_offboard_landings.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    factory_wire_links = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_factory_wire_links.py")],
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
            "Factory local solder/copper details are guarded without treating position 150 as a cut",
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
            "D94 pull-up identities, values, and endpoints are source-modeled",
            d94_pullups.returncode == 0,
            "factory R87/R88/R89 labels/BOM plus registered component/solder/value photos; `kicad/check_d94_pullups.py`",
        ),
        (
            "X1.107B/-BLOCK/H and R1 are source-modeled",
            d105_h.returncode == 0,
            "native sheet 1 plus `.009` R1 placement and owner component photo; `kicad/report_d105_h_boundary.py`",
        ),
        (
            "Cable geometry is recorded from the drawing",
            marker(photo_text, "X8", "300 mm", "X9", "400 mm", "poz. 151 shielded cable"),
            "assembly-photo README",
        ),
        (
            "Board points А:17 and А:18 carry documented S1 far ends without conflation",
            marker(bodge_text, "11 / А:17", "200358952", "A17.1", "12 / А:18", "Validated component and solder fits", "А:18 - S1:2", "not the А:17 link"),
            "sheets 2-5 wire table rows 11/12 plus accepted two-sided/photo-package evidence",
        ),
        (
            "All ten on-board insulated links map conductor positions and А:N points to guarded endpoints",
            factory_wire_links.returncode == 0 and marker(
                read(WIRE_TABLE_MD),
                "conductor's position", "not", "board-point", "number",
                "| 3 | А:7 | D1.22 - D35.10 |", "| 14 | А:20 | D3.10 - A23.1 - X3.3 |",
                "`Д104`, not `Д14`", "separate D14.3/D3.11 `SER_TXD` net",
                "insulated", "assembly wire, not replacement PCB etch",
            ),
            "sheets 2-5 table; owner continuity; `kicad/check_factory_wire_links.py`",
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
            and marker(plan_text, "S1/X3/X4/X6/X8/X9", "intentionally excluded", "physical A-point", "cable landings"),
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
            "`.009` assembly drawing; four-view `r94-photo-exhaustion.json`; `kicad/check_r94_landing.py`",
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
            "X6 is bracket-mounted and its 12 cm cable uses surface landings A:3/A:4",
            x6_landings.returncode == 0
            and marker(read(WIRE_TABLE_MD), "А:3", "А:4", "marked return terminal", "x6-cable-registration.json"),
            "sheet 3 cable table; two owner-photo angles; `kicad/check_x6_offboard_landings.py`",
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
                "promotes all 23 board-edge landings", "X4.6-X4.23", "explicit boundaries",
            ),
            "`.006` sheet-1 exit codes 401-405; `.009` target continuity still required",
        ),
        (
            "X4 bracket harness has all 23 physical board landings",
            x4_landings.returncode == 0 and marker(
                read(BOARD_SPEC), '"ref": "X4"', '"ref":"AX401"', '"ref":"AX423"',
                '"X4_06_BOUNDARY"', '"X4_23_BOUNDARY"', '"X4_FF_N"', '"X4_STOP_N"',
            ),
            "`.009` sheets4-5 wires27-49; `kicad/check_x4_offboard_landings.py`",
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
                '"X4_FF_N"', '[["D28", "8"], ["AX401", "1"], ["X4", "1"]]',
                '"X4_REC_N"', '[["D28", "10"], ["AX402", "1"], ["X4", "2"]]',
                '"X4_PLAY_N"', '[["D28", "12"], ["AX403", "1"], ["X4", "3"]]',
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
    status = "SHEETS 1-6 AND WIRE-TABLE PIN MAPPING ADOPTED" if ok else "ASSEMBLY DRAWING EXTRACTION FAILED"

    lines = [
        "# ДГШ5.109.009 СБ extraction audit",
        "",
        "Status date: **2026-07-11**.",
        "",
        f"Status: **{status}**",
        "",
        "This generated audit turns the photographed factory assembly drawing into",
        "guarded project evidence. Sheet 1 proves component posture, mounting/cable",
        "details, and local solder/copper operations; sheets 2-6 (ДУБЛИКАТ scan)",
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
        "- Preserve the proved D15 cut and D14 local link; hold the registered D56/D11 callout fields until continuity closes them.",
        "- Keep D94/D100/D98 horizontal during the source-PCB reroute.",
        "- Keep D13/D105 right-facing and preserve R1 as the component-side 2 kΩ X1.107B/H pull-up.",
        "- Conductor 11 is promoted as A17.1/А:17 to S1:1; conductor 12 is promoted as D98.7/А:18 to S1:2.",
        "- S1 remains an off-board bracket component and is excluded from generated PCB footprints.",
        "- Preserve А:7-А:14 and А:19-А:20 as insulated assembly links; their guarded electrical mapping must not be mistaken for replacement PCB etch.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
