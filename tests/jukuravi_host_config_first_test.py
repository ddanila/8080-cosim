#!/usr/bin/env python3
"""Guard the optional short-CONFIG-before-PROBE loader policy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import host
import protocol


class NullLogs:
    def rx(self, _data: bytes) -> None:
        pass

    def tx(self, _data: bytes) -> None:
        pass


class OrderedSession(host.HostSession):
    def __init__(self, config_first: bool) -> None:
        read_fd, write_fd = os.pipe()
        os.close(write_fd)
        super().__init__(
            read_fd,
            NullLogs(),
            1,
            1,
            None,
            None,
            False,
            loader_guard_seconds=0,
            loader_votes=1,
            loader_config_first=config_first,
        )
        self.calls: list[str] = []

    def close(self) -> None:
        os.close(self.fd)

    def _loader_v2_result_command(
        self,
        record_type: int,
        transaction: int,
        body: bytes,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[dict[str, int], int, int]:
        del transaction, cursor, timeout, description
        if record_type != protocol.TYPE_LOADER_V2_CONFIG or body != b"\x01":
            raise AssertionError("unexpected result command")
        self.calls.append("CONFIG")
        return (
            {
                "status": protocol.LOADER_STATUS_OK,
                "count": 1,
            },
            0,
            1,
        )

    def _loader_v2_data_command(
        self,
        record_type: int,
        transaction: int,
        body: bytes,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[dict[str, int], bytes, int, int]:
        del transaction, cursor, timeout, description
        if record_type != protocol.TYPE_LOADER_V2_PROBE:
            raise AssertionError("unexpected data command")
        self.calls.append("PROBE")
        return {"status": protocol.LOADER_STATUS_OK}, body, 0, 1


def run_case(config_first: bool, expected: list[str], order: str) -> None:
    session = OrderedSession(config_first)
    loader: dict[str, object] = {
        "ready": {"max_data_bytes": protocol.LOADER_V2_MAX_DATA},
        "chunks": [],
        "run": {"requested": False, "address": None, "acknowledged": False},
        "heartbeat": None,
    }
    try:
        session._run_loader_v2(
            b"",
            0x4000,
            None,
            0,
            1,
            0,
            1,
            loader,
            protocol.LOADER_V2_MAX_DATA,
        )
    finally:
        session.close()
    if session.calls != expected:
        raise SystemExit(f"order differs: {session.calls!r} != {expected!r}")
    if loader.get("config", {}).get("order") != order:
        raise SystemExit(f"config evidence differs: {loader.get('config')!r}")
    if loader.get("probe", {}).get("cookie_hex") != "5432380055AAC6C7":
        raise SystemExit("exact PROBE cookie evidence is absent")
    if session.host_symbol_repetitions != 1:
        raise SystemExit("configured one-vote width was not retained")


def main() -> int:
    run_case(True, ["CONFIG", "PROBE"], "before_probe")
    run_case(False, ["PROBE", "CONFIG"], "after_probe")
    print("JUKURAVI-HOST-CONFIG-FIRST: PASS (explicit recovery; default unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
