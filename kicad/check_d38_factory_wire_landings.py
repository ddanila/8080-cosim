#!/usr/bin/env python3
"""Hold A8B/A9B until corrected D38-side wire landings are proved.

The former D38 cross-face fit associated a D92.1/ROE white-wire joint with
A9B/SYNC. This guard must not pass that withdrawn candidate as a landing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
REVIEW = ROOT / "ref/photos/juku-pcb-2/a9b-corrected-trace-review.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"

records = {item["point"]: item for item in json.loads(LANDINGS.read_text())["points"]}
endpoints = {
    terminal: next(item for item in records[point]["endpoints"] if item["terminal"] == terminal)
    for point, terminal in ((8, "A8B"), (9, "A9B"))
}
review = json.loads(REVIEW.read_text())
board = pcbnew.LoadBoard(str(BOARD))
errors: list[str] = []
for number, net in (("8", "STSTB_D38"), ("12", "SYNC")):
    footprint = board.FindFootprintByReference("D38")
    pad = footprint.FindPadByNumber(number) if footprint else None
    if pad is None or pad.GetNetname() != net:
        errors.append(f"D38.{number} must remain on {net}")

old_a9 = endpoints["A9B"].get("board_fit_evidence", {})
if old_a9.get("joint_px") == [2286, 2450] or old_a9.get("via_px") == [2288, 2298]:
    errors.append("withdrawn D92.1/ROE white-wire joint is still fitted as A9B")
observation = endpoints["A9B"].get("candidate_owner_observation", "")
if "D92.1/ROE" not in observation or "(2025,2063)" not in observation:
    errors.append("A9B registry lost corrected ROE/SYNC distinction")
if "D92.1/ROE" not in review.get("decision", ""):
    errors.append("A9B review lost the D92.1/ROE retraction")

if errors:
    raise SystemExit("D38 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))

pending = [terminal for terminal, item in endpoints.items() if item.get("board_mm") is None]
if pending:
    raise SystemExit(
        "D38 FACTORY LANDINGS: HOLD — " + ", ".join(pending)
        + " lack proved D38-side wire landings; former A9B white joint favors A13B/ROE"
    )

raise SystemExit(
    "D38 FACTORY LANDINGS: FAIL — new A8B/A9B coordinates require a fresh "
    "same-hole, copper, and wire-continuity guard before release"
)
