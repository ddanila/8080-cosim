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
expected = {
    "SOUND": [("D57", "13"), ("R90", "1")],
    "SND_BASE": [("R90", "2"), ("VD4", "2"), ("VT1", "2")],
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
        "| `{}` | {} | {} | {} |".format(
            name,
            "PASS" if passed else "FAIL",
            ", ".join(f"`{ref}.{pin}`" for ref, pin in nodes),
            (net or {}).get("src", "missing net"),
        )
    )

if not ok:
    raise SystemExit("BEEPER-CHECK: board JSON beeper path mismatch")

lines = [
    "# Beeper readiness",
    "",
    "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**",
    "",
    "This guard proves the runnable digital source of the Juku beeper path and",
    "cross-checks the traced board handoff into the analog driver.",
    "",
    "- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the",
    "  traced `SOUND` source.",
    "- `hdl/sim/beeper_path_tb.v` programs D57 channel 1 with a small reload value",
    "  and requires `OUT1` to toggle.",
    "- `kicad/juku.board.json` independently carries the traced handoff:",
    "  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.",
    "",
    "## Command",
    "",
    "```sh",
    "sync/beeper_check.sh",
    "```",
    "",
    "## Digital Evidence",
    "",
    "| Check | Result |",
    "| --- | --- |",
    "| D57 channel 1 accepts control/data writes | PASS |",
    "| D57 `OUT1` / `SOUND` toggles after programming | PASS |",
    "",
    "## Board Handoff Evidence",
    "",
    "| Net | Result | Required nodes | Source |",
    "| --- | --- | --- | --- |",
]
lines.extend(rows)
lines.extend(
    [
        "",
        "## Remaining Boundary",
        "",
        "- This is a digital source plus board-handoff guard, not an analog speaker",
        "  model. Physical bring-up still needs the speaker unit, clamp polarity,",
        "  and level/current check on real hardware.",
        "",
    ]
)
(root / "docs" / "beeper-readiness.md").write_text("\n".join(lines))
PY

echo "BEEPER-CHECK: PASS"
echo "Wrote docs/beeper-readiness.md"
