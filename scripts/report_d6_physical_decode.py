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
    """RT4 index: A0..A7 = BA15..BA11,A5..A7 raw pin levels."""
    ba15 = (high5 >> 4) & 1
    ba14 = (high5 >> 3) & 1
    ba13 = (high5 >> 2) & 1
    ba12 = (high5 >> 1) & 1
    ba11 = high5 & 1
    a5 = mode & 1
    a6 = (mode >> 1) & 1
    a7 = (mode >> 2) & 1
    return ba15 | ba14 << 1 | ba13 << 2 | ba12 << 3 | ba11 << 4 | a5 << 5 | a6 << 6 | a7 << 7


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
    rom_nodes = {tuple(node) for node in board["nets"]["ROM_SEL"]["nodes"]}
    enable_nodes = {tuple(node) for node in board["nets"]["D6_V_ENABLE"]["nodes"]}
    wreq_nodes = {tuple(node) for node in board["nets"]["WREQ_N"]["nodes"]}
    hdl = (ROOT / "hdl/juku_top.v").read_text()
    devices = (ROOT / "hdl/devices.v").read_text()
    runtime_report = (ROOT / "docs/d6-runtime-path-diagnostic.md").read_text()
    model_checks = [
        ("Chip-removed ROM select is D6.12 to D8.15", {("D6", "12"), ("D8", "15")} <= rom_nodes),
        ("D6.11 reaches D2.15/-WREQ and stays separate from ROM select", {("D6", "11"), ("D2", "15")} <= wreq_nodes and ("D6", "11") not in rom_nodes),
        ("D6.11 conductor also reaches D92.5/R12.2", {("D6", "11"), ("D2", "15"), ("D92", "5"), ("R12", "2")} <= wreq_nodes),
        ("D13.12 drives the D6 enable conductor, not either output", ("D13", "12") in enable_nodes and ("D13", "12") not in rom_nodes | wreq_nodes),
        ("HDL keeps the D6 outputs separate", ".rom_n(d6_rom_select_n), .ram_n(d6_ram_output_n)" in hdl),
        ("HDL uses measured physical D6 address order", ".a({d6_a7_d105_i1, d3_o4_d6_a6, d3_o6_d6_a5, BA[11], BA[12], BA[13], BA[14], BA[15]})" in hdl),
        ("Runnable compatibility decode is explicit and excluded from LVS",
         "module decode_prom_functional" in devices
         and "`ifndef YOSYS\n    decode_prom_functional U_D6_FUNCTIONAL" in hdl),
        ("Structural consumers retain separate ROM/RAM conductors",
         "wire        rom_sel_n = d6_rom_select_n, ram_sel_n = d6_ram_output_n;" in hdl),
        ("All-row B37A RAM-gate boundary has a reproducible diagnostic",
         "ALL RAW A7..A5 ROWS EXHAUSTED AT THE RAM GATE BOUNDARY" in runtime_report
         and runtime_report.count("D6-RUNTIME-ALL-MODES ba=b37a") == 8),
        ("Raw-row regression and corrected checkpoint suffix are documented",
         "D6-RUNTIME-QUALIFIER mode=000 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=8 ram_d8=ff" in runtime_report
         and "checkpoint on suffix `11`" in runtime_report),
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
        f"- SHA256: `{sha}`", "- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, ~PC0, ~PC1, D6.15/D105.1 boundary`",
        "- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9", "",
        "## Output words", "", "| Raw word | Rows | D3 D2 D1 D0 | RAM_N D1 | ROM_N D0 |", "| ---: | ---: | --- | ---: | ---: |",
    ]
    for word in words:
        lines.append(f"| `{word:X}` | {counts[word]} | `{word:04b}` | `{(word >> 1) & 1}` | `{word & 1}` |")
    lines += [
        "", "Chip-removed owner continuity proves D6 output pins 11 and 12 are",
        "separate. D6.12 reaches D8.15, while D6.11 reaches D2.15/-WREQ and",
        "does not reach D8.15; the earlier installed-PROM",
        "zero-ohm reading that joined D6.11/D6.12/D13.12 is explicitly invalidated.", "",
        "## Mode maps", "", "Each address interval is inclusive. The 32-character signature is one raw",
        "nibble per 2 KiB block from `0000` through `F800`.", "",
        "| D6 A7 A6 A5 | 2 KiB signature | Inclusive address ranges |", "| --- | --- | --- |",
    ]
    for mode in range(8):
        signature = "".join(f"{value:X}" for value in mode_values[mode])
        rendered = "; ".join(f"`{start:04X}-{end:04X}` -> `{word:X}`" for start, end, word in actual_runs[mode])
        lines.append(f"| `{mode:03b}` | `{signature}` | {rendered} |")
    lines += [
        "", "## Direct observations", "", "- With raw `A7=1`, A5 and A6 are don't-cares: `0000-1FFF` emits `D` and",
        "  `2000-FFFF` emits `F`.", "- With raw `A7=0`, all four A6/A5 combinations are distinct. Mode `001`",
        "  contains word `8` at `0000-3FFF` and `C000-D7FF`, word `F` in the",
        "  middle, and word `1` at `D800-FFFF`; mode `010` extends word `8` through `D7FF`.",
        "  Direct `.009` continuity now proves A6=`~PC1` and A5=`~PC0`; A7 joins",
        "  D105.1 but its driver or pull source is still unresolved. The raw mode",
        "  numbers remain useful table coordinates, not a claim about A7 semantics.",
        "- D3/pin9 is low only in word `1`; D2/pin10 is high in words `D/F`.", "- These are physical electrical facts, not yet a complete explanation of",
        "  the downstream D8/D13/D92 memory timing. That behavior must be derived",
        "  from the now-separate ROM/RAM conductors and their confirmed consumers.",
        "- Runnable simulation therefore uses a separately named, non-LVS",
        "  `decode_prom_functional` oracle for the established EKTA/EKDOS memory",
        "  map. The physical table and separate conductors remain instantiated and",
        "  guarded; the compatibility path must be retired when downstream timing",
        "  continuity is sufficient to execute directly from the physical topology.",
        "- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a",
        "  full boot. At `B37A`, all eight raw A7..A5 combinations emit word `8` or",
        "  `F`; D6.9 is therefore high in every physical row, and disabling the PROM",
        "  also leaves it high. Mode selection and V1/V2 cannot repair the currently",
        "  modeled D13/D37 chain's inactive D58 output. The isolated `.009` endpoint,",
        "  polarity/function, and D58-path checks named there must resolve the boundary.",
        "- Raw row `000` emits word `8` at both PC `0484` and RAM target `B37A`,",
        "  but measured firmware suffix `11` and unresolved A7 prevent identifying",
        "  that raw row as the checkpoint state.",
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
