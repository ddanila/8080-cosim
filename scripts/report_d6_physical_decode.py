#!/usr/bin/env python3
"""Decode and guard the preserved physical D6 `.038` RT4 table."""
from __future__ import annotations

import hashlib
import json
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

    board = json.loads((ROOT / "kicad/juku.board.json").read_text())
    joined_nodes = {tuple(node) for node in board["nets"]["D6_MEM_SELECT_N"]["nodes"]}
    required_join = {("D6", "11"), ("D6", "12"), ("D13", "12"), ("D8", "15")}
    hdl = (ROOT / "hdl/juku_top.v").read_text()
    devices = (ROOT / "hdl/devices.v").read_text()
    runtime_report = (ROOT / "docs/d6-runtime-path-diagnostic.md").read_text()
    model_checks = [
        ("Board source joins D6.11/D6.12 to D13.12 and D8.15", required_join <= joined_nodes),
        ("HDL drives both D6 outputs onto the joined conductor", ".rom_n(d6_mem_select_n), .ram_n(d6_mem_select_n)" in hdl),
        ("HDL uses physical D6 address order", ".a({ppi0_pc[4], ppi0_pc[3], ppi0_pc[2], BA[11], BA[12], BA[13], BA[14], BA[15]})" in hdl),
        ("Runnable compatibility decode is explicit and excluded from LVS",
         "module decode_prom_functional" in devices
         and "`ifndef YOSYS\n    decode_prom_functional U_D6_FUNCTIONAL" in hdl),
        ("Structural consumers retain the measured joined D6 conductor",
         "wire        rom_sel_n = d6_mem_select_n, ram_sel_n = d6_mem_select_n;" in hdl),
        ("All-mode B37A RAM-gate boundary has a reproducible diagnostic",
         "ALL PHYSICAL MODES EXHAUSTED AT THE RAM GATE BOUNDARY" in runtime_report
         and runtime_report.count("D6-RUNTIME-ALL-MODES ba=b37a") == 8),
        ("Mode-000 D6 indistinguishability and D8 pager distinction are reproduced",
         "D6-RUNTIME-QUALIFIER mode=000 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=8 ram_d8=ff" in runtime_report
         and "every D8 output currently has exactly one peer" in runtime_report),
    ]
    if not all(ok for _, ok in model_checks):
        raise SystemExit(f"D6 physical-model adoption changed: {model_checks}")

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
        "  contains word `8` at `0000-3FFF` and `C000-D7FF`, word `F` in the",
        "  middle, and word `1` at `D800-FFFF`; mode `010` extends word `8` through `D7FF`.",
        "  Firmware coverage is reported separately; do not equate these physical",
        "  mode numbers with the emulator's PC1/PC0 banking convention.",
        "- D3/pin9 is low only in word `1`; D2/pin10 is high in words `D/F`; the",
        "  joined D1/D0 conductor is high only in word `F`.", "- These are physical electrical facts, not yet a complete explanation of",
        "  the downstream D8/D13/D92 memory timing. That behavior must be derived",
        "  from the joined conductor and its consumers rather than resurrecting",
        "  separate RAM/ROM selects as physical claims.",
        "- Runnable simulation therefore uses a separately named, non-LVS",
        "  `decode_prom_functional` oracle for the established EKTA/EKDOS memory",
        "  map. The physical table and joined conductor remain instantiated and",
        "  guarded; the compatibility path must be retired when downstream timing",
        "  continuity is sufficient to execute directly from the physical topology.",
        "- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a",
        "  full boot. At `B37A`, all eight PC4..PC2 combinations emit word `8` or",
        "  `F`; D6.9 is therefore high in every physical row, and disabling the PROM",
        "  also leaves it high. Mode selection and V1/V2 cannot repair the currently",
        "  modeled D13/D37 chain's inactive D58 output. The isolated `.009` endpoint,",
        "  polarity/function, and D58-path checks named there must resolve the boundary.",
        "- At checkpoint mode `000`, D6 emits the same word `8` at PC `0484` and",
        "  RAM target `B37A`; no D6 output bit can distinguish those reads. D8's",
        "  pager output changes from `EF` (D15 selected) to `FF` (all sockets released),",
        "  but its modeled output nets only reach the eight socket CEs. An authentic",
        "  address-sensitive RAM qualifier remains missing rather than inferred.",
        "", "## Model adoption guards", "",
        "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in model_checks)
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Status: PHYSICAL TABLE CLASSIFIED AND GUARDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
