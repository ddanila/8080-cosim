#!/usr/bin/env python3
"""Guard the exhausted sheet-1 chase for D30 section-B pins 8 and 11."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ref/schematics/p3_sheet1.png"
BOARD = ROOT / "kicad/juku.board.json"
REPORT = ROOT / "docs/d30-section-b-scan-chase.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nodes(spec: dict, net: str) -> set[tuple[str, str]]:
    return {tuple(item) for item in spec["nets"][net]["nodes"]}


def main() -> int:
    spec = json.loads(BOARD.read_text(encoding="utf-8"))
    r5 = next(chip for chip in spec["chips"] if chip["ref"] == "R5")
    r5_provenance = " ".join(map(str, r5.get("prov", {}).values()))
    checks = [
        ("D30.11 joins the measured D13.4/D105.2/D11.20 clock conductor",
         {("D30", "11"), ("D13", "4"), ("D105", "2"), ("D11", "20")} <= nodes(spec, "D13_4_D105_2")),
        ("D30.8 drives D29.7 on a dedicated measured conductor",
         nodes(spec, "D30_Q2N_D29_AIN7") == {("D30", "8"), ("D29", "7")}),
        ("D29.7 is removed from raw IOWR",
         ("D29", "7") not in nodes(spec, "IOWR")),
        ("Measured section-B D and /PRE pull-up is kept separate",
         nodes(spec, "D30B_D_PRE_N") == {("D30", "10"), ("D30", "12"), ("R5", "2")}),
        ("R5 provenance records the exact-sheet/physical-board conflict",
         "D30.4" in r5_provenance and "D30.10/.12" in r5_provenance
         and "continuity boundary" in r5_provenance),
        ("Measured /CLR path from D105.11 is kept separate",
         nodes(spec, "D105_MEMW_INV") == {("D105", "11"), ("D30", "13")}),
    ]
    failed = [name for name, passed in checks if not passed]
    if failed:
        raise SystemExit("D30 SECTION-B SCAN CHASE: FAIL: " + "; ".join(failed))

    lines = [
        "# D30 section-B sheet-1 scan chase", "",
        "Status: **OWNER CONTINUITY CLOSED / OLDER SCAN AMBIGUITY RETAINED**", "",
        "The full-resolution `.006` electrical sheet was re-read specifically for the two",
        "formerly unresolved D30 section-B conductors. This audit records why the scan",
        "alone was ambiguous and how direct target-board continuity closes both routes.", "", "## Source", "",
        f"- Image: `{SOURCE.relative_to(ROOT)}`",
        f"- SHA256: `{sha256(SOURCE)}`",
        "- Full image: `5150 x 3603` pixels",
        "- Primary inspection box: `x=950..2850, y=1200..2150`",
        "- West clock continuation box: `x=0..1700, y=1350..2100`", "",
        "## Result", "",
        "- D30.11 has a drawn westbound clock conductor. It crosses the vertical",
        "  D13.4/WR:19 route in the crowded gate field without a junction dot; the scan",
        "  therefore does not prove D30.11 on `D13_4_D105_2`, `D105_3`, or `WR:19`.",
        "- D30.8 has a drawn east/north departure. It traverses the dense memory/data",
        "  rail field, but no unique labeled destination or unambiguous junction survives",
        "  in this scan. Apparent alignment with a bus rail is not evidence for tying a",
        "  push-pull 7474 output to that bus.",
        "- D30.9 is omitted from the factory symbol and remains the already-recorded",
        "  explicit no-connect. The visible section-B output is D30.8, so it cannot be",
        "  dispositioned as an unused package half.",
        "- Direct owner continuity remains authoritative for D30.10/.12/R5 and",
        "  D105.11->D30.13; neither measured net is reopened by this older-sheet chase.", "",
        "Exact `.009` sheet 1 draws a +5 V resistor labeled R5 at D30.4, but the",
        "physical target board instead places R5 on D30.10/.12. The measured board",
        "wins: D30.4 remains a separate continuity boundary rather than being",
        "silently joined to +5 V through the drawing's conflicting reference.", "",
        "Direct owner continuity on the physical `.009` board now closes both routes:",
        "D30.11 reaches D105.2 on the D13.4/D11.20 clock conductor, and D30.8",
        "reaches D29.7. The latter supersedes the prior raw-IOWR assignment at D29.7.",
        "", "## Model guards", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | PASS |" for name, _ in checks)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("D30 SECTION-B SCAN CHASE: PASS; ambiguous routes rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
