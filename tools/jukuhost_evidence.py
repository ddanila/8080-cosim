#!/usr/bin/env python3
"""Convert a native JUKUHOST capture into modern JSON acceptance evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

CAPTURE_HEADER = 16
RECORD_OVERHEAD = 16
REQUEST = re.compile(
    r"^request op=([0-9A-F]{2}) seq=([0-9A-F]{2}) drive=(\d+) "
    r"track=(\d+) sector=(\d+) status=(\d+) records=(\d+) "
    r"request-bytes=(\d+) reply-bytes=(\d+) duplicate=([01])$"
)


class EvidenceError(ValueError):
    """The capture is truncated, corrupt, or lacks required evidence."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path: Path) -> tuple[int, list[dict[str, object]]]:
    data = path.read_bytes()
    if len(data) < CAPTURE_HEADER or data[:7] != b"JHCAP1\x01":
        raise EvidenceError("capture header is missing or unsupported")
    started_ms = struct.unpack_from("<Q", data, 8)[0]
    result: list[dict[str, object]] = []
    position = CAPTURE_HEADER
    while position < len(data):
        if position + RECORD_OVERHEAD > len(data):
            raise EvidenceError(f"truncated record header at {position}")
        kind, flags, length = struct.unpack_from("<BBH", data, position)
        if kind not in (1, 2, 3):
            raise EvidenceError(f"invalid record type {kind} at {position}")
        end = position + RECORD_OVERHEAD + length
        if end > len(data):
            raise EvidenceError(f"truncated record payload at {position}")
        expected = struct.unpack_from("<I", data, end - 4)[0]
        actual = zlib.crc32(data[position:end - 4])
        if actual != expected:
            raise EvidenceError(f"record CRC differs at {position}")
        result.append({
            "kind": kind,
            "flags": flags,
            "elapsed_ms": struct.unpack_from("<Q", data, position + 4)[0],
            "payload": data[position + 12:end - 4],
        })
        position = end
    return started_ms, result


def request_records(started_ms: int,
                    captured: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for record in captured:
        if record["kind"] != 3:
            continue
        payload = bytes(record["payload"]).decode("ascii", "strict")
        match = REQUEST.fullmatch(payload)
        if match is None:
            continue
        values = [int(value, 16 if index < 2 else 10)
                  for index, value in enumerate(match.groups())]
        elapsed_ms = int(record["elapsed_ms"])
        result.append({
            "schema": "juku-netdisk-request-trace-v1",
            "monotonic_seconds": round((started_ms + elapsed_ms) / 1000, 6),
            "elapsed_seconds": round(elapsed_ms / 1000, 6),
            "operation": values[0],
            "sequence": values[1],
            "drive": values[2],
            "track": values[3],
            "sector": values[4],
            "status": values[5],
            "records": values[6],
            "request_bytes": values[7],
            "reply_bytes": values[8],
            "duplicate": values[9] == 1,
        })
    return result


def atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_requests(path: Path, requests: list[dict[str, object]]) -> None:
    atomic_text(path, "".join(
        json.dumps(record, sort_keys=True) + "\n" for record in requests
    ))


def write_boot(path: Path, capture: Path, started_ms: int,
               captured: list[dict[str, object]],
               requests: list[dict[str, object]], args: argparse.Namespace) -> None:
    if args.system is None or args.fast_stage is None:
        raise EvidenceError("boot evidence requires --system and --fast-stage")
    first = next((record for record in requests
                  if 0x11 <= int(record["operation"]) <= 0x15), None)
    if first is None:
        raise EvidenceError("capture contains no disk request confirming boot")
    messages = [bytes(record["payload"]).decode("ascii", "replace")
                for record in captured if record["kind"] == 3]
    if not any(message.startswith("Fastboot V16 complete") or
               message.startswith("V16 final reply not seen")
               for message in messages):
        raise EvidenceError("capture contains no completed V16 transfer")
    confirmed = any(message.startswith("Fastboot V16 complete")
                    for message in messages)
    value = {
        "schema": "juku-janet-boot-result-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture": str(capture.resolve()),
        "serial": args.serial,
        "network_rom": True,
        "boot_baud": 19200,
        "effective_boot_baud": 19200,
        "disk_baud": args.disk_baud,
        "disk_protocol": args.disk_protocol,
        "system": str(args.system.resolve()),
        "system_sha256": sha256(args.system),
        "fast_stage": str(args.fast_stage.resolve()),
        "fast_stage_sha256": sha256(args.fast_stage),
        "completion_confirmed": int(confirmed),
        "capture_started_monotonic": round(started_ms / 1000, 6),
        "first_disk_request": {
            "monotonic_seconds": first["monotonic_seconds"],
            "elapsed_seconds": first["elapsed_seconds"],
            "operation": first["operation"],
            "sequence": first["sequence"],
        },
    }
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("capture", type=Path)
    result.add_argument("--requests-jsonl", type=Path, required=True)
    result.add_argument("--boot-result", type=Path)
    result.add_argument("--system", type=Path)
    result.add_argument("--fast-stage", type=Path)
    result.add_argument("--serial", default="")
    result.add_argument("--disk-baud", type=int, default=19200)
    result.add_argument("--disk-protocol", type=int, default=3)
    return result


def main() -> int:
    args = parser().parse_args()
    started_ms, captured = records(args.capture)
    requests = request_records(started_ms, captured)
    write_requests(args.requests_jsonl, requests)
    if args.boot_result is not None:
        write_boot(args.boot_result, args.capture, started_ms, captured,
                   requests, args)
    print(
        f"JUKUHOST-EVIDENCE: PASS ({len(captured)} capture records, "
        f"{len(requests)} requests)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, OSError, UnicodeError) as error:
        raise SystemExit(f"JUKUHOST-EVIDENCE: FAIL: {error}") from error
