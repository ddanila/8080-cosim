#!/usr/bin/env python3
"""Build ektaravi: the EktaSoft #0037 remix (EKTA37-REMIX-PLAN.md).

Phase 1 content: a deterministic patch set over the pinned `roms/ekta37.bin`
producing `ektaravi.bin`:

1. banner identity line — same-length replacement, honest non-factory
   identity: `'EktaRavi '26  Danila #0001`;
2. the monitor command dispatch table relocated from ROM `1977h` (runtime
   `D977h`) into the free gap at ROM `3900h` (runtime `F900h`, mode-1
   mapped), extended with the new `H` command;
3. the `H` handler and its help text after the table (prints the command
   list via the ROM's own `DA6Bh` NUL/'$'-terminated string printer);
4. block-1 checksum at `000Ah` regenerated (sum of `000Bh..07FFh`).

Everything else is byte-identical to ekta37. `--check` verifies the
committed image rebuilds identically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
SOURCE = ROOT / "roms" / "ekta37.bin"
SOURCE_SHA256 = "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27"
OUTPUT = HERE / "ektaravi.bin"

BANNER_OFFSET = 0x00DF
BANNER_OLD = b"'EktaSoft '88  Serial #0037"
BANNER_NEW = b"'EktaRavi '26  Danila #0001"

TABLE_OFFSET = 0x1977            # stock dispatch table (runtime D977h)
TABLE_POINTER_OFFSET = 0x1924    # operand of the single LXI H,D977h at 1923h
NEW_TABLE_OFFSET = 0x3900        # free gap; runtime F900h via mode-1 mapping
NEW_TABLE_RUNTIME = 0xF900
FREE_GAP_END = 0x3EBA            # first non-FF byte after the gap
PRINT_STRING = 0xDA6B            # ROM print routine: BC -> NUL/'$'-terminated

HELP_TEXT = (
    b"\r\n"
    b"D dump  F fill  M move  C compare\r\n"
    b"S set  X regs  G go  K find  E echo\r\n"
    b"R read  W write  P printer  A app\r\n"
    b"B basic  T boot system  H this help\r\n"
    b"\x00"
)


def build() -> tuple[bytes, dict[str, object]]:
    rom = SOURCE.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"source roms/ekta37.bin differs: {digest}")
    image = bytearray(rom)

    # 1. banner identity line (same length, inside checksummed block 1)
    if image[BANNER_OFFSET : BANNER_OFFSET + len(BANNER_OLD)] != BANNER_OLD:
        raise SystemExit("banner line is not at the pinned offset")
    if len(BANNER_NEW) != len(BANNER_OLD):
        raise SystemExit("banner replacement must be the exact same length")
    image[BANNER_OFFSET : BANNER_OFFSET + len(BANNER_NEW)] = BANNER_NEW

    # 2. relocated dispatch table + H entry
    table = bytearray()
    i = TABLE_OFFSET
    letters = []
    while image[i] != 0x00:
        letters.append(chr(image[i]))
        table += image[i : i + 3]
        i += 3
    if "".join(letters) != "FDSXGMCEKTBRWPA":
        raise SystemExit(f"stock command set differs: {''.join(letters)}")
    handler_runtime = NEW_TABLE_RUNTIME + len(table) + 4  # after H entry + NUL
    table += bytes((ord("H"), handler_runtime & 0xFF, handler_runtime >> 8))
    table += b"\x00"

    # 3. H handler: LXI B,text / CALL print / RET
    text_runtime = handler_runtime + 7
    handler = bytes(
        (
            0x01, text_runtime & 0xFF, text_runtime >> 8,      # LXI B,text
            0xCD, PRINT_STRING & 0xFF, PRINT_STRING >> 8,      # CALL DA6Bh
            0xC9,                                              # RET
        )
    )
    blob = bytes(table) + handler + HELP_TEXT
    end = NEW_TABLE_OFFSET + len(blob)
    if end > FREE_GAP_END:
        raise SystemExit("relocated table + H overflow the free gap")
    if any(b != 0xFF for b in image[NEW_TABLE_OFFSET:end]):
        raise SystemExit("free gap is not clean FFh fill")
    image[NEW_TABLE_OFFSET:end] = blob

    # 4. repoint the parser's single table reference
    if image[TABLE_POINTER_OFFSET : TABLE_POINTER_OFFSET + 2] != bytes((0x77, 0xD9)):
        raise SystemExit("table pointer operand is not at the pinned offset")
    image[TABLE_POINTER_OFFSET] = NEW_TABLE_RUNTIME & 0xFF
    image[TABLE_POINTER_OFFSET + 1] = NEW_TABLE_RUNTIME >> 8

    # 5. checksums: the boot verifier walks two regions in 2 KiB chunks with
    # stored bytes DESCENDING from 000Ah (low, 3 chunks) and 180Ah (upper,
    # 5 chunks) -- verified against all eight stock sums.
    for n, (lo, hi) in enumerate(((0x000B, 0x0800), (0x0800, 0x1000),
                                  (0x1000, 0x1800))):
        image[0x000A - n] = sum(image[lo:hi]) & 0xFF
    for n, (lo, hi) in enumerate(((0x180B, 0x2000), (0x2000, 0x2800),
                                  (0x2800, 0x3000), (0x3000, 0x3800),
                                  (0x3800, 0x4000))):
        image[0x180A - n] = sum(image[lo:hi]) & 0xFF

    metadata = {
        "source_sha256": SOURCE_SHA256,
        "banner": BANNER_NEW.decode(),
        "commands": "".join(letters) + "H",
        "table_runtime": f"0x{NEW_TABLE_RUNTIME:04X}",
        "h_handler_runtime": f"0x{handler_runtime:04X}",
        "blob_rom_range": f"0x{NEW_TABLE_OFFSET:04X}..0x{end:04X}",
        "blob_bytes": len(blob),
        "checksum_000a": f"0x{image[0x000A]:02X}",
        "image_sha256": hashlib.sha256(bytes(image)).hexdigest(),
    }
    return bytes(image), metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the committed image rebuilds identically")
    args = parser.parse_args()
    image, metadata = build()
    if args.check:
        committed = OUTPUT.read_bytes()
        if committed != image:
            print("EKTARAVI: committed image differs from rebuild", file=sys.stderr)
            return 1
        print(f"EKTARAVI-CHECK: PASS {metadata['image_sha256']}")
        return 0
    OUTPUT.write_bytes(image)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
