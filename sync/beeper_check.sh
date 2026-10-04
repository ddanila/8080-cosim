#!/usr/bin/env bash
# Guard the digital beeper source: D57 (8253 #3) channel 1 must be programmable
# and toggle the traced SOUND net.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== HDL D57 SOUND channel check =="
iverilog -g2012 -o "$TMP/beeper_path_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/beeper_path_tb.v
out=$(vvp "$TMP/beeper_path_tb")
echo "$out"
if ! printf '%s\n' "$out" | grep -q "BEEPER-PATH: PASS"; then
  echo "BEEPER-CHECK: FAIL"
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
board = json.loads((root / "kicad" / "juku.board.json").read_text())
chips = {chip["ref"]: chip for chip in board["chips"]}
if chips.get("VD4", {}).get("value") != "КД521В":
    raise SystemExit("BEEPER-CHECK: target-photo VD4 designation mismatch")
expected = {
    "SOUND": [("D57", "13"), ("R90", "1")],
    "SND_BASE": [("R90", "2"), ("VD4", "2"), ("VT1", "3")],
    "SND_CLAMP": [("VD4", "1"), ("R91", "1")],
    "AVDC": [("R91", "2"), ("D26", "40")],
    "SND_OUT": [("VT1", "1"), ("R48", "1")],
    "SPKR": [("R48", "2")],
}

rows = []
ok = True
for name, nodes in expected.items():
    net = board["nets"].get(name)
    have = {tuple(node) for node in net.get("nodes", [])} if net else set()
    missing = [node for node in nodes if node not in have]
    passed = net is not None and not missing
    ok = ok and passed
    rows.append(
        "| `{}` | {} | {} |".format(
            name,
            "PASS" if passed else "FAIL",
            ", ".join(f"`{ref}.{pin}`" for ref, pin in nodes),
        )
    )

if not ok:
    raise SystemExit("BEEPER-CHECK: board JSON beeper path mismatch")

lines = [
    "# Beeper readiness",
    "",
    "Status: **STANDALONE SOUND TOGGLE AND JSON HANDOFF GUARDED**",
    "",
    "The Icarus test instantiates D57's PIT primitive and writes control 76h",
    "and count 4 to channel 1. It counts SOUND transitions throughout the",
    "simulation, waits 40 input clocks after programming, and requires at",
    "least two transitions in total. It does not verify tone frequency,",
    "complete CPU I/O decoding, analog drive, or audible output.",
    "",
    "- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the",
    "  traced `SOUND` source.",
    "- `kicad/juku.board.json` independently carries the traced handoff:",
    "  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.",
    "- The July target-board view directly reads VD4 as `КД521В`; an independent May view corroborates the grade-В reverse face;",
    "  the retained sheet supplies its cathode/anode connectivity.",
    "",
    "## Command",
    "",
    "Run from the repository root with Bash, Python 3, and Icarus Verilog",
    "(`iverilog` and `vvp`). Simulation files are temporary and removed on",
    "exit. After the HDL and JSON checks pass, the command overwrites this",
    "report at its fixed path, `docs/beeper-readiness.md`.",
    "",
    "```sh",
    "sync/beeper_check.sh",
    "```",
    "",
    "## Digital Evidence",
    "",
    "| Check | Result |",
    "| --- | --- |",
    "| D57 `OUT1` / `SOUND` has at least two transitions after programming | PASS |",
    "",
    "## Board Handoff Evidence",
    "",
    "The JSON check requires the nodes below and VD4's modeled value КД521В.",
    "Additional net members are allowed. It does not inspect photo hashes,",
    "PCB pads, routed copper, or installed diode polarity. Detailed source",
    "annotations remain in `kicad/juku.board.json`.", "",
    "| Net | Result | Required nodes |",
    "| --- | --- | --- |",
]
lines.extend(rows)
lines.extend(
    [
        "",
        "## Remaining Boundary",
        "",
        "Physical bring-up needs the speaker unit and level/current checks on real",
        "hardware. Photo evidence establishes the clamp part designation; the",
        "retained drawing supplies polarity. Those records are distinct from",
        "physical continuity and powered audio verification.",
        "",
    ]
)
(root / "docs" / "beeper-readiness.md").write_text("\n".join(lines))
PY

echo "BEEPER-CHECK: PASS"
echo "Wrote docs/beeper-readiness.md"
