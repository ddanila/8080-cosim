#!/usr/bin/env python3
"""Build ekta4401: the EktaSoft #0037 remix (EKTA37-REMIX-PLAN.md).

Phase 1 content: a deterministic patch set over the pinned `roms/ekta37.bin`
producing `ekta4401.bin`:

1. banner identity line — same-length replacement, honest non-factory
   identity: `'EktaSoft&D.Sukharev '26#01` — serial 44 (one past the
   highest known factory serial #0043), build 01; not a factory number;
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
OUTPUT = HERE / "ekta4401.bin"

BANNER_OFFSET = 0x00DF
BANNER_OLD = b"'EktaSoft '88  Serial #0037"
BANNER_NEW = b"'EktaSoft&D.Sukharev '26#01"

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
    b"B basic  T boot(net)  J service\r\n"
    b"H this help\r\n"
    b"\x00"
)

# --- Phase 2: the Jukuravi loader as a monitor service -----------------------
#
# The T36 loader engine is stored verbatim (never relocated) and copied by `J`
# to the exact RAM addresses it was assembled for. In memory mode 1 the ROM is
# mapped only at D800h-FFFFh, so the low half is RAM: the engine can be copied
# there from ROM and executed unchanged, preserving every byte-level guarantee
# it carries. The engine initializes the 8251 and its 2400 baud D57 counter 0
# itself (T36 `0CE0h`), so `J` only has to hand it the machine.
#
# Segments are the transitive call-graph closure of the loader entry, the four
# public API vectors, the refresh primitive and the refresh command handler,
# plus the CRC table (computed access, outside the closure).
T36_SEGMENTS = (
    ("engine", 0x0A00, 0x0FFD),
    ("halt-helpers", 0x06E8, 0x0748),
    ("refresh+frames", 0x07A9, 0x0810),
    ("crc-table", 0x0900, 0x0A00),
    ("refresh-handler", 0x1070, 0x1113),
)
LOADER_ENTRY = 0x0A0C
DISK_REGION = (0x2325, 0x2A00)   # floppy subsystem, reclaimed for segments
MODE_PORT = 0x06                 # PPI0 port C, low two bits select memory mode
DISK_VECTORS = (0x3F50, 0x3F53, 0x3F56, 0x3F59)
NO_DISK_TEXT = b"\r\nNO DISK - NET ONLY\r\n\x00"


def t36_image() -> bytes:
    """The exact committed T36 diagnostic ROM (source of the loader bytes)."""
    firmware = ROOT / "spinoffs" / "jukuravi" / "firmware"
    sys.path.insert(0, str(firmware))
    import build_d0_row_refresh as t36  # noqa: PLC0415

    image, metadata = t36.build()
    if metadata["checksum"] != 0xC617 or len(image) != 8192:
        raise SystemExit("T36 build identity differs")
    return image


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
    # The table gains two entries (H, J); size it upfront so the H handler
    # that follows it is not overwritten when J is filled in later.
    stock_entries = bytes(table)
    table_length = len(stock_entries) + 3 + 3 + 1
    handler_runtime = NEW_TABLE_RUNTIME + table_length
    table = bytearray(stock_entries)
    table += bytes((ord("H"), handler_runtime & 0xFF, handler_runtime >> 8))
    table += bytes((ord("J"), 0, 0))          # J target patched in below
    table += b"\x00"
    if len(table) != table_length:
        raise SystemExit("dispatch table length drifted")

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

    # 3b. Phase 2: strip the floppy subsystem, store the loader segments in the
    # reclaimed space, and add the J service command.
    t36 = t36_image()
    disk_start, disk_end = DISK_REGION
    image[disk_start:disk_end] = b"\xFF" * (disk_end - disk_start)

    placements = []           # (name, rom_offset, runtime_source, dst, length)
    cursor = disk_start
    for name, lo, hi in T36_SEGMENTS:
        length = hi - lo
        if cursor + length > disk_end:      # spill into the tail of the gap
            break
        image[cursor : cursor + length] = t36[lo:hi]
        placements.append((name, cursor, cursor + 0xC000, lo, length))
        cursor += length
    spill = cursor
    cursor = end                            # after the H blob in the F900 gap
    for name, lo, hi in T36_SEGMENTS[len(placements):]:
        length = hi - lo
        image[cursor : cursor + length] = t36[lo:hi]
        placements.append((name, cursor, cursor + 0xC000, lo, length))
        cursor += length

    # J handler: DI, force memory mode 1 (ROM at D800h+, low half RAM),
    # copy each segment to its native address, then enter the loader.
    j_runtime = cursor + 0xC000
    code = bytearray((0xF3,))                                  # DI
    code += bytes((0xDB, MODE_PORT, 0xE6, 0xFC, 0xF6, 0x01,
                   0xD3, MODE_PORT))                           # IN/ANI/ORI/OUT
    copy_runtime = j_runtime + 1 + 8 + 12 * len(placements) + 3
    for _, _, source_runtime, dst, length in placements:
        code += bytes((0x21, source_runtime & 0xFF, source_runtime >> 8))
        code += bytes((0x11, dst & 0xFF, dst >> 8))
        code += bytes((0x01, length & 0xFF, length >> 8))
        code += bytes((0xCD, copy_runtime & 0xFF, copy_runtime >> 8))
    code += bytes((0xC3, LOADER_ENTRY & 0xFF, LOADER_ENTRY >> 8))
    copier = bytes((0x7E, 0x12, 0x23, 0x13, 0x0B, 0x78, 0xB1,
                    0xC2, copy_runtime & 0xFF, copy_runtime >> 8, 0xC9))
    if j_runtime + len(code) != copy_runtime:
        raise SystemExit("J handler layout drifted from its computed copier address")
    blob2 = bytes(code) + copier
    image[cursor : cursor + len(blob2)] = blob2
    cursor += len(blob2)

    # "no disk" stub for the reclaimed floppy vectors
    stub_runtime = cursor + 0xC000
    text_runtime = stub_runtime + 7
    stub = bytes((0x01, text_runtime & 0xFF, text_runtime >> 8,
                  0xCD, PRINT_STRING & 0xFF, PRINT_STRING >> 8, 0xC9)) + NO_DISK_TEXT
    image[cursor : cursor + len(stub)] = stub
    cursor += len(stub)
    if cursor > FREE_GAP_END:
        raise SystemExit("Phase 2 payload overflows the free gap")
    for vector in DISK_VECTORS:
        image[vector] = 0xC3
        image[vector + 1] = stub_runtime & 0xFF
        image[vector + 2] = stub_runtime >> 8

    # patch J's target into its reserved table slot
    j_slot = NEW_TABLE_OFFSET + len(stock_entries) + 3
    if image[j_slot] != ord("J"):
        raise SystemExit("J table slot is not where it was reserved")
    image[j_slot + 1] = j_runtime & 0xFF
    image[j_slot + 2] = j_runtime >> 8

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
        "loader_segments": [
            {"name": n, "rom": f"0x{o:04X}", "runtime_source": f"0x{s:04X}",
             "dst": f"0x{d:04X}", "bytes": ln}
            for n, o, s, d, ln in placements
        ],
        "j_runtime": f"0x{j_runtime:04X}",
        "no_disk_stub_runtime": f"0x{stub_runtime:04X}",
        "free_gap_used_to": f"0x{cursor:04X}",
        "banner": BANNER_NEW.decode(),
        "commands": "".join(letters) + "HJ",
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
            print("EKTA4401: committed image differs from rebuild", file=sys.stderr)
            return 1
        print(f"EKTA4401-CHECK: PASS {metadata['image_sha256']}")
        return 0
    OUTPUT.write_bytes(image)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
