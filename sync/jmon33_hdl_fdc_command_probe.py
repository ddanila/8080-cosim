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
    accepted = saw_write_track or saw_write_protect
    if not accepted:
        print("jmon33_hdl_fdc_command_probe: expected write-track or write-protect FDC trace not found", file=sys.stderr)
    text = text.replace(
        "Status: **JMON33 HDL COMMAND BOUNDED DIAGNOSTIC**",
        "Status: **JMON33 HDL FDC T-COMMAND ORACLE PINNED**" if accepted
        else "Status: **JMON33 HDL FDC TRACE REQUIREMENT FAILED**",
        1,
    )
    text = text.replace(
        "sync/jmon33_hdl_command_probe.py",
        "sync/jmon33_hdl_fdc_command_probe.py",
        1,
    )
    intro_start = text.index("This guard starts from")
    intro_end = text.index("## Command", intro_start)
    text = text[:intro_start] + (
        "This wrapper generates a disk-backed cosim checkpoint with the T command\n"
        "scheduled, then resumes its RAM and visible state in `juku_top`. The default\n"
        "checkpoint is already inside the FDC polling loop. The HDL run stops after\n"
        "eight FDC events and checks for a write-track or write-protect trace marker;\n"
        "it does not require a completed command or matching command framebuffer.\n\n"
        "Keep `JMON33_HDL_COMMAND_REPORT` unset when using this wrapper. It always\n"
        "reads and rewrites `docs/jmon33-hdl-fdc-command-probe.md`; a report override\n"
        "redirects only the underlying runner and leaves the wrapper checking the\n"
        "fixed report rather than the new output. For a separate report, invoke\n"
        "`sync/jmon33_hdl_command_probe.py` directly with the desired settings.\n\n"
    ) + text[intro_end:]
    text = text.split("\n## Disposition\n", 1)[0].rstrip() + "\n"
    text += (
        "\n"
        "## FDC-Specific Disposition\n"
        "\n"
        "- This wrapper intentionally stops on the FDC trace boundary, so the generic\n"
        "  command framebuffer result remains `FAIL`/diagnostic.\n"
        '- The wrapper accepts either a write-track command (`OUT 0x1C = 0xFD`)\n'
        '  or a write-protect status read (`IN 0x1C = 0x40`) in the trace. It does\n'
        '  not require both markers or verify their order.\n'
        '- Compare the [cosim FDC oracle](jmon33-fdc-command-probe.md) for the\n'
        '  polling-loop interpretation. This check does not prove disk formatting\n'
        '  or complete the generic command framebuffer oracle.\n'
    )
    REPORT.write_text(text)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
