#!/usr/bin/env python3
"""Generate the deterministic JUKUWIN icon and VERSIONINFO resource."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct


def make_icon() -> bytes:
    width = 32
    height = 32
    pixels = bytearray()
    # A block J in a deliberately simple 5x7 bitmap, scaled to 3x3 pixels.
    letter = (
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "10100",
        "01100",
    )
    for source_y in range(height - 1, -1, -1):
        for x in range(width):
            border = x in (1, 30) or source_y in (1, 30)
            letter_x = (x - 8) // 3
            letter_y = (source_y - 5) // 3
            on_letter = (
                8 <= x < 23 and 5 <= source_y < 26 and
                letter[letter_y][letter_x] == "1"
            )
            if on_letter:
                blue, green, red, alpha = 0xFF, 0xFF, 0xFF, 0xFF
            elif border:
                blue, green, red, alpha = 0x38, 0x28, 0x18, 0xFF
            else:
                blue, green, red, alpha = 0xB8, 0x68, 0x24, 0xFF
            pixels.extend((blue, green, red, alpha))
    mask = bytes(128)
    bitmap = struct.pack(
        "<IIIHHIIIIII", 40, width, height * 2, 1, 32, 0,
        len(pixels), 0, 0, 0, 0,
    ) + pixels + mask
    directory = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII", width, height, 0, 0, 1, 32, len(bitmap), 22
    )
    return directory + entry + bitmap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    (args.directory / "JUKUWIN.ICO").write_bytes(make_icon())
    resource = r'''#include <windows.h>

1 ICON "JUKUWIN.ICO"

1 VERSIONINFO
FILEVERSION 0,1,0,0
PRODUCTVERSION 0,1,0,0
FILEFLAGSMASK 0x3fL
FILEFLAGS 0x0L
FILEOS VOS__WINDOWS32
FILETYPE VFT_APP
FILESUBTYPE 0x0L
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904E4"
        BEGIN
            VALUE "CompanyName", "Juku project\0"
            VALUE "FileDescription", "Juku Host\0"
            VALUE "FileVersion", "0.1.0\0"
            VALUE "InternalName", "JUKUWIN\0"
            VALUE "OriginalFilename", "JUKUWIN.EXE\0"
            VALUE "ProductName", "Juku Host\0"
            VALUE "ProductVersion", "0.1.0\0"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0409, 1252
    END
END
'''
    (args.directory / "JUKUWIN.RC").write_text(
        resource, encoding="ascii", newline="\n"
    )
    print("JUKUWIN-RESOURCE-GENERATOR: PASS (32x32 icon + version 0.1.0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
