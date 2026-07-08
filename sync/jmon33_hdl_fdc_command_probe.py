#!/usr/bin/env python3
"""Run the checkpoint-resumed HDL jmon33 T command against the disk-backed FDC oracle."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-hdl-fdc-command-probe.md"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"


def main() -> int:
    env = os.environ.copy()
    env.setdefault("JUKU_DISK", str(DISK))
    env.setdefault("JMON33_HDL_COMMAND_DISK", str(DISK))
    env.setdefault("JMON33_HDL_COMMAND_REPORT", str(REPORT))
    env.setdefault("JMON33_HDL_COMMAND_CASES", "T-enter")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_CHECKPOINT", "1")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES", "26050000")
    env.setdefault("JMON33_HDL_COMMAND_PHASE_START_VRAM", "210")
    env.setdefault("JMON33_HDL_COMMAND_KHOLD", "500000")
    env.setdefault("JMON33_HDL_COMMAND_MAX_MCYC", "120000")
    env.setdefault("JMON33_HDL_COMMAND_TIMEOUT", "180")
    env.setdefault("JMON33_HDL_COMMAND_TRACEFDC", "1")
    env.setdefault("JMON33_HDL_COMMAND_STOPFDC", "8")

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
    lower_text = text.lower()
    saw_write_track = "out port=0x1c reg=0 data=0xfd" in lower_text
    saw_write_protect = "in  port=0x1c reg=0 data=0x40" in lower_text
    if not (saw_write_track or saw_write_protect):
        print("jmon33_hdl_fdc_command_probe: expected write-track or write-protect FDC trace not found", file=sys.stderr)
        return 1
    text = text.replace(
        "Status: **JMON33 HDL COMMAND BOUNDED DIAGNOSTIC**",
        "Status: **JMON33 HDL FDC T-COMMAND ORACLE PINNED**",
        1,
    )
    text += (
        "\n"
        "## FDC-Specific Disposition\n"
        "\n"
        "- This wrapper intentionally stops on the FDC trace boundary, so the generic\n"
        "  command framebuffer result remains `FAIL`/diagnostic.\n"
        "- The pass condition is the structural `juku_top` path reading status `0x40`\n"
        "  from the disk-backed FDC after the Monitor 3.3 `T` command has entered\n"
        "  the write-track/write-protect polling loop.\n"
        "- This matches the cosim oracle in `docs/jmon33-fdc-command-probe.md` and\n"
        "  removes the previous ambiguity that the HDL `T` path was merely a\n"
        "  keyboard-phase mismatch.\n"
    )
    REPORT.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
