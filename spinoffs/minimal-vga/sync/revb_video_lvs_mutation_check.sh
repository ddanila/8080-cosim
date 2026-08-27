#!/usr/bin/env bash
# R5.V1 negative controls: the full-card LVS must reject both a swap and a missing pin.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CARDROOT="$ROOT/spinoffs/minimal-vga"
command -v yosys >/dev/null 2>&1 || { echo "SKIP video LVS mutations: yosys not found"; exit 0; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

python3 "$CARDROOT/kicad/revb/gen_revb_lvs_map.py" video >/dev/null
yosys -q -p "read_verilog -lib $CARDROOT/hdl/revb/revb_video_lvs.v; read_verilog $CARDROOT/hdl/revb/revb_video_lvs.v; hierarchy -top revb_video_lvs_top; write_json $TMP/lvs.json"

python3 - "$CARDROOT/kicad/revb/video.board.json" "$TMP" <<'PY'
import copy, json, sys
board = json.load(open(sys.argv[1]))
for kind in ("swap", "missing"):
    test = copy.deepcopy(board)
    if kind == "swap":
        chip = next(c for c in test["chips"] if c["ref"] == "U16")
        chip["pins"]["3"], chip["pins"]["14"] = chip["pins"]["14"], chip["pins"]["3"]
        for net in test["nets"].values():
            for node in net["nodes"]:
                if node == ["U16", "3"]: node[1] = "14"
                elif node == ["U16", "14"]: node[1] = "3"
    else:
        chip = next(c for c in test["chips"] if c["ref"] == "U21")
        del chip["pins"]["22"]
        for net in test["nets"].values():
            net["nodes"] = [n for n in net["nodes"] if n != ["U21", "22"]]
    with open(f"{sys.argv[2]}/{kind}.json", "w") as out:
        json.dump(test, out)
PY

for mutation in swap missing; do
    if python3 "$ROOT/sync/lvs.py" --hdl "$TMP/lvs.json" --board "$TMP/$mutation.json" \
        --map "$CARDROOT/sync/revb_video_map.json" --include-power >"$TMP/$mutation.log" 2>&1; then
        echo "REVB-VIDEO-LVS-MUTATION: FAIL $mutation escaped" >&2
        exit 1
    fi
    grep -q '==> MISMATCH' "$TMP/$mutation.log"
done
echo "REVB-VIDEO-LVS-MUTATION: PASS swapped and missing connections rejected"
