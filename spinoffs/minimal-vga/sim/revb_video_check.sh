#!/usr/bin/env bash
# VJUGA rev B — Phase B2 video-card sim gate (TI.2). Runs the whole verified set for the
# chip-level TTL video twin: timing contract consistency, crop/letterbox resolution
# (D2.4), scanout fidelity, and /WAIT contention (D2.5). iverilog steps skip-not-fail
# when iverilog is absent, like the rest of the suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
R="spinoffs/minimal-vga/hdl/revb"
K="spinoffs/minimal-vga/kicad/revb"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

echo "== B2: timing contract == twin params (video-timing.json) =="
python3 "$K/revb_video_timing_check.py"

echo "== B2: crop/letterbox resolved against the oracle framebuffer (D2.4) =="
python3 "$K/revb_video_crop_check.py"

if ! command -v iverilog >/dev/null; then
  echo "  SKIP  B2 scanout + /WAIT sims: iverilog not found"
  echo "REVB-VIDEO-CHECK: partial (python gates only)"; exit 0
fi

echo "== B2: scanout fidelity + VGA timing (gate b) =="
iverilog -g2012 -o "$TMP/scan" "$R/revb_video_card_ttl.v" "$R/revb_video_scanout_tb.v"
vvp "$TMP/scan" | tee "$TMP/scan.log"
grep -q "REVB-VIDEO-SCANOUT: PASS" "$TMP/scan.log"

echo "== B2: /WAIT scanout-priority contention (gate c; D2.5) =="
iverilog -g2012 -o "$TMP/wait" "$R/revb_video_card_ttl.v" "$R/revb_video_wait_tb.v"
vvp "$TMP/wait" | tee "$TMP/wait.log"
grep -q "REVB-VIDEO-WAIT: PASS" "$TMP/wait.log"

echo "== B2: scanout address generator == src_row*40+byte_col (D2.7 accumulator) =="
iverilog -g2012 -o "$TMP/addr" "$R/revb_video_addrgen.v" "$R/revb_video_addrgen_tb.v"
vvp "$TMP/addr" | tee "$TMP/addr.log"
grep -q "REVB-VIDEO-ADDRGEN: PASS" "$TMP/addr.log"

echo "REVB-VIDEO-CHECK: PASS (timing + crop + scanout + /WAIT + addr-gen)"
