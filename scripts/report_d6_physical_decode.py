#!/usr/bin/env python3
"""Decode and guard the preserved physical D6 `.038` RT4 table."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "ref/physical-proms/validated/d6_038.raw.bin"
REPORT = ROOT / "docs/d6-physical-decode.md"
EXPECTED_SHA256 = "05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39"


def row_index(high5: int, mode: int) -> int:
    """RT4 index: A0..A7 = BA15..BA11,PC2..PC4."""
    ba15 = (high5 >> 4) & 1
    ba14 = (high5 >> 3) & 1
    ba13 = (high5 >> 2) & 1
    ba12 = (high5 >> 1) & 1
    ba11 = high5 & 1
    pc2 = mode & 1
    pc3 = (mode >> 1) & 1
    pc4 = (mode >> 2) & 1
    return ba15 | ba14 << 1 | ba13 << 2 | ba12 << 3 | ba11 << 4 | pc2 << 5 | pc3 << 6 | pc4 << 7


def ranges(values: list[int]) -> list[tuple[int, int, int]]:
    result = []
    start = 0
    for pos in range(1, 33):
        if pos == 32 or values[pos] != values[start]:
            result.append((start * 0x800, pos * 0x800 - 1, values[start]))
            start = pos
    return result


def main() -> int:
    data = RAW.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != 256 or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected D6 physical image: bytes={len(data)} sha256={sha}")
    if any(value & 0xF0 for value in data):
        raise SystemExit("D6 image contains nonzero high-nibble data")
    words = sorted(set(data))
    if words != [0x1, 0x8, 0xD, 0xF]:
        raise SystemExit(f"unexpected D6 output vocabulary: {words}")

    mode_values = [[data[row_index(high5, mode)] for high5 in range(32)] for mode in range(8)]
    expected_runs = {
        0: [(0x0000, 0xFFFF, 0x8)],
        1: [(0x0000, 0x3FFF, 0x8), (0x4000, 0xBFFF, 0xF), (0xC000, 0xD7FF, 0x8), (0xD800, 0xFFFF, 0x1)],
        2: [(0x0000, 0xD7FF, 0x8), (0xD800, 0xFFFF, 0x1)],
        3: [(0x0000, 0x3FFF, 0x1), (0x4000, 0xFFFF, 0x8)],
        4: [(0x0000, 0x1FFF, 0xD), (0x2000, 0xFFFF, 0xF)],
        5: [(0x0000, 0x1FFF, 0xD), (0x2000, 0xFFFF, 0xF)],
        6: [(0x0000, 0x1FFF, 0xD), (0x2000, 0xFFFF, 0xF)],
        7: [(0x0000, 0x1FFF, 0xD), (0x2000, 0xFFFF, 0xF)],
    }
    actual_runs = {mode: ranges(values) for mode, values in enumerate(mode_values)}
    if actual_runs != expected_runs:
        raise SystemExit(f"D6 mode-map classification changed: {actual_runs}")

    counts = {word: data.count(word) for word in words}
    lines = [
        "# Physical D6 `.038` decode", "", "Status: **PHYSICAL TABLE CLASSIFIED AND GUARDED**", "",
        "This generated report translates the preserved КР556РТ4 D6 image into",
        "address ranges without assigning semantics that the `.009` continuity does",
        "not support. Run `python3 scripts/report_d6_physical_decode.py` to refresh it.", "",
        "## Guarded artifact", "", f"- Raw image: `ref/physical-proms/validated/d6_038.raw.bin` ({len(data)} bytes)",
        f"- SHA256: `{sha}`", "- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, PC2, PC3, PC4`",
        "- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9", "",
        "## Output words", "", "| Raw word | Rows | D3 D2 D1 D0 | Joined D1/D0 conductor |", "| ---: | ---: | --- | --- |",
    ]
    for word in words:
        joined = ((word >> 1) & 1) & (word & 1)
        lines.append(f"| `{word:X}` | {counts[word]} | `{word:04b}` | `{joined}` |")
    lines += [
        "", "D6 pins 11 and 12 are open-collector outputs joined by direct owner",
        "continuity on the `.009` board. Their electrical wired-low result is `0`",
        "for words `1`, `8`, and `D`, and `1` only for word `F`. Consequently the",
        "older-sheet names `RAM_N` and `ROM_N` must not be interpreted as independent",
        "`.009` nets even though they remain useful physical pin-role labels.", "",
        "## Mode maps", "", "Each address interval is inclusive. The 32-character signature is one raw",
        "nibble per 2 KiB block from `0000` through `F800`.", "",
        "| PC4 PC3 PC2 | 2 KiB signature | Inclusive address ranges |", "| --- | --- | --- |",
    ]
    for mode in range(8):
        signature = "".join(f"{value:X}" for value in mode_values[mode])
        rendered = "; ".join(f"`{start:04X}-{end:04X}` -> `{word:X}`" for start, end, word in actual_runs[mode])
        lines.append(f"| `{mode:03b}` | `{signature}` | {rendered} |")
    lines += [
        "", "## Direct observations", "", "- With `PC4=1`, PC2 and PC3 are don't-cares: `0000-1FFF` emits `D` and",
        "  `2000-FFFF` emits `F`.", "- With `PC4=0`, all four PC3/PC2 combinations are distinct. Mode `001`",
        "  contains the familiar reset window, an inactive middle window, and the",
        "  `D800-FFFF` high-memory window; mode `010` extends word `8` through `D7FF`.",
        "- D3/pin9 is low only in word `1`; D2/pin10 is high in words `D/F`; the",
        "  joined D1/D0 conductor is high only in word `F`.", "- These are physical electrical facts, not yet a complete explanation of",
        "  the downstream D8/D13/D92 memory timing. That behavior must be derived",
        "  from the joined conductor and its consumers rather than resurrecting",
        "  separate RAM/ROM selects.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Status: PHYSICAL TABLE CLASSIFIED AND GUARDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
