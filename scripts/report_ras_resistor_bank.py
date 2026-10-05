#!/usr/bin/env python3
"""Guard and report the photo-registered R49-R56 RAS resistor bank."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/ras-resistor-bank-registration.json"
BOARD_JSON = ROOT / "kicad/juku.board.json"
GENERATOR = ROOT / "kicad/gen_kicad_pcb.py"
REPORT = ROOT / "docs/ras-resistor-bank.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row(items: list[str]) -> str:
    return "| " + " | ".join(items) + " |"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    generator = GENERATOR.read_text(encoding="utf-8")
    chips = {chip["ref"]: chip for chip in board["chips"]}

    expected_order = ["R56", "R52", "R55", "R51", "R54", "R50", "R53", "R49"]
    expected_values = {**{f"R{i}": "75" for i in range(49, 53)},
                       **{f"R{i}": "5,1к" for i in range(53, 57)}}
    placements = evidence["placements"]
    checks: list[tuple[str, bool, str]] = []

    source_hashes_ok = True
    for source in evidence["sources"]:
        path = ROOT / source["path"]
        actual = sha256(path) if path.is_file() else "missing"
        ok = actual == source["sha256"]
        source_hashes_ok &= ok
    checks.append(("All registered sources match SHA256", source_hashes_ok,
                   f"{len(evidence['sources'])} drawing/photo artifacts"))

    order_ok = evidence["top_to_bottom"] == expected_order
    order_ok &= sorted(placements) == sorted(expected_order)
    ys = [float(placements[ref]["centre_mm"][1]) for ref in expected_order]
    order_ok &= all(a < b for a, b in zip(ys, ys[1:]))
    checks.append(("Drawing refdes order matches the target photo column", order_ok,
                   "R56/R52, R55/R51, R54/R50, R53/R49"))

    geometry_ok = evidence["footprint"]["orientation_deg"] == 90
    geometry_ok &= abs(float(evidence["footprint"]["lead_span_mm"]) - 10.16) < 1e-9
    geometry_ok &= all(abs(float(placements[ref]["centre_mm"][0]) - 221.0) < 1e-9
                       for ref in expected_order)
    checks.append(("Registered geometry is the vertical 10.16 mm bank", geometry_ok,
                   "x=221.0 mm; eight independently recorded centres"))

    values_ok = all(chips.get(ref, {}).get("value") == value
                    and placements[ref]["value"] == value
                    for ref, value in expected_values.items())
    checks.append(("Target case markings are encoded as values", values_ok,
                   "R49-R52=75 Ω; R53-R56=5.1 kΩ"))

    provenance_ok = all("registered target-board photos" in
                        chips.get(ref, {}).get("prov", {}).get("refdes", "")
                        for ref in expected_order)
    checks.append(("Board provenance cites the target-board registration", provenance_ok,
                   "all eight board-JSON components"))

    generator_ok = "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal" in generator
    generator_ok &= all(f"'{ref}':({placements[ref]['centre_mm'][0]:.1f},"
                        f"{placements[ref]['centre_mm'][1]:.1f},90)" in generator
                        for ref in expected_order)
    generator_ok &= 'if ref == "C69"' not in generator and 'if ref == "R52"' not in generator
    checks.append(("PCB generator text contains the registered placements and footprint",
                   generator_ok, "registered footprint name and coordinates"))

    ok = all(check[1] for check in checks)
    lines = [
        "# R49-R56 RAS resistor bank",
        "",
        f"Status: **{'PLACEMENT / VALUES CLOSED' if ok else 'REGISTRATION FAILED'}**",
        "",
        "The `.006` assembly drawing fixes the bank/refdes order. Registered target-board",
        "component views show the same eight populated vertical bodies, while the reflected",
        "solder panorama corroborates the drilled column. The red bodies directly read `75Ω`",
        "and the tan bodies directly read `5K1`. The source model encodes R49-R52",
        "as 75 Ω and R53-R56 as 5.1 kΩ.",
        "",
        "## Command",
        "",
        "Run from the repository root with Python 3 (standard library only).",
        "The command replaces this report with the registered-evidence check results,",
        "then exits nonzero if any check fails.",
        "",
        "```sh",
        "python3 scripts/report_ras_resistor_bank.py",
        "```",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if passed else "FAIL", detail])
                 for name, passed, detail in checks)
    lines.extend([
        "",
        "## Registered top-to-bottom order",
        "",
        "| Order | Ref | Centre (mm) | Orientation | Lead span | Marking | Encoded value | Role |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ])
    for index, ref in enumerate(expected_order, 1):
        item = placements[ref]
        role = "RAS termination to GND" if ref in {"R53", "R54", "R55", "R56"} else "D53 series output"
        lines.append(row([
            str(index), ref,
            f"{item['centre_mm'][0]:.1f}, {item['centre_mm'][1]:.1f}",
            "90°", f"{evidence['footprint']['lead_span_mm']:.2f} mm",
            item["marking"], item["value"], role,
        ]))
    lines.extend([
        "",
        "## Scope",
        "",
        "This guard validates the registered source hashes, recorded order/geometry,",
        "board values and provenance markers, and selected PCB-generator text.",
        "It does not rerun image registration, inspect PCB output, execute DRC or",
        "measure resistor values and loaded RAS timing. The table's circuit roles",
        "come from the sheet-2 ladder; connectivity is checked separately by",
        "the [memory timing report](memory-timing-boundary.md).",
        "",
        "The separate source-PCB check requires KiCad's `pcbnew` Python module:",
        "",
        "```sh",
        "/usr/bin/python3 kicad/check_ras_resistor_bank.py",
        "```",
        "",
        "Use the Python interpreter that provides `pcbnew` on your installation.",
        "This checks the eight centres, orientation, lead span, values and pad widths,",
        "plus C69 pad widths; it does not inspect routed copper or run DRC.",
        "",
        "Source record: [bank registration](../ref/photos/juku-pcb-2/ras-resistor-bank-registration.json).",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("RAS RESISTOR BANK: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
