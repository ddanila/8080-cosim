#!/usr/bin/env python3
"""Run the monitor contract while TxEMPTY is permanently low after startup."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(Path(__file__).parent), str(FIRMWARE), str(FIRMWARE.parent)]

import build_d0_txready as firmware  # noqa: E402
import jukuravi_t29_recovery_test as shared  # noqa: E402


if __name__ == "__main__":
    # The initial local USART sanity test completes before byte 30. Thereafter
    # status bit 2 is forced low, reproducing the T29 physical-board stop while
    # leaving TxRDY and actual transmitted data healthy.
    os.environ["JUKU_USART_FAULT"] = "tx_empty_low_after:30"
    shared.firmware = firmware
    shared.TEST_LABEL = "JUKURAVI-T30-TXEMPTY"
    raise SystemExit(shared.main())
