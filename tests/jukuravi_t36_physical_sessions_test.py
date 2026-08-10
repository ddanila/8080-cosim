#!/usr/bin/env python3
"""Pin the bounded claims recovered from both physical T36 sessions."""

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
LOCAL_SESSION = (
    ROOT
    / "spinoffs"
    / "jukuravi"
    / "sessions"
    / "cs00024-t36-local-full-physical"
    / "20260810T205728.130960Z.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_jukuravi_partial_full_ram as analyzer  # noqa: E402


def objects(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


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

    local_summary = json.loads(LOCAL_SESSION.read_text())
    assert local_summary["status"] == "ok"
    assert local_summary["error"] is None
    assert local_summary["image"] == {
        "protocol_version": 1,
        "rom_version": 0x1E,
        "crc16": "C617",
    }
    assert local_summary["started_utc"] == "2026-08-10T20:57:28.130960Z"
    assert local_summary["finished_utc"] == "2026-08-10T21:42:28.968841Z"
    assert local_summary["attempts"][0]["decoded_frames"] == 746
    diagnostic = local_summary["diagnostic_status"]
    assert diagnostic["peripheral_fault_mask_hex"] == "00"
    assert all(
        diagnostic[name]
        for name in ("pic", "ppi", "d54", "d55", "d57", "ram_4000", "ram_c000")
    )

    batch = local_summary["batch"]
    assert batch["rom_profile"] == "t36"
    assert batch["rom_version"] == "0x1E"
    assert batch["rom_crc16"] == "0xC617"
    assert batch["overall_verdict"] == "findings"
    assert batch["core_failures"] == ["d57-raw"]
    results = {item["name"]: item for item in batch["results"]}
    assert set(results) == {
        "verified-return",
        "cpu-host-timebase",
        "a12-write-map",
        "a12-lhld",
        "a12-instruction",
        "a12-ready-classes",
        "a12-boundary",
        "cpu-increment-registers",
        "local-full-ram-sweep",
        "execution-address",
        "d57-raw",
    }
    assert results["cpu-host-timebase"]["cpu_clock_mhz"] == 1.701558
    assert results["cpu-host-timebase"]["delta_tstates"] == 1_078_000
    assert results["cpu-host-timebase"]["delta_seconds"] == 0.633537
    assert all(
        item["verdict"] == "pass"
        for name, item in results.items()
        if name not in ("cpu-host-timebase", "d57-raw")
    )

    local = results["local-full-ram-sweep"]
    assert local["start"] == "0x4000"
    assert local["end_exclusive"] == "0xC000"
    assert local["bytes_per_pattern"] == 0x8000
    assert local["locally_tested_bytes_per_pattern"] == 0xE000
    assert local["hold_ms"] == 6000.0
    assert local["refresh_interval_bytes"] == 128
    assert local["failed_patterns"] == []
    assert [item["name"] for item in local["patterns"]] == [
        "zeros",
        "ones",
        "checkerboard",
        "address-xor",
    ]
    for pattern in local["patterns"]:
        assert pattern["verdict"] == "pass"
        assert pattern["mismatching_bytes"] == 0
        assert pattern["xor_or"] == "0x00"
        assert pattern["candidate_packages"] == []
        assert [stage["stage"] for stage in pattern["stages"]] == [
            "low-resident",
            "high-resident",
        ]
        assert [
            (stage["start"], stage["end_exclusive"]) for stage in pattern["stages"]
        ] == [
            ("0x5000", "0xC000"),
            ("0x4000", "0xB000"),
        ]
        assert all(
            stage["bytes"] == 0x7000
            and stage["verdict"] == "pass"
            and stage["mismatching_bytes"] == 0
            and stage["xor_or"] == "0x00"
            and stage["first_mismatch"] is None
            and stage["refresh_interval_bytes"] == 128
            for stage in pattern["stages"]
        )

    retention = batch["retention_sweep"]
    assert retention[0] == {
        "attempts": 1,
        "cookie_bytes": 16,
        "echoed_hex": "524554454E54494F4E2D414745212121",
        "guard_ms": 6.0,
        "recovery": "pass",
        "recovery_attempts": 1,
        "seconds": 1.298094,
        "verdict": "pass",
    }
    assert retention[1]["guard_ms"] == 12.0
    assert retention[1]["seconds"] == 2.528204
    assert retention[1]["verdict"] == "fail"
    assert retention[1]["recovery"] == "fail"
    assert "bad_crc" in retention[1]["error"]

    d57 = results["d57-raw"]
    assert d57["verdict"] == "fail"
    assert d57["observed_hex"] == ("44353752A5010800" + "FD3DFC3C9999" * 8)
    assert d57["operation"]["run"]["return_seconds"] == 0.127933
    assert d57["operation"]["run"]["returned"] is True
    assert d57["operation"]["run"]["result"]["hex"] == d57["observed_hex"]
    assert d57["bad_samples"] == [
        {"channel": 2, "high": "99", "low": "99", "repetition": index}
        for index in range(1, 9)
    ]

    chunks = [item for item in objects(local_summary) if "store_retries" in item]
    assert len(chunks) == 282
    assert sum(int(item["bytes"]) for item in chunks) == 8642
    assert sum(int(item["store_retries"]) for item in chunks) == 0
    assert sum(int(item["attempts"]) > 1 for item in chunks) == 16
    assert sum(int(item["readback_attempts"]) > 1 for item in chunks) == 2
    assert max(int(item["attempts"]) for item in chunks) == 3
    assert max(int(item["readback_attempts"]) for item in chunks) == 3

    for key in ("rx_log", "tx_log"):
        capture = LOCAL_SESSION.with_name(local_summary[key])
        assert capture.is_file()
        expected_size = local_summary[
            "received_bytes" if key == "rx_log" else "transmitted_bytes"
        ]
        assert capture.stat().st_size == expected_size

    print(
        "JUKURAVI-T36-PHYSICAL: PASS "
        "(wire zero prefix plus complete local four-pattern 32 KiB proof; "
        "parser boundary; D57 channel-2 signature)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
