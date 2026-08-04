#!/usr/bin/env python3
"""Prove T32 normal execution stays below its deliberate upper-ROM probes."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(Path(__file__).parent), str(FIRMWARE), str(FIRMWARE.parent)]

import build_d0_waitclass as firmware  # noqa: E402
import jukuravi_t29_recovery_test as shared  # noqa: E402


if __name__ == "__main__":
    os.environ["JUKU_ROM_EXEC_RESET_AT"] = "0x1000"
    os.environ["JUKU_PIT_FAULT"] = "14:00:80"
    shared.firmware = firmware
    shared.TEST_LABEL = "JUKURAVI-T32-LOW4K"
    shared.PROGRESS_MARKERS = ()
    shared.SUCCESS_DETAIL = (
        "normal execution below 1000h; deliberate upper probes excluded; "
        "TxRDY recovery; CALL/RET; A/RAM result"
    )
    raise SystemExit(shared.main())
