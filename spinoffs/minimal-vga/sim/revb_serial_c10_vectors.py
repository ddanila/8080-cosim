#!/usr/bin/env python3
"""Build the one C10-compatible VJUGA serial request/reply vector (R5.S3)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import protocol  # noqa: E402


COOKIE = b"VJUGA-C10"
TRANSACTION = 0x5A
REQUEST_HEX = "A55A230C5A564A5547412D4331309FDBED"
REPLY_HEX = "A55AB10F5A0023000009564A5547412D433130DE"


def vectors() -> tuple[bytes, bytes]:
    request = protocol.encode_loader_v2_command(
        protocol.TYPE_LOADER_V2_PROBE, TRANSACTION, COOKIE
    )
    reply_payload = bytes(
        (
            TRANSACTION,
            protocol.LOADER_STATUS_OK,
            protocol.TYPE_LOADER_V2_PROBE,
            0,
            0,
            len(COOKIE),
        )
    ) + COOKIE
    reply = protocol.encode_frame(protocol.TYPE_LOADER_V2_DATA, reply_payload)
    if request.hex().upper() != REQUEST_HEX or reply.hex().upper() != REPLY_HEX:
        raise SystemExit("C10 protocol vectors changed; review the ABI before updating R5.S3")
    return request, reply


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    request, reply = vectors()
    c10_meta = json.loads(
        (ROOT / "spinoffs/jukuravi/network-rom/juku-network-rom-abi1.4-c10.json").read_text()
    )
    abi = c10_meta.get("abi", {})
    if (
        "c10" not in c10_meta.get("candidate", "").lower()
        or abi.get("major") != 1
        or abi.get("minor") != 4
    ):
        raise SystemExit("the adopted C10 metadata is not ABI 1.4")
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for name, data in (("request.hex", request), ("reply.hex", reply)):
            (args.out_dir / name).write_text("".join(f"{byte:02x}\n" for byte in data))
    print(
        "R5.S3 C10 vectors PASS: "
        f"request={len(request)} bytes/{hashlib.sha256(request).hexdigest()} "
        f"reply={len(reply)} bytes/{hashlib.sha256(reply).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
