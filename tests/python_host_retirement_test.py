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
DIAGNOSTIC_IMPORTERS = {
    Path("tools/janet_baud_ladder.py"),
    Path("tools/janet_baud_test.py"),
    Path("tools/janet_baud_test2.py"),
    Path("tools/janet_mode2_soak.py"),
}
HISTORICAL_PATH_REFERENCES = {
    Path("docs/portable-c-host-m0-contract.md"),
    Path("docs/portable-c-host-m2-acceptance.md"),
    Path("docs/portable-c-host-plan.md"),
    Path("tests/python_host_retirement_test.py"),
}


def repository_sources() -> list[Path]:
    sources: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or \
                "build" in path.parts:
            continue
        if path.suffix in {".md", ".py", ".sh", ".yml", ".yaml", ".json"}:
            sources.append(path)
    return sources


def main() -> int:
    assert all(not path.exists() for path in RETIRED), RETIRED
    assert len(FIXTURES) == 3, FIXTURES
    for fixture in FIXTURES:
        text = fixture.read_text()
        assert 'if __name__ == "__main__"' not in text, fixture
        assert not os.access(fixture, os.X_OK), fixture
        assert "not production host entry points" in text or \
            "no runnable CLI" in text, fixture

    # Fixture-backed protocol implementations may be imported only by tests
    # and by the four explicitly retained, bounded UART diagnostic labs.
    # This prevents a new operational wrapper from quietly restoring Python
    # as a production-server fallback.
    for source in ROOT.rglob("*.py"):
        if ".git" in source.parts or "build" in source.parts:
            continue
        relative = source.relative_to(ROOT)
        text = source.read_text(errors="replace")
        if "legacy_janet_" not in text:
            continue
        assert relative.parts[0] == "tests" or \
            relative in DIAGNOSTIC_IMPORTERS, relative

    retired_paths = tuple(path.relative_to(ROOT).as_posix()
                          for path in RETIRED)
    for source in repository_sources():
        relative = source.relative_to(ROOT)
        mentioned = any(path in source.read_text(errors="replace")
                        for path in retired_paths)
        assert not mentioned or relative in HISTORICAL_PATH_REFERENCES, \
            relative

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
