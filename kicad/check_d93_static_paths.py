#!/usr/bin/env python3
"""Guard exact-revision D93 reset and TEST/WF-VFOE connectivity."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
HDL = ROOT / "hdl" / "juku_top.v"


def main() -> None:
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    reset_nodes = spec["nets"]["RESET"]["nodes"]
    fdc_reset_nodes = spec["nets"]["FDC_RESET_N"]["nodes"]
    static_nodes = spec["nets"]["D93_TEST_WF_VFOE"]["nodes"]
    if ["D13", "9"] not in reset_nodes or ["D93", "19"] in reset_nodes:
        raise SystemExit("board JSON RESET does not terminate at D13.9")
    if fdc_reset_nodes != [["D13", "8"], ["D93", "19"]]:
        raise SystemExit(f"board JSON FDC reset inversion changed: {fdc_reset_nodes}")
    if static_nodes != [["D93", "22"], ["D93", "33"]]:
        raise SystemExit(f"board JSON D93 static tie changed: {static_nodes}")
    for stale in ("D93_MR_BOUNDARY", "D93_TEST_BOUNDARY", "D93_WF_VFOE_BOUNDARY"):
        if stale in spec["nets"]:
            raise SystemExit(f"stale boundary returned: {stale}")

    hdl = HDL.read_text(encoding="utf-8")
    for marker in (
        ".i9(reset_sys), .o8(fdc_reset_n)",
        ".mr_n(fdc_reset_n)",
        ".test(fdc_test_wf_vfoe)",
        ".wf_vfoe(fdc_test_wf_vfoe)",
    ):
        if marker not in hdl:
            raise SystemExit(f"HDL static-path marker missing: {marker}")
    print("D93 STATIC PATHS: PASS — RESET->D13.9/.8->D93.19; TEST 22<->WF/VFOE 33")


if __name__ == "__main__":
    main()
