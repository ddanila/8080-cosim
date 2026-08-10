#!/usr/bin/env python3
"""Recover full-RAM evidence from an interrupted Jukuravi batch summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import protocol  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recover completed 32-byte LOAD/readback coverage and the contiguous "
            "delayed-read prefix from an interrupted Jukuravi batch JSON"
        )
    )
    parser.add_argument("session", type=Path)
    parser.add_argument("--start", type=lambda value: int(value, 16), default=0x4000)
    parser.add_argument("--end", type=lambda value: int(value, 16), default=0xC000)
    parser.add_argument("--byte", type=lambda value: int(value, 16), default=0x00)
    parser.add_argument("--chunk", type=int, default=protocol.LOADER_V2_MAX_DATA)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args()


def frame_payload(frame: dict[str, object]) -> bytes:
    value = frame.get("payload_hex")
    if not isinstance(value, str):
        raise ValueError("frame payload_hex is missing")
    return bytes.fromhex(value)


def analyze(
    summary: dict[str, object], *, start: int, end: int, value: int, chunk: int
) -> dict[str, object]:
    if not 0x4000 <= start < end <= 0xC000:
        raise ValueError("range must fit 4000..BFFF")
    if not 0 <= value <= 0xFF:
        raise ValueError("byte must fit 00..FF")
    if chunk <= 0 or (end - start) % chunk:
        raise ValueError("chunk must divide the selected range")
    frames = summary.get("frames")
    if not isinstance(frames, list):
        raise ValueError("session has no decoded frame list")

    expected_addresses = list(range(start, end, chunk))
    expected_crc = protocol.crc16_ccitt_false(bytes((value,)) * chunk)
    loads: dict[int, list[tuple[int, bytes]]] = {}
    reads: dict[int, list[tuple[int, bytes]]] = {}
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        payload = frame_payload(frame)
        if frame.get("type") == "0xB0" and len(payload) == 10:
            _, status, command, _, hi, lo, count, crc_hi, crc_lo, _ = payload
            address = (hi << 8) | lo
            crc = (crc_hi << 8) | crc_lo
            if (
                status == protocol.LOADER_STATUS_OK
                and command == protocol.TYPE_LOADER_V2_LOAD
                and count == chunk
                and start <= address < end
                and crc == expected_crc
            ):
                loads.setdefault(address, []).append((index, payload))
        elif frame.get("type") == "0xB1" and len(payload) == 6 + chunk:
            _, status, command, hi, lo, count = payload[:6]
            address = (hi << 8) | lo
            data = payload[6:]
            if (
                status == protocol.LOADER_STATUS_OK
                and command == protocol.TYPE_LOADER_V2_READ
                and count == chunk
                and start <= address < end
                and data == bytes((value,)) * chunk
            ):
                reads.setdefault(address, []).append((index, payload))

    immediate: dict[int, tuple[int, int]] = {}
    for address in expected_addresses:
        for load_index, _ in loads.get(address, []):
            later_reads = [
                read_index
                for read_index, _ in reads.get(address, [])
                if read_index > load_index
            ]
            if later_reads:
                immediate[address] = (load_index, min(later_reads))
                break

    last_immediate_index = max(
        (read_index for _, read_index in immediate.values()), default=-1
    )
    delayed_addresses: list[int] = []
    next_address = start
    for index, frame in enumerate(frames):
        if index <= last_immediate_index or next_address >= end:
            continue
        if not isinstance(frame, dict) or frame.get("type") != "0xB1":
            continue
        payload = frame_payload(frame)
        if len(payload) != 6 + chunk:
            continue
        _, status, command, hi, lo, count = payload[:6]
        address = (hi << 8) | lo
        if (
            status == protocol.LOADER_STATUS_OK
            and command == protocol.TYPE_LOADER_V2_READ
            and address == next_address
            and count == chunk
            and payload[6:] == bytes((value,)) * chunk
        ):
            delayed_addresses.append(address)
            next_address += chunk

    store_retries = sum(
        payload[-1]
        for records in loads.values()
        for _, payload in records
    )
    delayed_end = start + len(delayed_addresses) * chunk
    rows = Counter(
        address & 0x7F for address in range(start, delayed_end)
    )
    duplicate_load_results = sum(max(0, len(records) - 1) for records in loads.values())
    return {
        "session_status": summary.get("status"),
        "session_error": summary.get("error"),
        "image": summary.get("image"),
        "range": {"start": f"0x{start:04X}", "end_exclusive": f"0x{end:04X}"},
        "pattern_byte": f"0x{value:02X}",
        "chunk_bytes": chunk,
        "expected_chunks": len(expected_addresses),
        "load": {
            "complete": set(loads) == set(expected_addresses),
            "unique_chunks": len(loads),
            "bytes": len(loads) * chunk,
            "store_retries": store_retries,
            "duplicate_results": duplicate_load_results,
        },
        "immediate_readback": {
            "complete": set(immediate) == set(expected_addresses),
            "unique_chunks": len(immediate),
            "bytes": len(immediate) * chunk,
        },
        "delayed_readback": {
            "complete": delayed_end == end,
            "contiguous_chunks": len(delayed_addresses),
            "bytes": len(delayed_addresses) * chunk,
            "start": f"0x{start:04X}",
            "end_exclusive": f"0x{delayed_end:04X}",
            "all_bytes_match": True,
            "physical_rows_seen": len(rows),
            "minimum_samples_per_row": min(rows.values(), default=0),
            "maximum_samples_per_row": max(rows.values(), default=0),
        },
    }


def main() -> int:
    args = parse_args()
    summary = json.loads(args.session.read_text())
    result = analyze(
        summary,
        start=args.start,
        end=args.end,
        value=args.byte,
        chunk=args.chunk,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "JUKURAVI-PARTIAL-FULL-RAM: "
            f"load={result['load']['bytes']}/{args.end - args.start} "
            f"immediate={result['immediate_readback']['bytes']}/{args.end - args.start} "
            f"delayed={result['delayed_readback']['bytes']}/{args.end - args.start} "
            f"rows={result['delayed_readback']['physical_rows_seen']} "
            f"store-retries={result['load']['store_retries']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
