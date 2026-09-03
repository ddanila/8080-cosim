#!/usr/bin/env python3
"""Audit the JUKUWIN PE target and its complete direct import set."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import subprocess


def fail(message: str) -> None:
    raise SystemExit(f"check-jukuwin-pe: {message}")


def resource_types(data: bytes, pe_offset: int) -> set[int]:
    """Return numeric root resource types and validate deterministic stamps."""
    section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    section_table = pe_offset + 24 + optional_size
    raw = None
    size = 0
    for index in range(section_count):
        section = section_table + index * 40
        if bytes(data[section:section + 8]).rstrip(b"\0") == b".rsrc":
            size = struct.unpack_from("<I", data, section + 16)[0]
            raw = struct.unpack_from("<I", data, section + 20)[0]
            break
    if raw is None or raw + 16 > len(data):
        fail("resource section missing or truncated")

    visited: set[int] = set()

    def visit(relative: int) -> None:
        if relative in visited or relative + 16 > size:
            fail("invalid resource directory")
        visited.add(relative)
        directory = raw + relative
        if directory + 16 > len(data):
            fail("truncated resource directory")
        timestamp = struct.unpack_from("<I", data, directory + 4)[0]
        if timestamp != 0:
            fail("non-deterministic resource timestamp")
        named, identifiers = struct.unpack_from("<HH", data, directory + 12)
        count = named + identifiers
        if relative + 16 + count * 8 > size:
            fail("resource entries exceed section")
        for entry_index in range(count):
            entry = directory + 16 + entry_index * 8
            target = struct.unpack_from("<I", data, entry + 4)[0]
            if target & 0x80000000:
                visit(target & 0x7FFFFFFF)

    visit(0)
    named, identifiers = struct.unpack_from("<HH", data, raw + 12)
    types = set()
    for entry_index in range(named, named + identifiers):
        entry = raw + 16 + entry_index * 8
        types.add(struct.unpack_from("<I", data, entry)[0] & 0xFFFF)
    return types


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--subsystem", choices=("console", "windows"),
                        required=True)
    args = parser.parse_args()

    data = args.executable.read_bytes()
    if data[:2] != b"MZ" or len(data) < 0x40:
        fail("not an MZ executable")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        fail("PE signature missing")
    machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
    optional = pe_offset + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    major_subsystem = struct.unpack_from("<H", data, optional + 48)[0]
    minor_subsystem = struct.unpack_from("<H", data, optional + 50)[0]
    subsystem = struct.unpack_from("<H", data, optional + 68)[0]
    expected_subsystem = 3 if args.subsystem == "console" else 2
    if machine != 0x014C or magic != 0x010B:
        fail(f"expected PE32/i386, got machine={machine:04x} magic={magic:04x}")
    if subsystem != expected_subsystem:
        fail(f"subsystem {subsystem} != {expected_subsystem}")
    if (major_subsystem, minor_subsystem) > (4, 0):
        fail(f"subsystem version {major_subsystem}.{minor_subsystem} exceeds 4.0")
    types = resource_types(data, pe_offset)
    missing_types = {3, 14, 16} - types
    if missing_types:
        fail("missing icon/version resource types: " +
             ", ".join(str(item) for item in sorted(missing_types)))
    signature = data.find(b"\xbd\x04\xef\xfe")
    if signature < 0 or signature + 56 > len(data):
        fail("VS_FIXEDFILEINFO missing")
    file_date = struct.unpack_from("<II", data, signature + 48)
    if file_date != (0, 0):
        fail("non-deterministic VERSIONINFO file date")

    result = subprocess.run(
        ["objdump", "-p", str(args.executable)], check=True,
        text=True, stdout=subprocess.PIPE,
    )
    dll = None
    imports = set()
    for line in result.stdout.splitlines():
        match = re.search(r"DLL Name:\s*(\S+)", line)
        if match:
            dll = match.group(1).upper()
            continue
        match = re.match(r"\s*[0-9a-fA-F]+\s+<none>\s+[0-9a-fA-F]+\s+(\S+)", line)
        if match and dll is not None:
            imports.add(f"{dll}!{match.group(1)}")
    allowed = {
        line.strip() for line in args.allowlist.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    unexpected = sorted(imports - allowed)
    missing = sorted(allowed - imports)
    if unexpected:
        fail("unexpected imports: " + ", ".join(unexpected))
    if missing:
        fail("allowlisted imports absent: " + ", ".join(missing))
    print(
        "JUKUWIN-PE-AUDIT: PASS "
        f"(PE32/i386, subsystem {major_subsystem}.{minor_subsystem} "
        f"{args.subsystem}, {len(imports)} reviewed imports, icon + version)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
