#!/usr/bin/env python3
"""Guard D105.10 H as an unresolved logic input, never the -5 V supply."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"
DSN = ROOT / "kicad/juku.dsn"
SES = ROOT / "kicad/juku.ses"
HDL = ROOT / "hdl/juku_top.v"
REPORT = ROOT / "docs/d105-h-boundary.md"

board_spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
h_net = board_spec["nets"].get("D105_10_H", {})
m5_net = board_spec["nets"].get("M5V_DERIVED", {})
checks: list[tuple[str, bool, str]] = []
checks.append(("H is a singleton D105.10 boundary",
               h_net.get("nodes") == [["D105", "10"]], str(h_net.get("nodes"))))
checks.append(("Derived -5 V excludes D105.10",
               ["D105", "10"] not in m5_net.get("nodes", []), str(m5_net.get("nodes"))))
checks.append(("Derived -5 V remains a power net", m5_net.get("power") is True,
               str(m5_net.get("power"))))

for label, path in (("Source PCB", SOURCE), ("Routed PCB", ROUTED)):
    board = pcbnew.LoadBoard(str(path))
    footprint = board.FindFootprintByReference("D105")
    pad = next(item for item in footprint.Pads() if item.GetNumber() == "10")
    position = pad.GetPosition()
    touching = [track for track in board.Tracks()
                if any(endpoint.x == position.x and endpoint.y == position.y
                       for endpoint in (track.GetStart(), track.GetEnd()))]
    checks.append((f"{label} assigns D105.10 to H", pad.GetNetname() == "D105_10_H",
                   pad.GetNetname()))
    checks.append((f"{label} has no routed segment on D105.10", not touching,
                   str(len(touching))))

dsn = DSN.read_text(encoding="utf-8")
checks.append(("DSN assigns singleton D105-10 to H",
               "(net D105_10_H\n      (pins D105-10)" in dsn and
               "E5-1 D105-10 D1-11" not in dsn, "kicad/juku.dsn"))
ses = SES.read_text(encoding="utf-8")
m5_start = ses.index('(net "M5V_DERIVED"')
m5_end = ses.find('\n      (net "', m5_start + 1)
m5_route = ses[m5_start:m5_end if m5_end >= 0 else len(ses)]
checks.append(("SES M5V route no longer terminates at D105.10",
               "344400 -2116850" not in m5_route, "kicad/juku.ses"))
hdl = HDL.read_text(encoding="utf-8")
checks.append(("HDL exposes H as an independent low-default boundary",
               "tri0 d105_h;" in hdl and ".b4(d105_h)" in hdl and
               ".b4(1'b0)" not in hdl, "hdl/juku_top.v"))

status = "D105 H BOUNDARY CORRECTED / SOURCE UNRESOLVED" if all(ok for _, ok, _ in checks) else "D105 H BOUNDARY FAILED"
lines = ["# D105 pin-10 H boundary", "", f"Status: **{status}**", "",
         "The full-resolution `.006` sheet draws a named off-sheet `H` arrow into",
         "D105 pin 10, a К155ЛА3 TTL logic input. A full-resolution sheet-2",
         "supply table also contains `H (−5)`, disproving the earlier claim that no",
         "H supply legend exists. Equating the two would put −5 V on a TTL input,",
         "so this is retained as a revision/notation conflict rather than a supply",
         "connection. The former connection also masked D2's used PROM output.", "",
         "The correction removes D105.10 from −5 V in board JSON, source PCB, routed",
         "PCB, DSN, SES, and HDL. This exposes one honest −5 V airwire in the",
         "derived routed snapshot instead of hiding it through D105.10; replacement",
         "copper remains a fabrication blocker. `H` remains a",
         "singleton target-revision boundary;",
         "the simulation low is an unresolved-input default that preserves the former",
         "constant-low gate behavior, not a claim that H is a supply. The deep cosim",
         "forces CPU `ready=1`, so it cannot constrain this WAIT input.", "",
         "| Check | Result | Evidence |", "| --- | --- | --- |"]
for name, ok, evidence in checks:
    lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | `{evidence}` |")
lines += ["", "A `.037` dump supplies D2 truth but cannot identify the source or timing of",
          "`H`. Both are required before releasing the physical WAIT chain. The routed",
          "snapshot must also regain a DRC-clean −5 V connection before fabrication.",
          "", "## Rejected local copper repairs", "",
          "KiCad DRC trials closed the airwire with nearby independent vias, but none",
          "was electrically legal:", "",
          "- a via at `(37.0,212.0)` shorts D105.9 `D2_WAIT_RAW` and conflicts with",
          "  `PHI2TTL`;",
          "- a left detour through `(31.0,210.4985)` crosses `D105_MRD_INV`, shorts",
          "  `RAM_OUT_EN`, and violates D13.4/`PHI2` clearance;",
          "- vias at the retained route near `(35.5722,198.5991)` remain too close to",
          "  `PHI2TTL`, while right-side front-copper detours cross `RESIN`, GND, or",
          "  the E3 control routing.", "",
          "Those candidates were rejected and the routed board restored to its guarded",
          "one-airwire state. Do not reinstate the original D105.10 junction or adopt a",
          "jumper/larger reroute without documenting it as a target-revision measurement",
          "or explicit Tier-1/2 redesign."]
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(status)
raise SystemExit(0 if status.startswith("D105 H BOUNDARY CORRECTED") else 1)
