#!/usr/bin/env bash
# Guard the runnable video raster geometry against the vendored MAME reference.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${VIDEO_TIMING_REPORT:-docs/video-timing-reference.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== parse MAME video constants =="
python3 - <<'PY' > "$TMP/mame-video.env"
from pathlib import Path
import re

text = Path("ref/mame_juku.cpp").read_text()

values: dict[str, int] = {}

def const(name: str) -> int:
    if name in values:
        return values[name]
    m = re.search(rf"static constexpr int {name} = ([^;]+);", text)
    if not m:
        raise SystemExit(f"missing {name}")
    expr = m.group(1)
    values[name] = int(eval(expr, {"__builtins__": {}}, values))
    return values[name]

width = const("DEFAULT_WIDTH")
height = const("DEFAULT_HEIGHT")
vfront = const("VERT_FRONT_PORCH")
vback = const("VERT_BACK_PORCH")
hfront = const("HORIZ_FRONT_PORCH")
hback = const("HORIZ_BACK_PORCH")
hperiod = const("HORIZ_PERIOD")
vperiod = const("VERT_PERIOD")

if width % 8:
    raise SystemExit(f"visible width {width} is not byte-aligned")

print(f"MAME_WIDTH={width}")
print(f"MAME_HEIGHT={height}")
print(f"MAME_COLS={width // 8}")
print(f"MAME_BYTES={(width // 8) * height}")
print(f"MAME_HFRONT={hfront}")
print(f"MAME_HBACK={hback}")
print(f"MAME_HPERIOD={hperiod}")
print(f"MAME_VFRONT={vfront}")
print(f"MAME_VBACK={vback}")
print(f"MAME_VPERIOD={vperiod}")
print(f"MAME_FRAME_RATE={1000000 / ((hperiod // 8) * vperiod):.6f}")
PY
source "$TMP/mame-video.env"

if [ "$MAME_WIDTH" -ne 320 ] || [ "$MAME_HEIGHT" -ne 241 ] || [ "$MAME_COLS" -ne 40 ] || [ "$MAME_BYTES" -ne 9640 ]; then
  echo "VIDEO-TIMING-CHECK: FAIL unexpected MAME geometry"
  cat "$TMP/mame-video.env"
  exit 1
fi

echo "== video raster geometry =="
iverilog -g2012 -s video_raster_geometry_tb -o "$TMP/video_raster_geometry_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/sim/video_raster_geometry_tb.v
vvp "$TMP/video_raster_geometry_tb" > "$TMP/video-raster.out"
cat "$TMP/video-raster.out"
pass_line=$(grep -m1 '^VIDEO-RASTER-GEOMETRY: PASS' "$TMP/video-raster.out" || true)
if [ -z "$pass_line" ]; then
  echo "VIDEO-TIMING-CHECK: FAIL"
  exit 1
fi

cat > "$REPORT" <<EOF
# Video timing reference

Status: **VIDEO RASTER GEOMETRY GUARDED**

This check pins the runnable video raster geometry against the vendored MAME
Juku reference and the local \`video_raster\` HDL block.

## Command

\`\`\`sh
sync/video_timing_check.sh
\`\`\`

## MAME Reference

Parsed from \`ref/mame_juku.cpp\`:

| Parameter | Value |
| --- | ---: |
| visible width | $MAME_WIDTH px |
| visible height | $MAME_HEIGHT lines |
| framebuffer columns | $MAME_COLS bytes |
| framebuffer bytes | $MAME_BYTES |
| horizontal front porch | $MAME_HFRONT px |
| horizontal back porch | $MAME_HBACK px |
| horizontal period | $MAME_HPERIOD px |
| vertical front porch | $MAME_VFRONT lines |
| vertical back porch | $MAME_VBACK lines |
| vertical period | $MAME_VPERIOD lines |
| nominal frame rate | $MAME_FRAME_RATE Hz |

## HDL Guard

- \`hdl/sim/video_raster_geometry_tb.v\` instantiates \`video_raster\`.
- It requires a 40 x 241 byte raster: \`9640\` framebuffer bytes.
- It requires one load phase followed by seven shift phases for every byte.
- It requires wrap back to \`0xD800\` after \`77120\` dot clocks.

Pass line:

\`\`\`
$pass_line
\`\`\`

## Boundary

This does not close the faithful shared-DRAM video slot timing. The still-open
work is the РЕ3/АГ3-driven CPU/video arbitration schedule and replacement of
the sim-only video read port with that real slot timing.
EOF

echo "VIDEO-TIMING-CHECK: PASS"
echo "Wrote $REPORT"
