#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${1:-docs/kp14-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s kp14_tb -o "$TMP/kp14_tb" hdl/devices.v hdl/sim/kp14_tb.v
output=$(vvp "$TMP/kp14_tb")
printf '%s\n' "$output"
grep -q '^KP14: PASS ' <<<"$output"

python3 - "$REPORT" <<'PY'
import json
import sys
from pathlib import Path

root = Path.cwd()
report = Path(sys.argv[1])
contract = json.loads((root / "ref/video/kp14-device-contract.json").read_text())
board = json.loads((root / "kicad/juku.board.json").read_text())
chips = {chip["ref"]: chip for chip in board["chips"]}

checks = [
    ("Contract records the КП14 equivalence", contract["equivalent"] == "SN74LS258B / SN74S258",
     f"{contract['primary_document']}; PDF SHA256 `{contract['source_pdf_sha256']}`"),
    ("Selected data is inverted", contract["function"]["enable_low_select_low"] == "Y is NOT A"
     and contract["function"]["enable_low_select_high"] == "Y is NOT B",
     "standalone HDL test checks both select states"),
    ("Output disable is active high", "high impedance" in contract["function"]["enable_high"],
     "/G=1 produces Z on all four outputs"),
    ("All five JSON mux entries declare КП14",
     all(chips[ref]["type"] == "KP14_MUX" for ref in ("D48", "D49", "D50", "D51", "D52")),
     "D48-D52 are КП14 in the board model"),
    ("Physical output pin names retain inversion",
     all(chips[ref]["pins"][pin].startswith("Y_N")
         for ref in ("D48", "D49", "D50", "D51", "D52")
         for pin in ("4", "7", "9", "12")),
     "pins 4/7/9/12 are Y_N0..Y_N3"),
]
ok = all(result for _, result, _ in checks)
lines = [
    "# К555КП14 / КР531КП14 primitive readiness",
    "",
    "Status: **DATASHEET-EXACT INVERTING КП14 PRIMITIVE GUARDED / BOARD TIMING UNMEASURED**"
    if ok else "Status: **КП14 PRIMITIVE CHECK FAILED**",
    "",
    "The primitive implements the SN74LS/S258 contract. With /G low,",
    "the selected A or B input is inverted at Y; with /G high, Y is high",
    "impedance. The РУ5 model removes this physical inversion only at its",
    "internal storage index so CPU-visible addresses remain linear.",
    "",
    "## Command",
    "",
    "```sh",
    "sync/kp14_check.sh",
    "```",
    "",
    "The standalone test checks inverted selection for A=1010/B=0101 and",
    "high impedance on disable. The script also checks contract metadata and",
    "the five canonical JSON component types and output pin names. It does",
    "not hash the PDF, inspect PCB pads, or test complete-board address timing.",
    "The PDF hash below is recorded metadata.", "",
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
    "## Boundary",
    "",
    "The D40/D59 1 MHz enable conductor is source- and owner-closed; see",
    "[the route review](d40-d59-d92-d95-1mhz-route.md). The structural model",
    "applies complementary enables to D48-D51. Runnable simulation uses a",
    "CPU-only address-bus scaffold and a separate video DRAM port, so it does",
    "not prove physical slot timing. Measured mux timing and unresolved",
    "serializer controls remain board boundaries; see",
    "[video reconstruction](video-readout-readiness.md).",
    "",
    f"Source document: [{contract['primary_document']}]({contract['source_url']}).",
    "",
])
report.write_text("\n".join(lines), encoding="utf-8")
if not ok:
    raise SystemExit(1)
print(f"Wrote {report}")
PY

echo "KP14-CHECK: PASS"
