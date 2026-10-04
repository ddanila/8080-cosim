#!/usr/bin/env python3
"""Pin the byte lineage between the cartridge and onboard Monitor BASIC."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "cartridge-basic-firmware-lineage.md"
CART = ROOT / "roms" / "jbasic11.bin"
MONITORS = (
    ("Monitor 2.2", ROOT / "roms" / "jmon22.bin"),
    ("Monitor 3.3", ROOT / "roms" / "jmon33.bin"),
)

CART_BODY_START = 0x0100
CART_BODY_END = 0x1D38
MONITOR_BODY_START = 0x03C8
MONITOR_BODY_END = 0x2000
DELTA = MONITOR_BODY_START - CART_BODY_START
CARTRIDGE_LOAD_BASE = 0x0100
BOOTSTRAP_OFFSET = 0x1F00
BOOTSTRAP_ADDRESS = CARTRIDGE_LOAD_BASE + BOOTSTRAP_OFFSET
BOOTSTRAP_PREFIX = bytes.fromhex("21 00 02 11 00 01 01 00 20")
BOOTSTRAP_LOOP = bytes.fromhex("7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum_rows(data: bytes) -> list[tuple[int, int, int, int, bool]]:
    rows = []
    for block in range(8):
        start = 4 if block == 0 else block * 0x800
        end = (block + 1) * 0x800
        computed = sum(data[start:end]) & 0xFF
        stored = data[3 + block]
        rows.append((block, start, end - 1, stored, computed == stored))
    return rows


def main() -> int:
    cart = CART.read_bytes()
    if len(cart) != 0x2000:
        raise SystemExit(f"expected 8192-byte cartridge, got {len(cart)}")

    cart_body = cart[CART_BODY_START:CART_BODY_END]
    monitor_results = []
    for label, path in MONITORS:
        data = path.read_bytes()
        if len(data) != 0x4000:
            raise SystemExit(f"expected 16384-byte {path.name}, got {len(data)}")
        body = data[MONITOR_BODY_START:MONITOR_BODY_END]
        mismatches = [
            (offset, left, right)
            for offset, (left, right) in enumerate(zip(cart_body, body))
            if left != right
        ]
        monitor_results.append((label, path, data, body, mismatches, checksum_rows(data)))

    failed_blocks = [str(block) for block, _, _, _, passed in monitor_results[0][5] if not passed]
    failed_block_text = ", ".join(failed_blocks)
    if len(failed_blocks) > 1:
        failed_block_text = ", ".join(failed_blocks[:-1]) + ", and " + failed_blocks[-1]

    zero_gap = cart[CART_BODY_END:0x1F00]
    bootstrap = cart[BOOTSTRAP_OFFSET:0x2000]
    if bootstrap[:len(BOOTSTRAP_PREFIX)] != BOOTSTRAP_PREFIX:
        raise SystemExit("relocation bootstrap prefix changed")
    loop_offset = bootstrap.find(BOOTSTRAP_LOOP)
    if loop_offset != len(BOOTSTRAP_PREFIX):
        raise SystemExit(f"relocation loop moved to bootstrap offset 0x{loop_offset:02X}")

    source_start = int.from_bytes(bootstrap[1:3], "little")
    destination_start = int.from_bytes(bootstrap[4:6], "little")
    copy_length = int.from_bytes(bootstrap[7:9], "little")
    source_end = source_start + copy_length - 1
    destination_end = destination_start + copy_length - 1
    available_source_end = CARTRIDGE_LOAD_BASE + len(cart) - 1
    missing_source_start = available_source_end + 1
    missing_length = source_end - available_source_end
    if (
        BOOTSTRAP_ADDRESS != 0x2000
        or source_start != 0x0200
        or destination_start != 0x0100
        or copy_length != 0x2000
        or source_end != 0x21FF
        or destination_end != 0x20FF
        or available_source_end != 0x20FF
        or missing_source_start != 0x2100
        or missing_length != 0x0100
    ):
        raise SystemExit("relocation range contract changed")

    lines = [
        "# Cartridge BASIC firmware-lineage audit",
        "",
        "Status: **ONBOARD BASIC LINEAGE PINNED / MISSING PAGE NOT DERIVED**",
        "",
        "This generated audit tests whether the Monitor ROMs contain source evidence",
        "for the unresolved `jbasic11.bin` cartridge tail. It establishes a strong",
        "lineage match, but deliberately does not export a reconstructed cartridge:",
        "the exact match ends before the missing page.",
        "",
        "## Command",
        "",
        "Run from the repository root with Python 3 (standard library only).",
        "The writer reads `jbasic11.bin`, `jmon22.bin` and `jmon33.bin` from",
        "`roms/` and overwrites this report.",
        "",
        "```sh",
        "python3 scripts/report_cartridge_basic_firmware_lineage.py",
        "```",
        "",
        "It asserts image sizes, the relocation prefix/loop and the derived copy",
        "range. Full-image hashes, body mismatch counts and block checksums are",
        "reported, not compared with pinned expected identities or results. A",
        "successful run alone does not verify the ROM identities or byte lineage.",
        "",
        "## Exact body mapping",
        "",
        f"Cartridge offsets `0x{CART_BODY_START:04X}..0x{CART_BODY_END - 1:04X}` map to",
        f"Monitor-ROM offsets `0x{MONITOR_BODY_START:04X}..0x{MONITOR_BODY_END - 1:04X}`",
        f"with a constant source delta of `+0x{DELTA:03X}`. The compared span is",
        f"`{len(cart_body)}` bytes (`0x{len(cart_body):04X}`).",
        "",
        "| Firmware | SHA256 | Compared slice SHA256 | Mismatches | Disposition |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for label, path, data, body, mismatches, _ in monitor_results:
        disposition = "byte-exact" if not mismatches else "single-byte divergence"
        lines.append(
            f"| {label} (`{path.relative_to(ROOT)}`) | `{sha256(data)}` | "
            f"`{sha256(body)}` | `{len(mismatches)}` | {disposition} |"
        )

    lines.extend(["", "Mismatch detail:", ""])
    mismatch_lines = []
    for label, _, _, _, mismatches, _ in monitor_results:
        for offset, cart_byte, monitor_byte in mismatches:
            mismatch_lines.append(
                f"- {label}: cartridge `0x{CART_BODY_START + offset:04X}=0x{cart_byte:02X}`; "
                f"Monitor ROM `0x{MONITOR_BODY_START + offset:04X}=0x{monitor_byte:02X}`."
            )
    lines.extend(mismatch_lines or ["- none"])

    lines.extend(
        [
            "",
            "The Monitor 3.3 slice is byte-identical to the cartridge slice. Monitor",
            "2.2 differs at only one byte. The match establishes shared BASIC bytes",
            "over the compared span; it does not supply the absent source page.",
            "",
            "## Relocation range contract",
            "",
            "If the cartridge is mapped at `0x0100`, its 22-byte bootstrap at",
            "file offset `0x1F00` lies at",
            f"`0x{BOOTSTRAP_ADDRESS:04X}`. Its literal 8080 operands load",
            f"`HL=0x{source_start:04X}`, `DE=0x{destination_start:04X}`, and",
            f"`BC=0x{copy_length:04X}`; the guarded loop copies one byte, increments",
            "HL/DE, decrements BC, and repeats until BC is zero.",
            "",
            "| Quantity | Derived range/value |",
            "| --- | --- |",
            f"| Copy source | `0x{source_start:04X}..0x{source_end:04X}` |",
            f"| Copy destination | `0x{destination_start:04X}..0x{destination_end:04X}` |",
            f"| Public image mapped span | `0x{CARTRIDGE_LOAD_BASE:04X}..0x{available_source_end:04X}` (`{len(cart)}` bytes) |",
            f"| Missing source span | `0x{missing_source_start:04X}..0x{source_end:04X}` (`{missing_length}` bytes, exactly one page) |",
            f"| Missing page destination | `0x{available_source_end + 1 - source_start + destination_start:04X}..0x{destination_end:04X}` |",
            "",
            "The copy count is therefore direct firmware evidence for a 256-byte",
            "shortfall; it is not inferred from a failed runtime experiment.",
            "",
            "## Cartridge suffix",
            "",
            "| Span | Bytes | Non-zero bytes | SHA256 | Interpretation |",
            "| --- | ---: | ---: | --- | --- |",
            f"| `0x{CART_BODY_END:04X}..0x1EFF` | `{len(zero_gap)}` | "
            f"`{sum(byte != 0 for byte in zero_gap)}` | `{sha256(zero_gap)}` | zero padding |",
            f"| `0x1F00..0x1FFF` | `{len(bootstrap)}` | "
            f"`{sum(byte != 0 for byte in bootstrap)}` | `{sha256(bootstrap)}` | relocation bootstrap page |",
            "",
            "The required loop-survival sequence occurs at bootstrap offset",
            f"`0x{loop_offset:02X}`. Its presence identifies relocation code, not a",
            "validated donor for the absent source page.",
            "",
            "## Monitor 2.2 integrity",
            "",
            "The public Monitor 2.2 image has failing 2 KiB checksum blocks "
            + failed_block_text
            + ".",
            "The [Monitor 2.2 audit](jmon22-reconstruction.md#checksum-boundary)",
            "records the full checksum table and proves that the",
            "block-3 failure is the sole BASIC-body mismatch: replacing `0x9A` at",
            "`0x1EFC` with the `0xDA` found in both Monitor 3.3 and this cartridge",
            "exactly closes the stored checksum. It leaves the original dump unchanged",
            "because blocks 6 and 7 remain unresolved.",
            "",
            "This generator compares bytes and checksum constraints; it does not execute",
            "a cartridge or patched monitor. The current acceptance and recovery inputs",
            "are summarized in [the cartridge boundary](cartridge-basic-boundary.md).",
            "",
            "## Boundary",
            "",
            "- The exact shared span ends at cartridge offset `0x1D37`; extrapolating the",
            "  `+0x2C8` source delta into later monitor/bootstrap code is not a defensible",
            "  missing-page donor.",
            "- A working loading/decode contract remains unverified; byte lineage and",
            "  relocation operands alone do not establish BASIC startup.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
