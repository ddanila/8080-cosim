#!/usr/bin/env python3
"""Guard the T35 CS00024 refresh, wrapper stops, and direct result."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "spinoffs" / "jukuravi" / "sessions"


def load(relative: str) -> dict[str, object]:
    path = SESSIONS / relative
    if not path.is_file():
        raise AssertionError(f"missing physical capture: {path}")
    return json.loads(path.read_text())


def require_t35(summary: dict[str, object]) -> None:
    image = summary.get("image")
    assert isinstance(image, dict)
    assert image.get("rom_version") == 0x1D
    assert image.get("crc16") == "45C4"


def main() -> int:
    first = load("cs00024-t35-first-physical/20260810T061734.589060Z.json")
    attach = load("cs00024-t35-idle-reattach-physical/20260810T061834.464961Z.json")
    require_t35(first)
    first_diagnostic = first.get("diagnostic_status")
    assert isinstance(first_diagnostic, dict)
    assert all(first_diagnostic.values())
    first_refresh = first.get("loader", {}).get("refresh")
    attach_refresh = attach.get("loader", {}).get("refresh")
    assert isinstance(first_refresh, dict) and isinstance(attach_refresh, dict)
    assert first_refresh.get("enabled") is True
    assert first_refresh.get("rows") == 128
    assert first_refresh.get("rx_refresh_calls") == 1752
    assert attach_refresh.get("rx_refresh_calls") == 40414
    assert attach.get("loader", {}).get("attached") is True

    cases = (
        (
            "cs00024-t35-batch-physical/20260810T063013.783535Z.json",
            "10",
            "7F00",
        ),
        (
            "cs00024-t35-batch-physical/20260810T150610.267813Z.json",
            "00",
            "7F00",
        ),
        (
            "cs00024-t35-batch-safe-physical/20260810T151126.497325Z.json",
            "10",
            "7F00",
        ),
        (
            "cs00024-t35-increment-6f-physical/20260810T154931.444912Z.json",
            "00",
            "6F00",
        ),
    )
    for relative, d57_mask, wrapper_address in cases:
        summary = load(relative)
        require_t35(summary)
        diagnostic = summary.get("diagnostic_status")
        assert isinstance(diagnostic, dict)
        assert diagnostic.get("peripheral_fault_mask_hex") == d57_mask
        assert diagnostic.get("d57") is (d57_mask == "00")
        results = summary.get("batch", {}).get("results")
        assert isinstance(results, list)
        names = {item.get("name") for item in results}
        assert {"verified-return", "cpu-host-timebase"} <= names
        assert all(item.get("verdict") in {"pass", "measured"} for item in results)
        frames = summary.get("frames")
        assert isinstance(frames, list) and len(frames) >= 2
        assert frames[-2].get("payload_hex") == (
            f"030026{wrapper_address}0CCDA907CD0040F5CDA907F1C9"
        )
        assert frames[-1].get("type") == "0xB0"
        assert frames[-1].get("payload_hex") == (f"0400280A{wrapper_address}00000000")
        error = str(summary.get("error"))
        assert "timeout" in error or "interrupted" in error

    direct = load("cs00024-t35-increment-direct-physical/20260810T155952.521638Z.json")
    require_t35(direct)
    direct_diagnostic = direct.get("diagnostic_status")
    assert isinstance(direct_diagnostic, dict)
    assert all(
        direct_diagnostic.get(name) is True
        for name in ("pic", "ppi", "d54", "d55", "d57", "ram_4000", "ram_c000")
    )
    direct_results = direct.get("batch", {}).get("results")
    assert isinstance(direct_results, list)
    direct_by_name = {item.get("name"): item for item in direct_results}
    assert direct_by_name["verified-return"].get("verdict") == "pass"
    assert direct_by_name["cpu-host-timebase"].get("cpu_clock_mhz") == 1.703357
    register = direct_by_name["cpu-increment-registers"]
    assert register.get("verdict") == "fail"
    assert register.get("expected_hex") == (
        "58313243A55555550010011A015A019A011A555555555555"
    )
    assert register.get("observed_hex") == (
        "58313243A55555555555011A55552020011A555555555555"
    )
    operation = register.get("operation")
    assert isinstance(operation, dict)
    assert "refresh_wrapper" not in operation
    assert all(chunk.get("verified") is True for chunk in operation.get("chunks", []))
    run = operation.get("run")
    assert isinstance(run, dict)
    assert run.get("address") == "0x4000"
    assert run.get("returned") is True
    assert run.get("return_replays") == 0
    assert direct.get("batch", {}).get("direct_probes") == ["cpu-increment-registers"]

    lanes = load("cs00024-t35-ram-lanes-physical/20260810T161602.033997Z.json")
    require_t35(lanes)
    assert "timeout waiting for LOAD" in str(lanes.get("error"))
    readbacks = [
        str(frame.get("payload_hex"))[12:]
        for frame in lanes.get("frames", [])
        if frame.get("type") == "0xB1"
        and str(frame.get("payload_hex", "")).startswith("0200264D0020")
    ]
    assert readbacks == [
        "0000FFFFFFFF00000000FFFFFFFF00000000FFFFFFFF00000000020000FF0000",
        "FFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFB",
        "AA00FFFFFFFF00000000FFFFFFFF00000000FFFFFFFF00000000AA55AAFF0000",
    ]
    expected = [bytes(32), bytes((0xFF,)) * 32, bytes((0xAA, 0x55)) * 16]
    xor_masks = [
        bytes(want ^ got for want, got in zip(pattern, bytes.fromhex(observed)))
        for pattern, observed in zip(expected, readbacks)
    ]
    assert [sum(mask != 0 for mask in masks) for masks in xor_masks] == [14, 3, 28]
    assert all(any(masks) for masks in xor_masks)
    assert xor_masks[0][0] == 0 and xor_masks[2][0] == 0
    assert set().union(*(set(masks) for masks in xor_masks)) >= {
        0x01,
        0x02,
        0x04,
        0x10,
        0x55,
        0xAA,
        0xFF,
    }
    print(
        "JUKURAVI-T35-PHYSICAL: PASS "
        "(refresh/reattach; D57 masks 10/00/10/00; "
        "three 7F00 plus one 6F00 RUN-ACK/no-RETURN stops; "
        "direct 4000 returns a non-D1 register result; "
        "six-second lane capture proves shared row decay)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
