#!/usr/bin/env python3
"""Prove the C executable is the sole runnable production Juku host."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"
RETIRED = (
    ROOT / "tools" / "janet_netboot.py",
    ROOT / "tools" / "janet_fastboot.py",
    ROOT / "tools" / "janet_disk_server.py",
)
FIXTURES = tuple(sorted((ROOT / "tests" / "fixtures").glob(
    "legacy_janet_*.py"
)))


def main() -> int:
    assert all(not path.exists() for path in RETIRED), RETIRED
    assert len(FIXTURES) == 3, FIXTURES
    for fixture in FIXTURES:
        text = fixture.read_text()
        assert 'if __name__ == "__main__"' not in text, fixture
        assert not os.access(fixture, os.X_OK), fixture
        assert "not production host entry points" in text or \
            "no runnable CLI" in text, fixture
    assert HOST.is_file() and os.access(HOST, os.X_OK), HOST
    result = subprocess.run(
        [str(HOST), "--selftest"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    assert result.returncode == 0 and "selftest: PASS" in result.stdout, \
        result.stdout
    print("PYTHON-HOST-RETIREMENT-TEST: PASS "
          "(one executable host; frozen non-runnable fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
