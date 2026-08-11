#!/usr/bin/env python3
"""Build ekta4401: the EktaSoft #0037 remix (EKTA37-REMIX-PLAN.md).

Phase 1 content: a deterministic patch set over the pinned `roms/ekta37.bin`
producing `ekta4401.bin`:

1. banner identity line — same-length replacement, honest non-factory
   identity: `'EktaSoft&D.Sukharev '26#01` — serial 44 (one past the
   highest known factory serial #0043), build 01; not a factory number;
2. the monitor command dispatch table relocated from ROM `1977h` (runtime
   `D977h`) into the free gap at ROM `3900h` (runtime `F900h`, mode-1
   mapped), extended with the new `H`, `J`, and `V` commands;
3. the `H` handler and its help text after the table (prints the command
   list via the ROM's own `DA6Bh` NUL/'$'-terminated string printer), plus
   the `V` write-only framebuffer diamond-tunnel easter egg;
4. all eight ROM self-test chunk checksums regenerated.

The Phase-2 block below additionally replaces the floppy subsystem with the
verbatim T36 loader segments and guarded stubs. `--check` verifies the combined
image and both 8 KiB socket-programming halves rebuild identically.
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
D15_OUTPUT = HERE / "ekta4401-d15.bin"
D16_OUTPUT = HERE / "ekta4401-d16.bin"

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
    b"B basic  T boot(net)  J service  V ?\r\n"
    b"H this help\r\n"
    b"\x00"
)

# --- Phase 2: the Jukuravi loader as a monitor service -----------------------
#
# The T36 loader engine is stored verbatim (never relocated) and copied by `J`
# to the exact RAM addresses it was assembled for. In memory mode 1 the ROM is
# mapped only at D800h-FFFFh, so the low half is RAM: the engine can be copied
# there from ROM and executed unchanged, preserving every byte-level guarantee
# it carries. Before entering it, `J` calls the engine's own restore routine to
# deterministically initialize the 8251 and its 2400-baud D57 counter 0.
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
LOADER_RESTORE_SERIAL = 0x0CE1
DISK_REGION = (0x2325, 0x2A00)   # floppy subsystem, reclaimed for segments
MODE_PORT = 0x06                 # PPI0 port C, low two bits select memory mode
DISK_VECTORS = (0x3F50, 0x3F53, 0x3F56, 0x3F59)
NO_DISK_TEXT = b"\r\nNO DISK - NET ONLY\r\n\x00"

FRAMEBUFFER_BASE = 0xD800
FRAMEBUFFER_BYTES = 40 * 241
DEMO_FRAMES = 12
LOGO_ROW = 112
LOGO_COLUMN = 15
LOGO_TEXT = "JUKU 2026"
DEMO_RAM_RUNTIME = 0x1200

# Seven useful scanlines plus one blank line, transposed below into the
# framebuffer's row-major byte order. Each character is one 8-pixel byte, so
# the logo costs only 72 bytes and the animation never needs a framebuffer
# read (which would see mapped ROM in memory mode 1).
LOGO_GLYPHS = {
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    "0": (0x3C, 0x42, 0x46, 0x4A, 0x52, 0x62, 0x3C, 0x00),
    "2": (0x3C, 0x42, 0x02, 0x0C, 0x30, 0x40, 0x7E, 0x00),
    "6": (0x1C, 0x20, 0x40, 0x7C, 0x42, 0x42, 0x3C, 0x00),
    "J": (0x1E, 0x04, 0x04, 0x04, 0x44, 0x44, 0x38, 0x00),
    "K": (0x42, 0x44, 0x48, 0x70, 0x48, 0x44, 0x42, 0x00),
    "U": (0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00),
}


def logo_bytes() -> bytes:
    """Return the `JUKU 2026` mark in framebuffer row-major order."""
    return bytes(LOGO_GLYPHS[letter][row] for row in range(8) for letter in LOGO_TEXT)


def visual_demo(runtime: int) -> tuple[bytes, dict[str, int]]:
    """Build the fixed-duration, write-only `V` framebuffer effect.

    A high-ROM handler cannot write the underlying framebuffer directly. The
    small entry copies the body to otherwise hidden low RAM, then the body
    disables interrupts, selects all-RAM mode 3, paints, restores mode 1 and
    returns to the ROM monitor.
    """
    code = bytearray()

    def word(value: int) -> bytes:
        return bytes((value & 0xFF, value >> 8))

    body = bytearray()
    labels: dict[str, int] = {}
    fixups: list[tuple[int, str]] = []

    def mark(name: str) -> None:
        labels[name] = DEMO_RAM_RUNTIME + len(body)

    def absolute(opcode: int, label: str) -> None:
        body.extend((opcode, 0x00, 0x00))
        fixups.append((len(body) - 2, label))

    body += bytes((0xF3,))                              # DI
    body += bytes((0xDB, MODE_PORT, 0xE6, 0xFC, 0xF6, 0x03,
                   0xD3, MODE_PORT))                   # memory mode 3 (all RAM)
    body += bytes((0xAF,))                              # XRA A
    absolute(0x32, "phase")                           # STA phase
    body += bytes((0x3E, DEMO_FRAMES))                 # MVI A,n
    absolute(0x32, "frames")                          # STA frames

    # A coordinate-based, moving diamond tunnel. The old address hash made a
    # superficially varied byte stream, but its 256-byte period appeared as a
    # screen full of repeated glyphs. Here X is an explicitly symmetric
    # 40-column distance table and Y is abs(row-120)/8, giving approximately
    # square 8x8 cells. Bit 1 of X+Y+phase forms concentric moving rings.
    mark("frame")
    body += bytes((0x21,)) + word(FRAMEBUFFER_BASE)    # LXI H,D800
    body += bytes((0x3E, 241))                         # MVI A,241 rows
    absolute(0x32, "rows")                            # STA rows
    mark("row")
    absolute(0x3A, "rows")                            # LDA rows
    body += bytes((0xD6, 121))                         # SUI 121: signed Y
    absolute(0xF2, "positive_y")                      # JP positive_y
    body += bytes((0x2F, 0x3C))                        # CMA / INR A: abs(Y)
    mark("positive_y")
    body += bytes((0x0F, 0x0F, 0x0F, 0xE6, 0x1F,     # RRC*3 / ANI 1F
                   0x47))                              # MOV B,A: |Y|/8
    absolute(0x3A, "phase")                           # LDA phase
    body += bytes((0x80, 0x47))                        # ADD B / MOV B,A
    absolute(0x11, "x_distance")                      # LXI D,x_distance
    body += bytes((0x0E, 40))                          # MVI C,40 columns
    mark("column")
    body += bytes((
        0x1A,             # LDAX D: symmetric X distance
        0x80,             # ADD B: X + scaled Y + phase
        0xE6, 0x02,       # ANI 02: alternating tunnel bands
        0xFE, 0x01,       # CPI 01
        0x9F,             # SBB A: 00 -> FF, 02 -> 00
        0x77,             # MOV M,A
        0x23,             # INX H
        0x13,             # INX D
        0x0D,             # DCR C
    ))
    absolute(0xC2, "column")                          # JNZ column
    absolute(0x3A, "rows")                            # LDA rows
    body += bytes((0x3D,))                             # DCR A
    absolute(0x32, "rows")                            # STA rows
    absolute(0xC2, "row")                             # JNZ row
    absolute(0xCD, "logo")                            # CALL logo
    absolute(0x3A, "phase")                           # LDA phase
    body += bytes((0x3C,))                             # INR A
    absolute(0x32, "phase")                           # STA phase
    absolute(0x3A, "frames")                          # LDA frames
    body += bytes((0x3D,))                             # DCR A
    absolute(0x32, "frames")                          # STA frames
    absolute(0xC2, "frame")                           # JNZ frame

    # Clear the effect before returning to the normal monitor prompt.
    body += bytes((0x21,)) + word(FRAMEBUFFER_BASE)
    body += bytes((0x01,)) + word(FRAMEBUFFER_BYTES)
    clear = DEMO_RAM_RUNTIME + len(body)
    body += bytes((0x36, 0x00, 0x23, 0x0B, 0x78, 0xB1,
                   0xC2, clear & 0xFF, clear >> 8))
    body += bytes((0xDB, MODE_PORT, 0xE6, 0xFC, 0xF6, 0x01,
                   0xD3, MODE_PORT, 0xFB, 0xC9))       # mode 1 / EI / RET

    mark("logo")
    plaque_target = FRAMEBUFFER_BASE + (LOGO_ROW - 1) * 40 + LOGO_COLUMN - 1
    logo_target = FRAMEBUFFER_BASE + LOGO_ROW * 40 + LOGO_COLUMN
    body += bytes((
        0x21, plaque_target & 0xFF, plaque_target >> 8, # LXI H,plaque
        0x06, 0x0A,                                    # MVI B,10 rows
    ))
    mark("plaque_row")
    body += bytes((0x0E, len(LOGO_TEXT) + 2, 0xAF))    # MVI C,11 / XRA A
    mark("plaque_column")
    body += bytes((0x77, 0x23, 0x0D))                  # MOV M,A/INX H/DCR C
    absolute(0xC2, "plaque_column")                   # JNZ plaque_column
    body += bytes((0x0E, 40 - len(LOGO_TEXT) - 2))     # MVI C,row stride
    mark("plaque_skip")
    body += bytes((0x23, 0x0D))                        # INX H/DCR C
    absolute(0xC2, "plaque_skip")                     # JNZ plaque_skip
    body += bytes((0x05,))                             # DCR B
    absolute(0xC2, "plaque_row")                      # JNZ plaque_row
    body += bytes((
        0x21, logo_target & 0xFF, logo_target >> 8, # LXI H,target
    ))
    absolute(0x11, "logo_data")                       # LXI D,data
    body += bytes((0x06, 0x08, 0x0E, len(LOGO_TEXT))) # rows / columns
    mark("logo_column")
    body += bytes((0x1A, 0x77, 0x13, 0x23, 0x0D))     # copy one logo byte
    absolute(0xC2, "logo_column")                     # JNZ logo_column
    body += bytes((0x0E, 40 - len(LOGO_TEXT)))         # MVI C,row stride
    mark("logo_skip")
    body += bytes((0x23, 0x0D))                        # INX H/DCR C
    absolute(0xC2, "logo_skip")                       # JNZ logo_skip
    body += bytes((0x05,))                             # DCR B
    absolute(0xC2, "logo_row")                        # JNZ logo_row
    body += bytes((0xC9,))                             # RET

    # The logo-row entry is the MVI C immediately before the column loop.
    labels["logo_row"] = labels["logo_column"] - 2
    mark("x_distance")
    body += bytes(range(19, -1, -1)) + bytes(range(20))
    mark("logo_data")
    data = logo_bytes()
    body += data
    mark("phase")
    body += b"\x00"
    mark("frames")
    body += b"\x00"
    mark("rows")
    body += b"\x00"

    for offset, label in fixups:
        if label not in labels:
            raise SystemExit(f"V demo label is undefined: {label}")
        body[offset : offset + 2] = word(labels[label])

    # Copy the complete body+logo from mapped ROM to its linked low-RAM home.
    entry_bytes = 22
    body_source = runtime + entry_bytes
    code += bytes((0x21,)) + word(body_source)          # LXI H,source
    code += bytes((0x11,)) + word(DEMO_RAM_RUNTIME)    # LXI D,destination
    code += bytes((0x01,)) + word(len(body))           # LXI B,length
    copy = runtime + len(code)
    code += bytes((0x7E, 0x12, 0x23, 0x13, 0x0B, 0x78, 0xB1,
                   0xC2, copy & 0xFF, copy >> 8))
    code += bytes((0xC3,)) + word(DEMO_RAM_RUNTIME)    # JMP copied body
    if len(code) != entry_bytes:
        raise SystemExit("V entry layout drifted")
    code += body
    return bytes(code), {
        "runtime": runtime,
        "bytes": len(code),
        "body_source_runtime": body_source,
        "ram_runtime": DEMO_RAM_RUNTIME,
        "body_bytes": len(body),
        "frames": DEMO_FRAMES,
        "framebuffer_bytes_per_frame": FRAMEBUFFER_BYTES,
        "pattern": "symmetric-diamond-tunnel",
        "logo_runtime": labels["logo"],
        "logo_data_runtime": labels["logo_data"],
        "logo_bytes": len(data),
    }


def t36_image() -> bytes:
    """The exact committed T36 diagnostic ROM (source of the loader bytes)."""
    firmware = ROOT / "spinoffs" / "jukuravi" / "firmware"
    sys.path.insert(0, str(firmware))
    import build_d0_row_refresh as t36  # noqa: PLC0415

    image, metadata = t36.build()
    if (
        metadata["checksum"] != 0xC617
        or metadata["loader_restore_serial"] != LOADER_RESTORE_SERIAL
        or len(image) != 8192
    ):
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

    # 2. relocated dispatch table + H/J/V entries
    table = bytearray()
    i = TABLE_OFFSET
    letters = []
    while image[i] != 0x00:
        letters.append(chr(image[i]))
        table += image[i : i + 3]
        i += 3
    if "".join(letters) != "FDSXGMCEKTBRWPA":
        raise SystemExit(f"stock command set differs: {''.join(letters)}")
    # Size the complete table upfront so none of the handlers which follow it
    # move when the J and V targets are filled in later.
    stock_entries = bytes(table)
    table_length = len(stock_entries) + 3 + 3 + 3 + 1
    handler_runtime = NEW_TABLE_RUNTIME + table_length
    table = bytearray(stock_entries)
    table += bytes((ord("H"), handler_runtime & 0xFF, handler_runtime >> 8))
    table += bytes((ord("J"), 0, 0))          # J target patched in below
    table += bytes((ord("V"), 0, 0))          # V target patched in below
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
    demo_runtime = handler_runtime + len(handler) + len(HELP_TEXT)
    demo, demo_metadata = visual_demo(demo_runtime)
    blob = bytes(table) + handler + HELP_TEXT + demo
    end = NEW_TABLE_OFFSET + len(blob)
    if end > FREE_GAP_END:
        raise SystemExit("relocated table + H overflow the free gap")
    if any(b != 0xFF for b in image[NEW_TABLE_OFFSET:end]):
        raise SystemExit("free gap is not clean FFh fill")
    image[NEW_TABLE_OFFSET:end] = blob

    # Patch the easter-egg target after the complete blob has been laid out.
    v_slot = NEW_TABLE_OFFSET + len(stock_entries) + 6
    if image[v_slot] != ord("V"):
        raise SystemExit("V table slot is not where it was reserved")
    image[v_slot + 1] = demo_runtime & 0xFF
    image[v_slot + 2] = demo_runtime >> 8

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
    # copy each segment to its native address, restore the exact T36 serial/PIT
    # state, then enter the loader.
    j_runtime = cursor + 0xC000
    code = bytearray((0xF3,))                                  # DI
    code += bytes((0xDB, MODE_PORT, 0xE6, 0xFC, 0xF6, 0x01,
                   0xD3, MODE_PORT))                           # IN/ANI/ORI/OUT
    copy_runtime = j_runtime + 1 + 8 + 12 * len(placements) + 6
    for _, _, source_runtime, dst, length in placements:
        code += bytes((0x21, source_runtime & 0xFF, source_runtime >> 8))
        code += bytes((0x11, dst & 0xFF, dst >> 8))
        code += bytes((0x01, length & 0xFF, length >> 8))
        code += bytes((0xCD, copy_runtime & 0xFF, copy_runtime >> 8))
    code += bytes(
        (
            0xCD,
            LOADER_RESTORE_SERIAL & 0xFF,
            LOADER_RESTORE_SERIAL >> 8,
            0xC3,
            LOADER_ENTRY & 0xFF,
            LOADER_ENTRY >> 8,
        )
    )
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
        "commands": "".join(letters) + "HJV",
        "table_runtime": f"0x{NEW_TABLE_RUNTIME:04X}",
        "h_handler_runtime": f"0x{handler_runtime:04X}",
        "visual_demo": {
            **demo_metadata,
            "runtime": f"0x{demo_runtime:04X}",
            "logo_runtime": f"0x{int(demo_metadata['logo_runtime']):04X}",
            "logo_data_runtime": f"0x{int(demo_metadata['logo_data_runtime']):04X}",
            "logo": LOGO_TEXT,
        },
        "blob_rom_range": f"0x{NEW_TABLE_OFFSET:04X}..0x{end:04X}",
        "blob_bytes": len(blob),
        "checksum_000a": f"0x{image[0x000A]:02X}",
        "d15_sha256": hashlib.sha256(bytes(image[:0x2000])).hexdigest(),
        "d16_sha256": hashlib.sha256(bytes(image[0x2000:])).hexdigest(),
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
        expected_outputs = (
            (OUTPUT, image),
            (D15_OUTPUT, image[:0x2000]),
            (D16_OUTPUT, image[0x2000:]),
        )
        for path, expected in expected_outputs:
            if not path.exists() or path.read_bytes() != expected:
                print(f"EKTA4401: committed {path.name} differs from rebuild", file=sys.stderr)
                return 1
        print(f"EKTA4401-CHECK: PASS {metadata['image_sha256']}")
        return 0
    OUTPUT.write_bytes(image)
    D15_OUTPUT.write_bytes(image[:0x2000])
    D16_OUTPUT.write_bytes(image[0x2000:])
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
