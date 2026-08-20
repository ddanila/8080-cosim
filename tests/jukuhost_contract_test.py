#!/usr/bin/env python3
"""Prove that the frozen C-host migration vectors match the Python baseline."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.janet_disk_server import (  # noqa: E402
    REPLY_SYNC,
    SECTOR_ORDER,
    checksum,
    encode_v3_record,
    record_offset,
)
from tools.janet_fastboot import (  # noqa: E402
    checked_frame,
    crc16_ccitt,
    crc16_ibm,
    fletcher16,
)
from tools.janet_netboot import boot_frames, frame  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "jukuhost" / "python-era-v1.txt"


def load_fixture() -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, raw in enumerate(FIXTURE.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise AssertionError(f"malformed fixture line {line_number}")
        key, value = line.split("=", 1)
        if not key or key in result:
            raise AssertionError(f"invalid fixture key on line {line_number}")
        result[key] = value
    return result


def packet(body: bytes) -> bytes:
    return body + bytes((checksum(body),))


def main() -> int:
    actual: dict[str, str] = {"schema": "jukuhost-python-era-v1"}
    actual["janet_poll_01_02"] = frame(1, 2, 0x0C).hex()
    actual["janet_ack_01_02"] = frame(1, 2, 0x08).hex()
    actual["janet_data_01_02_abc"] = frame(1, 2, 0x07, b"abc").hex()
    for index, encoded in enumerate(boot_frames(bytes(range(128)))):
        actual[f"boot_raw_frame_{index}"] = encoded.hex()
    actual["crc16_ccitt_123456789"] = f"{crc16_ccitt(b'123456789'):04x}"
    actual["crc16_ibm_123456789"] = f"{crc16_ibm(b'123456789'):04x}"
    actual["fletcher_range16"] = bytes(fletcher16(bytes(range(16)))).hex()
    actual["fast_ready_v16"] = checked_frame(ord("R"), bytes((16, 1))).hex()
    actual["fast_probe_v16"] = checked_frame(ord("Q"), bytes((16, 1))).hex()
    actual["fast_reply_seq0_ok"] = checked_frame(ord("A"), bytes((0, 0))).hex()
    request = packet(b"JD" + bytes((0x11, 0x22, 0, 2, 0, 1)))
    reply = packet(REPLY_SYNC + bytes((0x22, 0)) + bytes(range(8)))
    actual["n3_read_req"] = request.hex()
    actual["n3_read_reply_8"] = reply.hex()
    actual["n3_encode_fill"] = encode_v3_record(
        b"\xA5" * 128, deleted_directory=False
    ).hex()
    deleted = bytearray(range(128))
    deleted[0::32] = b"\xE5" * 4
    actual["n3_encode_deleted"] = encode_v3_record(
        bytes(deleted), deleted_directory=True
    ).hex()
    actual["n3_encode_raw"] = encode_v3_record(
        bytes(range(128)), deleted_directory=False
    ).hex()
    actual["sector_order"] = ",".join(str(value) for value in SECTOR_ORDER)
    actual["offset_t2_s1"] = str(record_offset(2, 1))

    expected = load_fixture()
    if actual != expected:
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        changed = sorted(
            key for key in actual.keys() & expected.keys()
            if actual[key] != expected[key]
        )
        raise AssertionError(
            f"frozen host contract differs: missing={missing}, "
            f"extra={extra}, changed={changed}"
        )
    print(f"JUKUHOST-CONTRACT-TEST: PASS ({len(actual)} frozen values)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
