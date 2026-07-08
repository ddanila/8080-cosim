#!/usr/bin/env python3
"""Probe jmon33 commands typed after the monitor-idle cursor is visible."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env.setdefault("JMON33_COMMAND_ORACLE", "idle")
    env.setdefault("JMON33_COMMAND_START_VRAM", "210")
    env.setdefault("JMON33_COMMAND_REPORT", str(ROOT / "docs" / "jmon33-idle-command-probe.md"))
    proc = subprocess.run([sys.executable, str(ROOT / "sync" / "jmon33_command_probe.py")], cwd=ROOT, env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
