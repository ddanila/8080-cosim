#!/usr/bin/env python3
"""Pin the first physical Ekta4401 service-loader and corrected D57 control."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "spinoffs" / "jukuravi" / "sessions"
FIRST_J = (
    SESSIONS
    / "cs00015-ekta4401-first-j-physical"
    / "20260811T194722.762604Z.json"
)
LEGACY_D57 = (
    SESSIONS
    / "cs00015-ekta4401-d57-control-physical"
    / "20260811T195018.477043Z.json"
)
CORRECTED_D57 = (
    SESSIONS
    / "cs00015-ekta4401-d57-verrtr-control-physical"
    / "20260811T195525.505743Z.json"
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def check_capture_files(path: Path, session: dict[str, object]) -> None:
    for log_key, size_key in (("rx_log", "received_bytes"), ("tx_log", "transmitted_bytes")):
        capture = path.with_name(str(session[log_key]))
        assert capture.is_file()
        assert capture.stat().st_size == session[size_key]


def main() -> int:
    first = load(FIRST_J)
    assert first["status"] == "ok"
    assert first["host_transport"]["handshake_mismatches"] == []
    loader = first["loader"]
    assert loader["attached"] is True
    assert loader["status"] == "control_complete"
    assert loader["ready"]["api_version"] == 2
    assert loader["ready"]["default_votes"] == 1
    assert loader["probe"]["attempts"] == 1
    assert loader["refresh"] == {
        "api": "0x07A9",
        "attempts": 1,
        "enabled": True,
        "operation": "query",
        "policy_flags": "0x07",
        "row_start": "0x00",
        "rows": 128,
        "rx_refresh_calls": 5485,
        "transaction": 1,
    }
    check_capture_files(FIRST_J, first)

    legacy = load(LEGACY_D57)
    legacy_hex = legacy["loader"]["run"]["result"]["hex"]
    assert legacy["status"] == "ok"
    assert legacy["host_transport"]["handshake_mismatches"] == []
    assert legacy_hex == (
        "44353752A5010800"
        "FD3DFC3CD3D3FD3DFC3CD3D3FD3DFC3CD3D3FD3DFC3CD33F"
        "FD3DFC3C3F3FFD3DFC3C3F3FFD3DFC3C3F3FFD3DFC3C3F3F"
    )
    check_capture_files(LEGACY_D57, legacy)

    corrected = load(CORRECTED_D57)
    corrected_loader = corrected["loader"]
    corrected_hex = corrected_loader["run"]["result"]["hex"]
    assert corrected["status"] == "ok"
    assert corrected["host_transport"]["handshake_mismatches"] == []
    assert corrected_loader["bytes"] == 216
    assert corrected_loader["sha256"] == (
        "24b8fa3ae6ae1b72f3618fb0e495216bc7cd3aab79f34ea95b4c0dbc11b35746"
    )
    assert corrected_loader["run"]["returned"] is True
    assert corrected_loader["run"]["return_replays"] == 0
    assert corrected_hex == "44353753A5020840" + "FD3DFC3CFE3E" * 8
    check_capture_files(CORRECTED_D57, corrected)

    print(
        "JUKURAVI-EKTA4401-PHYSICAL: PASS "
        "(API-v2 J attach; legacy timing capture retained; corrected "
        "D57 /VER RTR control passes 8/8)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
