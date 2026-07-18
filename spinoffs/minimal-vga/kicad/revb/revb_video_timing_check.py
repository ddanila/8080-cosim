#!/usr/bin/env python3
"""TI.2 gate — the chip-level twin's default timing parameters must equal the timing
contract (video-timing.json). Pure python, no tools: parses the parameter defaults out of
revb_video_card_ttl.v and compares them to the JSON, and re-checks the JSON's own
arithmetic (H/V totals, 40x241 framebuffer, 320x241 doubled). Keeps the Verilog and the
contract from drifting apart.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
V = os.path.join(REPO, "spinoffs", "minimal-vga", "hdl", "revb", "revb_video_card_ttl.v")
T = json.load(open(os.path.join(HERE, "video-timing.json")))

src = open(V).read()
# Parameter defaults are declared comma-separated on 'parameter integer' lines, so match
# every NAME = <digits> and keep the first (the default). Computed localparams reference
# other names (NAME = A + B), so they don't match the pure-digit RHS.
params = {}
for m in re.finditer(r'(\w+)\s*=\s*(\d+)\b', src):
    params.setdefault(m.group(1), int(m.group(2)))

fails = []


def want(name, expect):
    if params.get(name) != expect:
        fails.append(f"twin {name}={params.get(name)} != contract {expect}")


h, v, fb = T["h"], T["v"], T["framebuffer"]
want("H_ACTIVE", h["active"]); want("H_FP", h["front_porch"]); want("H_SYNC", h["sync"])
want("H_BP", h["back_porch"]); want("H_TOTAL", h["total"])
want("V_ACTIVE", v["active"]); want("V_FP", v["front_porch"]); want("V_SYNC", v["sync"])
want("V_BP", v["back_porch"]); want("V_TOTAL", v["total"])
want("FB_COLS", fb["cols_bytes"]); want("FB_ROWS", fb["rows"])

# JSON self-consistency (the contract must be internally correct)
if h["active"] + h["front_porch"] + h["sync"] + h["back_porch"] != h["total"]:
    fails.append("H porches do not sum to H total")
if v["active"] + v["front_porch"] + v["sync"] + v["back_porch"] != v["total"]:
    fails.append("V porches do not sum to V total")
if fb["cols_bytes"] * fb["rows"] != fb["bytes"]:
    fails.append("framebuffer cols*rows != bytes")
sc = T["scanout"]
if fb["src_pixels_w"] * sc["h_double"] != sc["doubled_w"] or \
   fb["src_pixels_h"] * sc["v_double"] != sc["doubled_h"]:
    fails.append("doubled dimensions inconsistent")

if fails:
    print("video timing check FAILED:")
    for f in fails:
        print(f"    {f}")
    sys.exit(1)
refresh = T["dot_clock_hz"] / (h["total"] * v["total"])
print(f"video timing check OK: twin params == video-timing.json "
      f"(640x480@{refresh:.2f}Hz, fb {fb['cols_bytes']}x{fb['rows']})")
