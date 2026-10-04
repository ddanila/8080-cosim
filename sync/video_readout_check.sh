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

echo "== juku_top abstract pixel-oracle readout =="
iverilog -g2012 -o "$TMP/video_out_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/video_out_tb.v
vvp "$TMP/video_out_tb" >/dev/null 2>&1
cmp -s hdl/sim/vram_top.bin hdl/sim/vram_vidout.bin

src_bytes=$(wc -c < hdl/sim/vram_top.bin | tr -d ' ')
readout_bytes=$(wc -c < hdl/sim/vram_readout.bin | tr -d ' ')
vidout_bytes=$(wc -c < hdl/sim/vram_vidout.bin | tr -d ' ')

cat > "$REPORT" <<EOF
# Video readout readiness

Status: **RUNNABLE ABSTRACT VIDEO READOUT GUARDED**

This guard checks byte preservation in the runnable abstract video path.
It runs archive-37 RomBios 3.43m with a requested stop target of $WRITES
framebuffer writes (VIDEO_WRITES defaults to 6000), then serializes the capture.
The testbench also has a 400 ms simulated time cap. This script suppresses
the boot log and does not assert that the write target was reached.
It does not require a full boot prompt or compare that screen to cosim:

- hdl/sim/video_readout_tb.v serializes a booted framebuffer through the
  abstracted ir16_sr pixel serializer and reconstructs the bytes.
- hdl/sim/video_out_tb.v drives juku_top's own video_raster -> ir16_sr ->
  lp5_xor1 path and reconstructs the emitted abstract vid_out bitstream.
- Both reconstructed byte streams must compare exactly against the booted
  juku_top framebuffer.

The sim-only vid_out port is not composite voltage and is not a simulated D34
or VIDEO_OUT node. It contains no sync summing, VT2 output stage, termination, or edge
model. Its name is retained only for HDL interface compatibility.

The remaining physical boundary is the shared-DRAM slot timing: arbitration
through the КП14 muxes, D53 decoder and D41 timing chain. This check does not claim
that timing is closed; it locks only the byte-to-pixel serializer and runnable
juku_top abstract oracle. The companion raster-geometry guard is
\`sync/video_timing_check.sh\` / \`docs/video-timing-reference.md\`.

## Command

\`\`\`sh
VIDEO_WRITES=$WRITES sync/video_readout_check.sh
\`\`\`

The check requires Bash, Python 3, Icarus Verilog (\`iverilog\` and \`vvp\`),
and the archived \`roms/ekta37.bin\`. It runs from the repository root and
rewrites the named captures and generated hex inputs under \`hdl/sim\`.
The first argument selects the report path (default
\`docs/video-readout-readiness.md\`); its parent directory must exist. An
alternate report path does not isolate the capture files.

## Evidence

| Artifact | Bytes | Check |
| --- | ---: | --- |
| hdl/sim/vram_top.bin | $src_bytes | source framebuffer from juku_top_tb |
| hdl/sim/vram_readout.bin | $readout_bytes | byte-identical standalone serializer reconstruction |
| hdl/sim/vram_vidout.bin | $vidout_bytes | byte-identical juku_top abstract-oracle reconstruction |

## Remaining Boundary

- Establish the CPU/video shared-DRAM slot schedule with source closure and
  measured timing. The validated D8/D94 РЕ3 contents are already available;
  they do not establish this arbitration schedule. See
  [the slot timing audit](video-slot-timing-audit.md).
- Replace the sim-only second framebuffer read port with the real shared-memory
  video read slot when the timing source is available.
EOF

echo "VIDEO-READOUT-CHECK: PASS"
echo "Wrote $REPORT"
