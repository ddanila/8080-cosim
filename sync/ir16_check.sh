#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${1:-docs/ir16-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s ir16_tb -o "$TMP/ir16_tb" hdl/devices.v hdl/sim/ir16_tb.v
output=$(vvp "$TMP/ir16_tb")
printf '%s\n' "$output"
grep -q '^IR16: PASS ' <<<"$output"

python3 - "$REPORT" <<'PY'
import json
import sys
from pathlib import Path

root = Path.cwd()
report = Path(sys.argv[1])
contract = json.loads((root / "ref/video/ir16-device-contract.json").read_text())
board = json.loads((root / "kicad/juku.board.json").read_text())

def endpoints(name):
    return {tuple(node) for node in board["nets"][name]["nodes"]}

checks = [
    ("К555ИР16 equivalence is pinned", contract["equivalent"] == "SN74LS295B",
     f"{contract['primary_document']}; PDF SHA256 `{contract['source_pdf_sha256']}`"),
    ("Clock transition is high-to-low", contract["clock_edge"] == "high-to-low",
     "standalone HDL test rejects a rising-edge state change"),
    ("LD/SH polarity is literal", contract["modes"]["ld_sh_high"].startswith("parallel load")
     and contract["modes"]["ld_sh_low"].startswith("right shift"),
     "LD/SH=1 loads A-D; LD/SH=0 shifts SER through QA toward QD"),
    ("OC is active-high three-state control", contract["modes"]["oc_high"] == "outputs enabled"
     and "high impedance" in contract["modes"]["oc_low"],
     "OC=0 produces Z while sequential state continues"),
    ("D41 output control is physically high", ("D41", "8") in endpoints("P5V"),
     "D41.8 is on P5V"),
    ("D42/D43 output control remains one explicit rail", endpoints("SHIFT_G")
     == {("D41", "9"), ("D42", "8"), ("D43", "8")},
     "SHIFT_G joins D41.CLK to D42.OC/D43.OC; its remote source remains open"),
]
ok = all(result for _, result, _ in checks)
lines = [
    "# К555ИР16 primitive readiness",
    "",
    "Status: **DATASHEET-EXACT ИР16 PRIMITIVE GUARDED / BOARD CONTROL SOURCES OPEN**"
    if ok else "Status: **ИР16 PRIMITIVE CHECK FAILED**",
    "",
    "This guard corrects the shared D41/D42/D43 device primitive without",
    "claiming the unresolved board timing rails. The device is the SN74LS295B-",
    "equivalent four-bit register: it changes state on the falling clock edge,",
    "loads when LD/SH is high, shifts right when LD/SH is low, and uses pin 8",
    "as an active-high three-state output control.",
    "",
    "## Command",
    "",
    "```sh",
    "sync/ir16_check.sh",
    "```",
    "",
    "## Checks",
    "",
    "| Check | Result | Evidence |",
    "| --- | --- | --- |",
]
lines.extend(
    f"| {name} | {'PASS' if result else 'FAIL'} | {evidence} |"
    for name, result, evidence in checks
)
lines.extend([
    "",
    "## Physical consequence",
    "",
    "- `SHIFT_G` is now correctly classified as the D42/D43 output-control rail;",
    "  it is not a serializer clock or clock-inhibit input.",
    "- D41 uses that same rail as its clock while its own OC pin is tied high.",
    "- D42/D43 still receive their separate clock on `XTAL16M` and their mode",
    "  input on `LOAD_VID`.",
    "- The remote sources of `SHIFT_G` and `TIMING_TAG17` remain evidence gaps,",
    "  so this correction does not claim a physical DRAM slot schedule or pixels.",
    "",
    f"Source document: [{contract['primary_document']}]({contract['source_url']}).",
    "",
])
report.write_text("\n".join(lines), encoding="utf-8")
if not ok:
    raise SystemExit(1)
print(f"Wrote {report}")
PY

echo "IR16-CHECK: PASS"
