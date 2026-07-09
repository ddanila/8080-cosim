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
VENDORED_DISK_GLOBS = ("*.CPM", "*.JUK")

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


def fmt_offsets(offsets: list[int], limit: int | None = None) -> str:
    if not offsets:
        return "-"
    visible = offsets if limit is None else offsets[:limit]
    text = ", ".join(f"`0x{offset:04X}`" for offset in visible)
    if limit is not None and len(offsets) > limit:
        text += f" (+{len(offsets) - limit})"
    return text


def vendored_disks() -> list[Path]:
    disks: list[Path] = []
    for pattern in VENDORED_DISK_GLOBS:
        disks.extend((ROOT / "media" / "disks").glob(pattern))
    return sorted(disks)


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return offsets
        offsets.append(pos)
        start = pos + 1


def fmt_disk_offsets(offsets: list[int]) -> str:
    if not offsets:
        return "`0`"
    sample = ", ".join(f"`0x{offset:05X}`" for offset in offsets[:3])
    if len(offsets) > 3:
        sample += f" (+{len(offsets) - 3})"
    return sample


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


def vendored_disk_rows(cart: bytes) -> tuple[list[str], list[str]]:
    rows: list[str] = []
    summary: list[str] = []
    needles = [b"BASIC", b"READY", b"ERROR"]
    final_page = cart[-0x100:]
    first_body_page = cart[0x0200:0x0300]
    full_tail_hits = 0
    final_page_hits = 0
    body_page_hits = 0

    for path in vendored_disks():
        data = path.read_bytes()
        best_len, cart_off, disk_off = best_overlap(cart, data, min_chunk=128)
        strings = string_offsets(data, needles)
        full_offsets = find_all(data, cart)
        full_tail_offsets = [
            offset for offset in full_offsets if offset + len(cart) + 0x100 <= len(data)
        ]
        final_offsets = find_all(data, final_page)
        final_tail_offsets = [
            offset for offset in final_offsets if offset + len(final_page) + 0x100 <= len(data)
        ]
        body_offsets = find_all(data, first_body_page)
        full_tail_hits += len(full_tail_offsets)
        final_page_hits += len(final_tail_offsets)
        body_page_hits += len(body_offsets)
        rows.append(
            table_row(
                [
                    f"`{path.relative_to(ROOT)}`",
                    len(data),
                    f"`{sha256(data)}`",
                    (
                        f"`{best_len}` bytes at cart `0x{cart_off:04X}` / "
                        f"disk `0x{disk_off:05X}`"
                    ),
                    fmt_disk_offsets(full_tail_offsets),
                    fmt_disk_offsets(final_tail_offsets),
                    fmt_disk_offsets(body_offsets),
                    (
                        f"BASIC {fmt_offsets(strings['BASIC'], limit=5)}; "
                        f"READY {fmt_offsets(strings['READY'], limit=5)}; "
                        f"ERROR {fmt_offsets(strings['ERROR'], limit=5)}"
                    ),
                ]
            )
        )

    summary.extend(
        [
            table_row(["Known 8 KiB cartridge image followed by an extra page", full_tail_hits]),
            table_row(["Known final cartridge page followed by an extra page", final_page_hits]),
            table_row(["First relocated body page occurrences", body_page_hits]),
        ]
    )
    return rows, summary


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
    raw_disk_rows, raw_disk_summary = vendored_disk_rows(cart)

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
            "## Vendored Raw Disk Sweep",
            "",
            "This bytewise sweep covers every vendored `*.CPM` and `*.JUK` image",
            "under `media/disks/`, including the public `J3KUTIL4.JUK` utility",
            "image. It looks for the known cartridge stream, the known final",
            "cartridge page, and the first relocated body page inside raw disk",
            "bytes. A hit in the first two categories with another `0x100` bytes",
            "available would be a concrete tail-page donor lead.",
            "",
            "| Probe | Hits |",
            "| --- | ---: |",
        ]
    )
    lines.extend(raw_disk_summary)
    lines.extend(
        [
            "",
            "| Disk | Bytes | SHA256 | Best exact overlap with cartridge | Full image + tail offsets | Final page + tail offsets | Body-page offsets | Strings |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(raw_disk_rows)
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
            "- The vendored raw disk sweep finds no known 8 KiB cartridge image, and",
            "  no known final cartridge page, followed by an extra `0x100` bytes.",
            "  That rules out a direct raw-disk tail donor among the current",
            "  vendored public media without claiming the unknown page contents.",
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
