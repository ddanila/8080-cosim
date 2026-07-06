#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

WRITES=${VIDEO_WRITES:-6000}
REPORT=${1:-docs/video-readout-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== generate ROM hex =="
python3 - <<'PY'
from pathlib import Path
rom = Path("roms/ekta37.bin").read_bytes()
Path("hdl/sim/ekta37.hex").write_text("\n".join(f"{byte:02x}" for byte in rom) + "\n")
PY

echo "== generate source framebuffer from juku_top boot =="
iverilog -g2012 -o "$TMP/juku_top_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v
vvp "$TMP/juku_top_tb" +maxvram="$WRITES" >/dev/null 2>&1

echo "== convert framebuffer to readmemh input =="
python3 - <<'PY'
from pathlib import Path
src = Path("hdl/sim/vram_top.bin").read_bytes()
padded = src + bytes(16384 - len(src))
Path("hdl/sim/vram_top.hex").write_text("\n".join(f"{byte:02x}" for byte in padded) + "\n")
print(len(src))
PY

echo "== standalone serializer readout =="
iverilog -g2012 -o "$TMP/video_readout_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/video_readout_tb.v
vvp "$TMP/video_readout_tb" >/dev/null 2>&1
cmp -s hdl/sim/vram_top.bin hdl/sim/vram_readout.bin

echo "== juku_top video-output readout =="
iverilog -g2012 -o "$TMP/video_out_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/video_out_tb.v
vvp "$TMP/video_out_tb" >/dev/null 2>&1
cmp -s hdl/sim/vram_top.bin hdl/sim/vram_vidout.bin

src_bytes=$(wc -c < hdl/sim/vram_top.bin | tr -d ' ')
readout_bytes=$(wc -c < hdl/sim/vram_readout.bin | tr -d ' ')
vidout_bytes=$(wc -c < hdl/sim/vram_vidout.bin | tr -d ' ')

cat > "$REPORT" <<EOF
# Video readout readiness

Status: **READY FOR V2 VIDEO READOUT**

This guard proves the current runnable video-readout path for WS-B2:

- hdl/sim/video_readout_tb.v serializes a booted framebuffer through the
  abstracted ir16_sr pixel serializer and reconstructs the bytes.
- hdl/sim/video_out_tb.v drives juku_top's own video_raster -> ir16_sr ->
  lp5_xor1 path and reconstructs the emitted vid_out stream.
- Both reconstructed byte streams must compare exactly against the booted
  juku_top framebuffer.

The V3 boundary remains the faithful physical slot timing: shared DRAM
arbitration through the КП14 muxes and dumped РЕ3/АГ3 timing. This check does not
claim that timing is closed; it locks the byte-to-pixel serializer and runnable
juku_top output stage.

## Command

\`\`\`sh
sync/video_readout_check.sh
\`\`\`

## Evidence

| Artifact | Bytes | Check |
| --- | ---: | --- |
| hdl/sim/vram_top.bin | $src_bytes | source framebuffer from juku_top_tb |
| hdl/sim/vram_readout.bin | $readout_bytes | byte-identical standalone serializer reconstruction |
| hdl/sim/vram_vidout.bin | $vidout_bytes | byte-identical juku_top video-output reconstruction |

## Remaining Boundary

- Dump or otherwise prove the РЕ3/АГ3 timing that arbitrates CPU/video DRAM
  slots.
- Replace the sim-only second framebuffer read port with the real shared-memory
  video read slot when the timing source is available.
EOF

echo "VIDEO-READOUT-CHECK: PASS"
echo "Wrote $REPORT"
