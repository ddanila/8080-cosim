#!/usr/bin/env bash
# Guard the К155АГ3 / 74123 package and D56's photo-proved trigger grounding.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${AG3_REPORT:-docs/ag3-oneshot-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s ag3_oneshot_tb -o "$TMP/ag3_oneshot_tb" \
  hdl/devices.v hdl/sim/ag3_oneshot_tb.v
vvp "$TMP/ag3_oneshot_tb" > "$TMP/ag3.out"
pass_line=$(grep -m1 '^AG3-ONESHOT: PASS' "$TMP/ag3.out" || true)
if [ -z "$pass_line" ]; then
  cat "$TMP/ag3.out"
  echo "AG3-CHECK: FAIL"
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

board = json.loads(Path("kicad/juku.board.json").read_text(encoding="utf-8"))
gnd = {tuple(node) for node in board["nets"]["GND"]["nodes"]}
required = {("D56", "1"), ("D56", "8"), ("D56", "9")}
assert required <= gnd, f"D56 trigger ground missing: {sorted(required - gnd)}"
assert ["D56", "1"] not in board["no_connects"]
assert ["D56", "9"] not in board["no_connects"]
assert ["D56", "13"] in board["no_connects"]

registration = json.loads(Path(
    "ref/photos/dgsh5-109-009-sb/factory-modification-registration.json"
).read_text(encoding="utf-8"))
ground = registration["d56"]["trigger_ground_rail"]
assert ground["source_net"] == "GND"
assert ground["package_ground_pin"] == "8"
assert set(ground["trigger_pins"]) == {"1", "9"}
assert len(ground["solder_observations"]) == 2
PY

cat > "$REPORT" <<EOF
# К155АГ3 / 74123 one-shot readiness

Status: **PACKAGE BEHAVIOR AND D56 TRIGGER GROUNDING GUARDED**

The \`ag3_oneshot\` primitive now implements the two К155АГ3/74123
retriggerable monostable sections instead of releasing all four outputs as
high-impedance placeholders. D56 uses the traced R59/C8 and R47/C7 timing
networks, giving typical modeled pulses of about 223 us and 5.04 us.

## Primary specification

Texas Instruments, *SN54122/SN54123/SN54130/SN54LS122/SN54LS123 and
SN74122/SN74123/SN74130/SN74LS122/SN74LS123 — Retriggerable Monostable
Multivibrators*, SDLS043, December 1983, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls123.pdf>

The guard covers:

- active-low overriding clear and complementary Q/Q-bar outputs;
- B rising with A low, A falling with B high, and valid clear-release triggers;
- independent dual sections and parameterized RC pulse durations;
- retrigger extension after the documented 0.22-Cext inhibit interval; and
- immediate clear termination and cancellation of stale delayed completions.

## Installed-board trigger closure

The native sheet leaves D56.1 and D56.9 unstubbed, but two overlapping owner
solder photographs resolve the installed \`.009\` target. The reflected local
package fit places D56.9 directly on D56.8's upper ground rail; D56.1 joins the
same rail through the uninterrupted wide left-edge return. Both active-low A
inputs are therefore grounded, enabling the source-traced SYNC-B connections on
pins 2 and 10. The separate position-159 callout at D56.5/D56.12 remains held.

## Command

\`\`\`sh
sync/ag3_check.sh
\`\`\`

## Result

\`\`\`text
$pass_line
\`\`\`

## Evidence boundary

The RC-derived widths are datasheet-typical behavioral values, not a substitute
for measuring the installed К155АГ3 across component tolerance and temperature.
D56.12's printed tag-16 far destination and the item-159 assembly conductor are
still explicit physical boundaries.
EOF

echo "$pass_line"
echo "AG3-CHECK: PASS"
