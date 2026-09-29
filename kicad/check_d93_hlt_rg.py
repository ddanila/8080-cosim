#!/usr/bin/env python3
"""Guard the exact-revision D93 HLT selector and unused RG pin."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad" / "juku.board.json"
HDL = ROOT / "hdl" / "juku_top.v"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    ready = spec["nets"]["FDC_READY"]["nodes"]
    if ["D93", "32"] not in ready or ["D93", "23"] in ready:
        raise SystemExit("FDC_READY lost D93.32 or incorrectly includes HLT/D93.23")
    if spec["nets"]["D99_Q1N_BOUNDARY"]["nodes"] != [["D99", "4"], ["D93", "23"]]:
        raise SystemExit("D99.4-to-D93.23 HLT source route changed")
    if spec["nets"]["D93_RG_NC"]["nodes"] != [["D93", "25"]]:
        raise SystemExit("D93 RG unused-pin disposition changed")
    for stale in ("D93_HLT_BOUNDARY", "D93_RG_BOUNDARY"):
        if stale in spec["nets"]:
            raise SystemExit(f"stale controller boundary returned: {stale}")
    hdl = HDL.read_text(encoding="utf-8")
    if ".hlt(d99_q1n_boundary)" not in hdl or ".rg(fdc_rg_nc)" not in hdl:
        raise SystemExit("structural D93 HLT/RG mapping changed")
    print("D93 HLT/RG: PASS — D99.4 drives HLT separately from READY; RG is unused/open")


if __name__ == "__main__":
    main()
