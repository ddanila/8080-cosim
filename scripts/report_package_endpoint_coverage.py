#!/usr/bin/env python3
"""Ensure every non-power board endpoint exists in its package pin contract."""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
OUT = ROOT / "docs/package-endpoint-coverage.md"


def main() -> None:
    board = json.loads(BOARD.read_text())
    chips = {chip["ref"]: chip for chip in board["chips"]}
    allowed_power = []
    invalid = []
    for net, entry in board["nets"].items():
        nodes = entry.get("nodes", []) if isinstance(entry, dict) else entry
        is_power = isinstance(entry, dict) and bool(entry.get("power"))
        for ref, pin in nodes:
            chip = chips.get(ref)
            if chip is None or str(pin) in chip.get("pins", {}):
                continue
            row = (ref, str(pin), net, chip["type"])
            (allowed_power if is_power else invalid).append(row)

    if invalid:
        details = "; ".join(f"{ref}.{pin}:{net}" for ref, pin, net, _ in invalid)
        raise SystemExit("PACKAGE ENDPOINT COVERAGE: FAIL: undeclared non-power endpoints: " + details)

    by_net = collections.Counter(net for _, _, net, _ in allowed_power)
    refs = {ref for ref, _, _, _ in allowed_power}
    invalid_nc = [
        (ref, str(pin)) for ref, pin in board.get("no_connects", [])
        if ref not in chips or str(pin) not in chips[ref].get("pins", {})
    ]
    if invalid_nc:
        details = "; ".join(f"{ref}.{pin}" for ref, pin in invalid_nc)
        raise SystemExit("PACKAGE ENDPOINT COVERAGE: FAIL: undeclared no-connect pins: " + details)
    checks = [
        ("Every known-chip non-power net endpoint is declared by its chip/package", not invalid),
        ("Every explicit no-connect exists in its chip/package", not invalid_nc),
        ("S1 off-board SPDT contact 3 is explicitly declared", chips["S1"]["pins"].get("3") == "P3"),
        ("Remaining undeclared endpoints belong only to tagged PCB power nets", all(board["nets"][net].get("power") for net in by_net)),
    ]
    lines = [
        "# Package endpoint coverage", "",
        "Status: **NON-POWER PACKAGE CONTRACTS COMPLETE**", "",
        "This guard reads `kicad/juku.board.json`. For net endpoints whose references",
        "exist in `chips`, it rejects undeclared pins unless the net is tagged `power`.",
        "It also rejects explicit no-connects absent from the chip pin contract.", "",
        "## Command", "", "```sh",
        "python3 scripts/report_package_endpoint_coverage.py", "```", "",
        "## Summary", "",
        f"- Undeclared non-power endpoints: `{len(invalid)}`",
        f"- Undeclared explicit no-connect pins: `{len(invalid_nc)}`",
        f"- Power endpoints outside board pin contracts: `{len(allowed_power)}` across `{len(refs)}` refs",
        "", "| Tagged power net | Endpoints outside board pin contracts |",
        "| --- | ---: |",
    ]
    lines.extend(f"| `{net}` | {count} |" for net, count in sorted(by_net.items()))
    lines.extend(["", "## Checks", "", "| Check | Result |", "| --- | --- |"])
    lines.extend(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in checks)
    lines.extend([
        "", "## Scope", "",
        "- Net endpoints with references absent from `chips` are skipped. Explicit",
        "  no-connects with unknown references are rejected.",
        "- This check does not find required pins omitted from both nets and",
        "  no-connects, validate package pin functions, or inspect HDL pinmaps.",
        "- Tagged power-net exceptions are counted; their voltage, routing and",
        "  electrical suitability are not validated here.",
        "- Spinoff boards, routed copper and physical continuity are outside this",
        "  report. Use their own package, LVS and manufacturing checks.",
    ])
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"PACKAGE ENDPOINT COVERAGE: PASS; nonpower=0, power-excluded={len(allowed_power)}")


if __name__ == "__main__":
    main()
