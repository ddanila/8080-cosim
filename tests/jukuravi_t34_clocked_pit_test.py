#!/usr/bin/env python3
"""Guard T34's clock-safe D55 metadata and complete T31-compatible monitor."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(Path(__file__).parent), str(FIRMWARE), str(FIRMWARE.parent)]

import build_d0_clocked_pit as firmware  # noqa: E402
import build_d0_low4k as t31  # noqa: E402
import jukuravi_t29_recovery_test as shared  # noqa: E402


def verify_build_contract() -> None:
    image, metadata = firmware.build()
    if hashlib.sha256(image).hexdigest() != (
        "63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5"
    ):
        raise AssertionError("T34 image identity changed")
    if metadata["checksum"] != 0xA637:
        raise AssertionError("T34 self-CRC changed")
    if metadata["loader_extension_end"] != 0x0FFF:
        raise AssertionError("T34 crossed the proven low-4K execution boundary")
    if metadata["d55_clock_source_writes"] != list(
        firmware.D55_CLOCK_SOURCE_WRITES
    ):
        raise AssertionError("T34 D54 source setup metadata changed")
    if metadata["d55_settle_iterations"] != 40:
        raise AssertionError("T34 D55 settle loop changed")

    old_image, old_metadata = t31.build()
    if hashlib.sha256(old_image).hexdigest() != (
        "a4fed9185616bbfbef22ab6f0b18202e6d79ad7dbe3b7c46a77a700d3af3676c"
    ) or old_metadata["checksum"] != 0x72EF:
        raise AssertionError("historical T31 was not preserved byte-exactly")


if __name__ == "__main__":
    verify_build_contract()
    os.environ["JUKU_ROM_EXEC_RESET_AT"] = "0x1000"
    os.environ["JUKU_PIT_FAULT"] = "14:00:80"
    shared.firmware = firmware
    shared.TEST_LABEL = "JUKURAVI-T34-CLOCKED-PIT"
    shared.PROGRESS_MARKERS = ()
    shared.SUCCESS_DETAIL = (
        "clock-source metadata; exact T31 preserved; low-4K monitor; "
        "D55-path bit; TxRDY recovery; CALL/RET; A/RAM result"
    )
    raise SystemExit(shared.main())
