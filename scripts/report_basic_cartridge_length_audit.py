#!/usr/bin/env python3
"""Audit the Monitor 3.3 cartridge BASIC payload length boundary."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "basic-cartridge-length-audit.md"
CART = ROOT / "roms" / "jbasic11.bin"
BAS_PARTS = [ROOT / "ref" / "firmware" / f"BAS{idx}.HEX" for idx in range(4)]
DISK_CANDIDATES = [
    ROOT / "ref" / "extracted-software" / "JUKPROG2_JBASIC.COM",
    ROOT / "ref" / "extracted-software" / "JUKPROG2_JBASIC_live_candidate.COM",
    ROOT / "ref" / "extracted-software" / "JUKU1_JBASIC_raw_candidate.COM",
]

LOAD_BASE = 0x0100
RELOC_SRC_START = 0x0200
RELOC_DST_START = 0x0100
RELOC_LEN = 0x2000
LOOP_TARGET = 0x2009
LOOP_RETURN = 0x2013


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_hex_bytes(path: Path) -> bytes:
    text = path.read_text(errors="replace")
    hex_digits = "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")
    return bytes.fromhex(hex_digits)


def string_offsets(data: bytes, needles: list[bytes]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for needle in needles:
        offsets: list[int] = []
        start = 0
        while True:
            pos = data.find(needle, start)
            if pos < 0:
                break
            offsets.append(pos)
            start = pos + 1
        result[needle.decode("ascii")] = offsets
    return result


def best_overlap(a: bytes, b: bytes, min_chunk: int = 64) -> tuple[int, int, int]:
    best = (0, 0, 0)
    for aoff in range(0, max(0, len(a) - min_chunk + 1), 16):
        pos = b.find(a[aoff : aoff + min_chunk])
        if pos < 0:
            continue
        count = 0
        while aoff + count < len(a) and pos + count < len(b) and a[aoff + count] == b[pos + count]:
            count += 1
        if count > best[0]:
            best = (count, aoff, pos)
    return best


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def hex_span(start: int, end: int) -> str:
    return f"`0x{start:04X}..0x{end:04X}`"


def fmt_offsets(offsets: list[int]) -> str:
    return ", ".join(f"`0x{offset:04X}`" for offset in offsets) if offsets else "-"


def candidate_rows(cart: bytes) -> list[str]:
    rows: list[str] = []
    needles = [b"BASIC", b"READY", b"ERROR"]
    for path in DISK_CANDIDATES:
        data = path.read_bytes()
        best_len, cart_off, candidate_off = best_overlap(cart, data)
        strings = string_offsets(data, needles)
        rows.append(
            table_row(
                [
                    f"`{path.relative_to(ROOT)}`",
                    len(data),
                    f"`{sha256(data)}`",
                    f"`{data[:8].hex(' ')}`",
                    f"`{best_len}` bytes at cart `0x{cart_off:04X}` / candidate `0x{candidate_off:04X}`",
                    f"BASIC {fmt_offsets(strings['BASIC'])}; READY {fmt_offsets(strings['READY'])}; ERROR {fmt_offsets(strings['ERROR'])}",
                ]
            )
        )
    return rows


def main() -> int:
    cart = CART.read_bytes()
    legacy = b"".join(decode_hex_bytes(path) for path in BAS_PARTS)
    load_end = LOAD_BASE + len(cart) - 1
    reloc_src_end = RELOC_SRC_START + RELOC_LEN - 1
    reloc_dst_end = RELOC_DST_START + RELOC_LEN - 1
    missing_start = max(load_end + 1, RELOC_SRC_START)
    missing_len = max(0, reloc_src_end - missing_start + 1)

    loop_target_src = RELOC_SRC_START + (LOOP_TARGET - RELOC_DST_START)
    loop_return_src = RELOC_SRC_START + (LOOP_RETURN - RELOC_DST_START)
    first_missing_write = RELOC_DST_START + max(0, missing_start - RELOC_SRC_START)

    status = "CARTRIDGE BASIC TAIL PAGE MISSING" if missing_len else "CARTRIDGE BASIC LENGTH COVERS RELOCATION"
    lines = [
        "# BASIC cartridge length audit",
        "",
        f"Status: **{status}**",
        "",
        "This generated report sharpens the Monitor 3.3 cartridge BASIC boundary",
        "from `docs/basic-low-stub-inspection.md`. The launch path itself is",
        "intentional; the remaining failure is that the public 8 KiB cartridge",
        "shape does not cover the runtime source range used by its own relocation",
        "bootstrap.",
        "",
        "## Inputs",
        "",
        "| Item | Value |",
        "| --- | --- |",
        table_row(["Cartridge", f"`{CART.relative_to(ROOT)}`"]),
        table_row(["Cartridge bytes", f"`{len(cart)}`"]),
        table_row(["Cartridge SHA256", f"`{sha256(cart)}`"]),
        table_row(["Legacy BAS0-3 bytes", f"`{len(legacy)}`"]),
        table_row(["Legacy BAS0-3 SHA256", f"`{sha256(legacy)}`"]),
        table_row(["First `0x0200` bytes identical", "`YES`" if cart[:0x0200] == legacy[:0x0200] else "`NO`"]),
        table_row(["Full images identical", "`YES`" if cart == legacy else "`NO`"]),
        "",
        "## Relocation Coverage",
        "",
        "| Field | Value |",
        "| --- | --- |",
        table_row(["Monitor-loaded runtime span", hex_span(LOAD_BASE, load_end)]),
        table_row(["Bootstrap source span", hex_span(RELOC_SRC_START, reloc_src_end)]),
        table_row(["Bootstrap destination span", hex_span(RELOC_DST_START, reloc_dst_end)]),
        table_row(["Missing source span", hex_span(missing_start, reloc_src_end) if missing_len else "-"]),
        table_row(["Missing source bytes", f"`{missing_len}`"]),
        table_row(["First destination byte sourced from missing span", f"`0x{first_missing_write:04X}`" if missing_len else "-"]),
        table_row(["Loop target overwrite source", f"`0x{loop_target_src:04X}` -> runtime `0x{LOOP_TARGET:04X}`"]),
        table_row(["Loop return overwrite source", f"`0x{loop_return_src:04X}` -> runtime `0x{LOOP_RETURN:04X}`"]),
        "",
        "The public payload loaded at `0x0100` ends at `0x20FF`, but the",
        "bootstrap copies `0x0200..0x21FF` down to `0x0100..0x20FF`. Therefore",
        "the last `0x100` source bytes are not supplied by the 8 KiB cartridge",
        "image. The first missing-source write lands at runtime `0x2000`; by",
        "the time execution reaches the loop tail, the live `MOV A,M` at",
        "`0x2009` and the nominal `JMP 0x0100` at `0x2013` are overwritten",
        "from zero-filled `0x2109` and `0x2113` respectively.",
        "",
        "## Disk BASIC Candidate Cross-check",
        "",
        "The disk-side `JBASIC.COM` candidates are useful for the proven EKDOS",
        "`READY` path, but none is a direct byte-for-byte tail donor for the",
        "Monitor 3.3 cartridge bootstrap.",
        "",
        "| Candidate | Bytes | SHA256 | First bytes | Best exact overlap with cartridge | Strings |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    lines.extend(candidate_rows(cart))
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The D8/D22 cartridge window and Monitor 3.3 copy path are already proven.",
            "- The public 8 KiB cartridge media shape is too short for the runtime",
            "  relocation loop it contains; the missing span is exactly one 256-byte",
            "  page, `0x2100..0x21FF` in runtime address space.",
            "- The extracted disk BASIC candidates are separate EKDOS payload shapes,",
            "  not an automatic replacement for the missing cartridge tail page.",
            "- The next automatic cartridge step would require another public artifact",
            "  or a derivable tail-page source. Otherwise this remains a media/monitor",
            "  compatibility boundary, while disk-side `JBASIC.COM` remains the guarded",
            "  functional BASIC path.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if missing_len == 0x100 else 1


if __name__ == "__main__":
    raise SystemExit(main())
