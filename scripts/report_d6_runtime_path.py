#!/usr/bin/env python3
"""Reproduce and document the physical-D6 mode-000 runnable boundary."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "d6-runtime-path-diagnostic.md"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="d6-runtime-path.") as tmp_name:
        sim = Path(tmp_name) / "d6_runtime_path_tb"
        compile_proc = subprocess.run(
            [
                "iverilog", "-g2012", "-s", "d6_runtime_path_tb", "-o", str(sim),
                str(ROOT / "hdl" / "devices.v"),
                str(ROOT / "hdl" / "sim" / "d6_runtime_path_tb.v"),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        run_proc = subprocess.run(
            ["vvp", str(sim)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        ) if compile_proc.returncode == 0 else None

    output = run_proc.stdout if run_proc else compile_proc.stdout
    required = [
        "D6-RUNTIME-LOW-ROM ba=0484 mode=000 join_n=0 roe_n=1 d58_oe_n=1",
        "D6-RUNTIME-RAM ba=b37a mode=000 join_n=0 rev=0 roe_n=1 ram_out_en=0 d58_oe_n=1 oracle_ram_n=0 oracle_d58_oe_n=0",
        "D6-RUNTIME-PATH: BOUNDARY REPRODUCED",
    ]
    ok = compile_proc.returncode == 0 and run_proc is not None and run_proc.returncode == 0
    ok = ok and all(marker in output for marker in required)
    if not ok:
        print(output)
        raise SystemExit("D6 RUNTIME PATH DIAGNOSTIC: FAIL")

    lines = [
        "# D6 runnable-path diagnostic", "",
        "Status: **PHYSICAL MODE-000 RAM GATE BOUNDARY REPRODUCED**", "",
        "This generated diagnostic preserves the exact combinational failure found",
        "while testing whether the runnable boot could use D6 `.038` directly. It is",
        "not a replacement memory decoder and does not bless the compatibility oracle.",
        "It narrows the remaining reconstruction to one physical control path.", "",
        "## Reproduction", "", "```sh",
        "python3 scripts/report_d6_runtime_path.py", "```", "",
        "The test reads the validated D6 table through `decode_prom`, then follows",
        "D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.",
        "It also samples `decode_prom_functional` only to state the established",
        "runnable behavior at the same addresses.", "",
        "## Result", "", "```text", *output.strip().splitlines(), "```", "",
        "At low-ROM address `0484`, physical word `8` correctly leaves D58 released",
        "while the joined D6 conductor enables the D8 pager. At RAM call target",
        "`B37A`, the same physical word `8` still leaves D6.9 high; the currently",
        "traced D13/D37 polarity therefore keeps D58 OE high. The checkpoint-resume",
        "experiment consequently consumed `FF` at the RAM call and never reached the",
        "PIC/keyboard boundary. Restoring the explicit oracle returned the guard to",
        "`PASS` at 25,744 resumed machine cycles.", "",
        "## Evidence boundary", "",
        "- The RT4 reader wiring and repeated table are guarded independently; this",
        "  result is not evidence to reorder or complement the dump.",
        "- The `.006` sheet shows separate D6 ROM/RAM outputs. Direct owner continuity",
        "  on the `.009` board instead reported D6.11, D6.12, and D13.12 joined and",
        "  found no D8/D9 continuation. The source model currently retains older-sheet",
        "  D8/D92 branches on that joined net, so this cross-revision contradiction",
        "  must be resolved before the oracle can be retired.",
        "- The decisive hardware check is an isolated, powered-off resistance map with",
        "  D6 and D13 removed, followed by live levels at D6.9, D13.2, D37.6, and",
        "  D58.9 during a known RAM read. Do not infer a new net merely to make boot pass.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("D6 RUNTIME PATH DIAGNOSTIC: PASS (boundary reproduced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
