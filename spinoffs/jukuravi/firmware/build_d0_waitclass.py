#!/usr/bin/env python3
"""Build T32: the proven low-4K monitor plus an upper-ROM wait-class matrix."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_resilient as base
from build_d5_loader_v5 import emit_loader as emit_loader_v5


protocol = base.protocol


OUTPUT = base.HERE / "diag-d0-waitclass.bin"
DOS_OUTPUT = base.HERE / "dos" / "T32HOST.BIN"
INFO_OUTPUT = base.HERE / "dos" / "T32INFO.TXT"
ROM_VERSION = 0x1B
IDENTITY = b"JUKURAVI-D0-WAITCLASS-MONITOR-2400-1\0"
LOADER_ENTRY = 0x0A0C
RESULT_ADDRESS = 0x4100

# Page-aligned representatives cover the full upper-half {A11,A10,A9}
# matrix.  Each entry records its high address byte at 4100h, then executes
# JMP 0A0Ch and returns to the resident loader.  The unique result byte proves
# that the requested upper-ROM address actually executed after reattachment.
TRAMPOLINES = {
    0x1100: "CAS-gated A11=0 A10=0 A9=0",
    0x1200: "no-wait A11=0 A10=0 A9=1",
    0x1400: "always-wait A11=0 A10=1 A9=0",
    0x1600: "always-wait A11=0 A10=1 A9=1",
    0x1800: "CAS-gated A11=1 A10=0 A9=0",
    0x1A00: "no-wait A11=1 A10=0 A9=1",
    0x1C00: "always-wait A11=1 A10=1 A9=0",
    0x1E00: "always-wait A11=1 A10=1 A9=1",
}


def trampoline(address: int) -> bytes:
    marker = address >> 8
    return bytes(
        (
            0x3E, marker,  # MVI A,marker
            0x32, RESULT_ADDRESS & 0xFF, RESULT_ADDRESS >> 8,  # STA 4100h
            0xC3, LOADER_ENTRY & 0xFF, LOADER_ENTRY >> 8,  # JMP 0A0Ch
        )
    )


def _refresh_protocol_checksum(
    image: bytearray, metadata: dict[str, object]
) -> None:
    banner_offset = int(metadata["banner_offset"])
    ack_offset = int(metadata["ack_offset"])
    checksum_image = bytearray(image)
    for offset in (
        banner_offset + 6,
        banner_offset + 7,
        banner_offset + 8,
        ack_offset + 6,
        ack_offset + 7,
        ack_offset + 8,
    ):
        checksum_image[offset] = 0
    checksum = protocol.crc16_ccitt_false(bytes(checksum_image))
    payload = bytes(
        (protocol.PROTOCOL_VERSION, ROM_VERSION, checksum >> 8, checksum & 0xFF)
    )
    banner = protocol.encode_frame(protocol.TYPE_BANNER, payload)
    ack = protocol.encode_frame(protocol.TYPE_ACK, payload)
    image[banner_offset:banner_offset + len(banner)] = banner
    image[ack_offset:ack_offset + len(ack)] = ack
    metadata.update(checksum=checksum, banner=banner, ack=ack)


def build() -> tuple[bytes, dict[str, object]]:
    saved = (
        base.ROM_VERSION,
        base.IDENTITY,
        base.SOLICITED_INPUT,
        base.FILTER_INVALID_SYMBOLS,
        base.CLEAR_INVALID_ERRORS,
        base.VERIFY_BUFFER_STORES,
        base.LOADER_EMITTER,
        base.LOADER_WORKSPACE_BASE,
        base.LOADER_WORKSPACE_BYTES,
        base.POSTDIAG_PROGRESS_MARKERS,
        base.REQUIRE_BANNER_TX_EMPTY,
        base.REQUIRE_FINAL_TX_EMPTY,
        base.DIRECT_LOADER_HANDOFF,
    )
    try:
        base.ROM_VERSION = ROM_VERSION
        base.IDENTITY = IDENTITY
        base.SOLICITED_INPUT = True
        base.FILTER_INVALID_SYMBOLS = True
        base.CLEAR_INVALID_ERRORS = True
        base.VERIFY_BUFFER_STORES = True
        base.LOADER_EMITTER = emit_loader_v5
        base.LOADER_WORKSPACE_BASE = 0xC000
        base.LOADER_WORKSPACE_BYTES = 0x1000
        base.POSTDIAG_PROGRESS_MARKERS = None
        base.REQUIRE_BANNER_TX_EMPTY = True
        base.REQUIRE_FINAL_TX_EMPTY = False
        base.DIRECT_LOADER_HANDOFF = True
        original, metadata = base.build()
    finally:
        (
            base.ROM_VERSION,
            base.IDENTITY,
            base.SOLICITED_INPUT,
            base.FILTER_INVALID_SYMBOLS,
            base.CLEAR_INVALID_ERRORS,
            base.VERIFY_BUFFER_STORES,
            base.LOADER_EMITTER,
            base.LOADER_WORKSPACE_BASE,
            base.LOADER_WORKSPACE_BYTES,
            base.POSTDIAG_PROGRESS_MARKERS,
            base.REQUIRE_BANNER_TX_EMPTY,
            base.REQUIRE_FINAL_TX_EMPTY,
            base.DIRECT_LOADER_HANDOFF,
        ) = saved

    if int(metadata["loader_extension_end"]) > 0x1000:
        raise ValueError("T32 loader crosses the 1000h execution boundary")
    if int(metadata["loader_entry"]) != LOADER_ENTRY:
        raise ValueError("T32 loader entry moved")

    image = bytearray(original)
    for address in TRAMPOLINES:
        program = trampoline(address)
        if image[address:address + len(program)] != b"\x76" * len(program):
            raise ValueError(f"T32 trampoline {address:04X}h overlaps non-fill bytes")
        image[address:address + len(program)] = program
    _refresh_protocol_checksum(image, metadata)
    metadata["waitclass_trampolines"] = dict(TRAMPOLINES)
    return bytes(image), metadata


def info_text(metadata: dict[str, object], digest: str) -> str:
    lines = [
        "T32HOST.BIN - JUKURAVI WAIT-CLASS MONITOR",
        "",
        f"ROM protocol version: {ROM_VERSION:02X}h",
        f"Self CRC16: {int(metadata['checksum']):04X}h",
        f"SHA256: {digest}",
        "",
        "Program at offset 0000h into an AT28C64B and verify it.",
        "T32 retains the proven T31 low-4K monitor and loader API v2.",
        "Normal execution remains below 1000h.",
        "",
        "Upper-ROM diagnostic entries (marker at 4100h, then JMP 0A0Ch):",
    ]
    lines.extend(
        f"  {address:04X}h  {description}" for address, description in TRAMPOLINES.items()
    )
    lines.extend(
        [
            "",
            "Run one entry at a time through a 3-byte RAM JMP trampoline, then",
            "reattach and read 4100h. Its byte must equal the entry high byte.",
            "A failed class will not return a READY banner or the right marker.",
            "Keep the existing 106Fh T31 result as the original CAS-gated evidence.",
            "",
        ]
    )
    return "\r\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    info = info_text(metadata, digest).encode("ascii")
    if args.check:
        expected = ((OUTPUT, image), (DOS_OUTPUT, image), (INFO_OUTPUT, info))
        for output, content in expected:
            if not output.exists() or output.read_bytes() != content:
                raise SystemExit(f"{output.name} is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        INFO_OUTPUT.write_bytes(info)
        action = "wrote"
    print(
        f"JUKURAVI-D0-WAITCLASS-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} loader_end={int(metadata['loader_extension_end']):04X} "
        f"trampolines={len(TRAMPOLINES)} self_crc16={int(metadata['checksum']):04X} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
