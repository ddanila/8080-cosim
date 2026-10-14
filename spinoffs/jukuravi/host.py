#!/usr/bin/env python3
"""Jukuravi CLI and compatibility imports backed by the pinned RAVI library."""
import importlib
import sys
from pathlib import Path
from ravi_bootstrap import require

require()
implementation = importlib.import_module("ravi.backends.juku.host")
implementation.DEFAULT_LOG_DIR = Path(__file__).resolve().parent / "sessions" / "default"
if __name__ == "__main__":
    raise SystemExit(implementation.main())
sys.modules[__name__] = implementation
