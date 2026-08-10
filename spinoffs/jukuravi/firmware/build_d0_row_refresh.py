#!/usr/bin/env python3
"""Build T36: T35 transport with physical MK4564 row-address refresh."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_refresh as t35
import protocol

OUTPUT = t35.base.HERE / "diag-d0-row-refresh.bin"
DOS_OUTPUT = t35.base.HERE / "dos" / "T36HOST.BIN"
README = t35.base.HERE / "README.md"
DOS_MANIFEST = t35.base.HERE / "dos" / "SHA256.TXT"
DOS_INFO = t35.base.HERE / "dos" / "T36INFO.TXT"
ROM_VERSION = 0x1E
IDENTITY = b"JUKURAVI-D0-PHYSICAL-REFRESH-1\0"

# D48/D49 place CPU A0..A7 on MA0..MA7 during the populated-bank RAS
# phase.  MK4564/2164 refresh consumes MA0..MA6 and ignores MA7, so one
# fixed high-byte RAM page with L=00h..7Fh visits every physical row.
REFRESH_ROWS = 128
REFRESH_ROW_START = 0x00
REFRESH_BASE_ADDRESS = 0x4000
REFRESH_INCREMENT_OPCODE = 0x2C  # INR L
REFRESH_ADDRESS_AXIS = "cpu-low-seven-bits"


def build():
    saved = (
        t35.ROM_VERSION,
        t35.IDENTITY,
        t35.REFRESH_ROWS,
        t35.REFRESH_GROUPS,
        t35.REFRESH_ROW_START,
        t35.REFRESH_BASE_ADDRESS,
        t35.REFRESH_INCREMENT_OPCODE,
        t35.REFRESH_ADDRESS_AXIS,
    )
    try:
        t35.ROM_VERSION = ROM_VERSION
        t35.IDENTITY = IDENTITY
        t35.REFRESH_ROWS = REFRESH_ROWS
        t35.REFRESH_GROUPS = REFRESH_ROWS // 4
        t35.REFRESH_ROW_START = REFRESH_ROW_START
        t35.REFRESH_BASE_ADDRESS = REFRESH_BASE_ADDRESS
        t35.REFRESH_INCREMENT_OPCODE = REFRESH_INCREMENT_OPCODE
        t35.REFRESH_ADDRESS_AXIS = REFRESH_ADDRESS_AXIS
        image, metadata = t35.build()
        metadata.update(
            {
                "refresh_physical_row_bits": "CPU A0..A6 -> MA0..MA6",
                "refresh_ma7_policy": "ignored by 128-cycle refresh",
                "supersedes_rom_version": t35.ROM_VERSION - 1,
            }
        )
        return image, metadata
    finally:
        (
            t35.ROM_VERSION,
            t35.IDENTITY,
            t35.REFRESH_ROWS,
            t35.REFRESH_GROUPS,
            t35.REFRESH_ROW_START,
            t35.REFRESH_BASE_ADDRESS,
            t35.REFRESH_INCREMENT_OPCODE,
            t35.REFRESH_ADDRESS_AXIS,
        ) = saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        for output in (OUTPUT, DOS_OUTPUT):
            if not output.exists() or output.read_bytes() != image:
                raise SystemExit(f"{output.name} is missing or stale")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the T36 image SHA256")
        manifest_line = f"{digest}  {DOS_OUTPUT.name}"
        if not DOS_MANIFEST.exists() or manifest_line not in DOS_MANIFEST.read_text():
            raise SystemExit("DOS SHA256 manifest does not pin T36HOST.BIN")
        info = "" if not DOS_INFO.exists() else DOS_INFO.read_text()
        for required in (
            f"ROM version: {ROM_VERSION:02X}h",
            f"Self CRC16: {int(metadata['checksum']):04X}h",
            f"SHA256: {digest}",
            f"CALL {protocol.LOADER_V2_REFRESH_API:04X}h",
            "CPU A0..A6",
        ):
            if required not in info:
                raise SystemExit(f"T36INFO.TXT is missing {required!r}")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-ROW-REFRESH-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} loader_end={int(metadata['loader_extension_end']):04X} "
        f"refresh_api={int(metadata['refresh_api']):04X} "
        f"refresh_ms={float(metadata['refresh_worst_ms_cs00024']):.3f} "
        f"self_crc16={int(metadata['checksum']):04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
