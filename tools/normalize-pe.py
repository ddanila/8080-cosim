#!/usr/bin/env python3
"""Remove linker and resource-compiler timestamps from a PE build."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct


def normalize_resources(
    data: bytearray, pe_offset: int, section_count: int, optional_size: int
) -> tuple[int, int]:
    """Zero timestamps in resource directories and VS_FIXEDFILEINFO records."""
    section_table = pe_offset + 24 + optional_size
    resource_raw = None
    resource_size = 0
    for index in range(section_count):
        section = section_table + index * 40
        name = bytes(data[section:section + 8]).rstrip(b"\0")
        if name == b".rsrc":
            resource_size = struct.unpack_from("<I", data, section + 16)[0]
            resource_raw = struct.unpack_from("<I", data, section + 20)[0]
            break
    if resource_raw is None:
        return 0, 0

    visited: set[int] = set()

    def visit(relative: int) -> None:
        if relative in visited or relative + 16 > resource_size:
            raise SystemExit("normalize-pe: invalid resource directory")
        visited.add(relative)
        directory = resource_raw + relative
        if directory + 16 > len(data):
            raise SystemExit("normalize-pe: truncated resource directory")
        struct.pack_into("<I", data, directory + 4, 0)
        named, identifiers = struct.unpack_from("<HH", data, directory + 12)
        count = named + identifiers
        if relative + 16 + count * 8 > resource_size:
            raise SystemExit("normalize-pe: invalid resource entries")
        for entry_index in range(count):
            entry = directory + 16 + entry_index * 8
            target = struct.unpack_from("<I", data, entry + 4)[0]
            if target & 0x80000000:
                visit(target & 0x7FFFFFFF)

    visit(0)

    fixed_signature = b"\xbd\x04\xef\xfe"
    fixed_count = 0
    cursor = resource_raw
    resource_end = min(resource_raw + resource_size, len(data))
    while True:
        cursor = data.find(fixed_signature, cursor, resource_end)
        if cursor < 0:
            break
        if cursor + 56 > resource_end:
            raise SystemExit("normalize-pe: truncated VS_FIXEDFILEINFO")
        # dwFileDateMS and dwFileDateLS are the final two DWORDs.
        struct.pack_into("<II", data, cursor + 48, 0, 0)
        fixed_count += 1
        cursor += len(fixed_signature)
    return len(visited), fixed_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    data = bytearray(args.executable.read_bytes())
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise SystemExit("normalize-pe: not an MZ executable")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise SystemExit("normalize-pe: PE signature missing")
    section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    struct.pack_into("<I", data, pe_offset + 8, 0)
    resource_count, version_count = normalize_resources(
        data, pe_offset, section_count, optional_size
    )
    args.executable.write_bytes(data)
    print(
        "JUKUWIN-PE-NORMALIZE: PASS "
        f"(COFF timestamp=0, resource directories={resource_count}, "
        f"versions={version_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
