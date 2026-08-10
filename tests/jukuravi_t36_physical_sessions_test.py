#!/usr/bin/env python3
"""Pin the bounded claims recovered from the first physical T36 session."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = (
    ROOT
    / "spinoffs"
    / "jukuravi"
    / "sessions"
    / "cs00024-t36-full-physical"
    / "20260810T174121.361256Z.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_jukuravi_partial_full_ram as analyzer  # noqa: E402


def main() -> int:
    summary = json.loads(SESSION.read_text())
    assert summary["status"] == "error"
    assert summary["error"] == "interrupted by operator"
    assert summary["image"] == {
        "protocol_version": 1,
        "rom_version": 0x1E,
        "crc16": "C617",
    }
    diagnostic = summary["diagnostic_status"]
    assert diagnostic["peripheral_fault_mask_hex"] == "00"
    assert all(
        diagnostic[name]
        for name in ("pic", "ppi", "d54", "d55", "d57", "ram_4000", "ram_c000")
    )
    results = {item["name"]: item for item in summary["batch"]["results"]}
    assert set(results) == {
        "verified-return",
        "cpu-host-timebase",
        "a12-write-map",
        "a12-lhld",
        "a12-instruction",
        "a12-ready-classes",
        "a12-boundary",
        "cpu-increment-registers",
    }
    assert results["verified-return"]["verdict"] == "pass"
    assert results["cpu-host-timebase"]["verdict"] == "measured"
    assert results["cpu-host-timebase"]["cpu_clock_mhz"] == 1.702797
    assert all(
        results[name]["verdict"] == "pass"
        for name in results
        if name not in ("cpu-host-timebase",)
    )

    recovered = analyzer.analyze(summary, start=0x4000, end=0xC000, value=0, chunk=32)
    assert recovered["load"] == {
        "complete": True,
        "unique_chunks": 1024,
        "bytes": 0x8000,
        "store_retries": 0,
        "duplicate_results": 0,
    }
    assert recovered["immediate_readback"] == {
        "complete": True,
        "unique_chunks": 1024,
        "bytes": 0x8000,
    }
    delayed = recovered["delayed_readback"]
    assert delayed == {
        "complete": False,
        "contiguous_chunks": 54,
        "bytes": 1728,
        "start": "0x4000",
        "end_exclusive": "0x46C0",
        "all_bytes_match": True,
        "physical_rows_seen": 128,
        "minimum_samples_per_row": 13,
        "maximum_samples_per_row": 14,
    }
    for key in ("rx_log", "tx_log"):
        capture = SESSION.with_name(summary[key])
        assert capture.is_file() and capture.stat().st_size > 400_000

    print(
        "JUKURAVI-T36-PHYSICAL: PASS "
        "(clean boot/probes; full zero write+verify; bounded 1728-byte delayed prefix)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
