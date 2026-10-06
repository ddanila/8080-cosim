#!/usr/bin/env python3
"""Record owner-closed D93.40 +12 V continuity and its photo registration."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
REPORT = ROOT / "docs/d93-pin40-photo-chase.md"


def pad(board: pcbnew.BOARD, ref: str, number: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    return next(item for item in footprint.Pads() if item.GetNumber() == number)


def mm(position: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def main() -> int:
    spec = json.loads(BOARD_JSON.read_text())
    d93 = next(chip for chip in spec["chips"] if chip["ref"] == "D93")
    p12_nodes = {tuple(node) for node in spec["nets"]["P12V"]["nodes"]}
    observations = {}
    with ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["refdes"] == "D93" and row["pin"] == "40":
                observations[row["endpoint_id"]] = row

    board = pcbnew.LoadBoard(str(PCB))
    target = pad(board, "D93", "40")
    tx, ty = mm(target.GetPosition())
    candidates = []
    for footprint in board.GetFootprints():
        for item in footprint.Pads():
            if item.GetNetname() != "P12V":
                continue
            if footprint.GetReference() == "D93" and item.GetNumber() == "40":
                continue
            x, y = mm(item.GetPosition())
            candidates.append((math.hypot(x - tx, y - ty), footprint.GetReference(), item.GetNumber(), x, y))
    candidates.sort()

    checks = [
        ("D93 is the physical КР1818ВГ93", d93.get("type") == "VG93_FDC"),
        ("D93 pin 40 has the VDD_12V role", d93.get("pins", {}).get("40") == "VDD_12V"),
        ("Source model assigns D93.40 to P12V", ("D93", "40") in p12_nodes),
        ("Source PCB assigns D93.40 to P12V", target.GetNetname() == "P12V"),
        ("Component and solder observations are preserved", set(observations) == {"seed-component-D93-40", "seed-solder-D93-40"}),
        ("Nearest P12V anchors are D14.8 and D32.8", [(ref, pin) for _, ref, pin, _, _ in candidates[:2]] == [("D14", "8"), ("D32", "8")]),
    ]
    ok = all(result for _, result in checks)
    status = "OWNER CONTINUITY CLOSED / D93.40 ON P12V" if ok else "D93 PIN40 CLOSURE FAILED"
    component = observations.get("seed-component-D93-40", {})
    solder = observations.get("seed-solder-D93-40", {})
    lines = [
        "# D93 pin-40 power-trace chase", "", f"Status: **{status}**", "",
        "The physical D93 is the populated КР1818ВГ93. The maintenance close-up",
        "temporarily removes it from its socket and provides the clearest pin-40",
        "registration; this is not evidence that the design omits the controller.", "",
        "## Reproduction", "",
        "Run from the repository root using Python with KiCad's `pcbnew` module.",
        "The command overwrites this report; it reads the board and text records,",
        "so materialized photograph bytes are not required.", "",
        "```sh", "/usr/bin/python3 kicad/report_d93_pin40_photo_chase.py", "```", "",
        "The guard checks D93 identity/pin role, JSON/source-PCB net assignment,",
        "the two observation IDs, and geometric distances to P12V pads. It does",
        "not check photo hashes, inspect copper continuity, or repeat the owner",
        "measurement. Nearby modeled anchors are optional corroboration targets.", "",
        "## Registered evidence", "",
        f"- Component observation: `{component.get('image', '-')}` at `({component.get('x_px', '-')}, {component.get('y_px', '-')})` px.",
        f"- Solder observation: `{solder.get('image', '-')}` at `({solder.get('x_px', '-')}, {solder.get('y_px', '-')})` px.",
        f"- Source-PCB D93.40 pad centre: `({tx:.3f}, {ty:.3f})` mm on `P12V`.",
        "- The photographs register the pad but do not prove its far copper.",
        "- Direct owner continuity on 2026-07-15 proves the P12V merge.", "",
        "## Guard checks", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | {'PASS' if result else 'FAIL'} |" for name, result in checks)
    lines += [
        "", "## Optional corroboration", "",
        "The nearest modeled +12 V anchors are D14.8 and D32.8. For an independent",
        "board comparison, meter D93.40 to either anchor and to A60.1 or X8.3.",
        "Their proximity in source-PCB geometry does not establish owner-board copper.", "",
        "D93.40 is already closed to P12V by owner continuity; these are optional",
        "cross-checks rather than outstanding release probes.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(status)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
