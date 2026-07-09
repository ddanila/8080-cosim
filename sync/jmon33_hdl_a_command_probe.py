#!/usr/bin/env python3
"""Run the checkpoint-resumed HDL jmon33 A-command framebuffer oracle."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-hdl-command-probe.md"
EXPECTED_STATUS = "Status: **JMON33 HDL A-COMMAND ORACLE READY**"
EXPECTED_SHA256 = "af3cfaefcc1f43604a02a2b2f95449a12c1b7a02a14581aea0bbfa06df51283a"


def main() -> int:
    env = os.environ.copy()
    env.setdefault("JMON33_HDL_COMMAND_REPORT", str(REPORT))
    env.setdefault("JMON33_HDL_COMMAND_CASES", "A-enter")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_CHECKPOINT", "1")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES", "26050000")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_START_VRAM", "210")
    env.setdefault("JMON33_HDL_COMMAND_KHOLD", "500000")
    env.setdefault("JMON33_HDL_COMMAND_KGAP", "100000")
    env.setdefault("JMON33_HDL_COMMAND_TIMEOUT", "360")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "sync" / "jmon33_hdl_command_probe.py")],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        return proc.returncode

    text = REPORT.read_text(errors="replace")
    if EXPECTED_STATUS not in text or EXPECTED_SHA256 not in text or "| A-enter |" not in text or "| PASS |" not in text:
        print("jmon33_hdl_a_command_probe: expected A-command HDL oracle evidence not found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
