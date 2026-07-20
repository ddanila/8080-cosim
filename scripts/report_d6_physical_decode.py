#!/usr/bin/env python3
"""Decode and guard the preserved physical D6 `.038` RT4 table."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "ref/physical-proms/validated/d6_038.raw.bin"
REPORT = ROOT / "docs/d6-physical-decode.md"
EXPECTED_SHA256 = "c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489"
SHEET1_OVERVIEW = ROOT / "ref/photos/dgsh5-109-009-e3/PXL_20260718_101754468.jpg"
SHEET1_DETAIL = ROOT / "ref/photos/dgsh5-109-009-e3/PXL_20260718_101805510.jpg"
EXPECTED_SHEET1_OVERVIEW_SHA256 = "effc98746807ef28dab97051ceba293f4433c0f3b39b86cbb55ddcaad24aeca4"
EXPECTED_SHEET1_DETAIL_SHA256 = "40a524d663dc4685a7093782165264524cd70780fb41638a8d1c0cbca0b36216"


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
    if words != [0x1, 0x8, 0xB, 0xF]:
        raise SystemExit(f"unexpected D6 output vocabulary: {words}")

    drawing_hashes = {
        SHEET1_OVERVIEW: EXPECTED_SHEET1_OVERVIEW_SHA256,
        SHEET1_DETAIL: EXPECTED_SHEET1_DETAIL_SHA256,
    }
    for path, expected in drawing_hashes.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(
                f"unexpected recovered .009 sheet-1 photo: {path.relative_to(ROOT)} "
                f"sha256={actual}"
            )

    mode_values = [[data[row_index(high5, mode)] for high5 in range(32)] for mode in range(8)]
    expected_runs = {
        0: [(0x0000, 0xFFFF, 0x1)],
        1: [(0x0000, 0x3FFF, 0x1), (0x4000, 0xBFFF, 0xF), (0xC000, 0xD7FF, 0x1), (0xD800, 0xFFFF, 0x8)],
        2: [(0x0000, 0xD7FF, 0x1), (0xD800, 0xFFFF, 0x8)],
        3: [(0x0000, 0x3FFF, 0x8), (0x4000, 0xFFFF, 0x1)],
        4: [(0x0000, 0x1FFF, 0xB), (0x2000, 0xFFFF, 0xF)],
        5: [(0x0000, 0x1FFF, 0xB), (0x2000, 0xFFFF, 0xF)],
        6: [(0x0000, 0x1FFF, 0xB), (0x2000, 0xFFFF, 0xF)],
        7: [(0x0000, 0x1FFF, 0xB), (0x2000, 0xFFFF, 0xF)],
    }
    actual_runs = {mode: ranges(values) for mode, values in enumerate(mode_values)}
    if actual_runs != expected_runs:
        raise SystemExit(f"D6 mode-map classification changed: {actual_runs}")

    board = json.loads((ROOT / "kicad/juku.board.json").read_text())
    rom_nodes = {tuple(node) for node in board["nets"]["ROM_SEL"]["nodes"]}
    enable_nodes = {tuple(node) for node in board["nets"]["D6_V_ENABLE"]["nodes"]}
    wreq_nodes = {tuple(node) for node in board["nets"]["WREQ_N"]["nodes"]}
    io_cycle_nodes = {tuple(node) for node in board["nets"]["IO_CYCLE_H"]["nodes"]}
    hdl = (ROOT / "hdl/juku_top.v").read_text()
    devices = (ROOT / "hdl/devices.v").read_text()
    reader = (ROOT / "tools/re3_board_rt4_dumper/re3_board_rt4_dumper.ino").read_text()
    validator = (ROOT / "scripts/validate_rt4_dump.py").read_text()
    runtime_report = (ROOT / "docs/d6-runtime-path-diagnostic.md").read_text()
    model_checks = [
        ("Chip-removed ROM select is D6.12 to D8.15", {("D6", "12"), ("D8", "15")} <= rom_nodes),
        ("D6.11 reaches D2.15/-WREQ and stays separate from ROM select", {("D6", "11"), ("D2", "15")} <= wreq_nodes and ("D6", "11") not in rom_nodes),
        ("D6.11 conductor also reaches D92.5/R12.2", {("D6", "11"), ("D2", "15"), ("D92", "5"), ("R12", "2")} <= wreq_nodes),
        ("D13.12 drives the D6 enable conductor, not either output", ("D13", "12") in enable_nodes and ("D13", "12") not in rom_nodes | wreq_nodes),
        ("D7.8 drives D105.1 and D6 A7 as IO_CYCLE_H",
         {("D7", "8"), ("D105", "1"), ("D6", "15")} <= io_cycle_nodes),
        ("HDL keeps the D6 outputs separate", ".rom_n(d6_rom_select_n), .ram_n(d6_ram_output_n)" in hdl),
        ("HDL models D6 raw outputs as open collector with physical pull-up recovery",
         "К556РТ4 outputs are open collector" in devices
         and "assign d[bit_index] = (!v_en_n && !raw[bit_index]) ? 1'b0 : 1'bz;" in devices
         and "Physical R11..R14 recover the four open-collector D6 outputs high" in hdl),
        ("HDL uses measured physical D6 address order", ".a({io_cycle_h, d3_o4_d6_a6, d3_o6_d6_a5, BA[11], BA[12], BA[13], BA[14], BA[15]})" in hdl),
        ("RT4 reader packs D0/pin12 through D3/pin9 into raw bits 0 through 3",
         "RT4 D0..D3 (pins 12,11,10,9)" in reader
         and "value |= (1U << bit)" in reader),
        ("RT4 reader revision 3 has continuity-confirmed channel order and verifies both enables",
         "DATA_PINS[4] = {4, 3, 2, A1}" in reader
         and "ENABLE_13_PIN = 5" in reader
         and "ENABLE_14_PIN = 6" in reader
         and "disabled_raw=" in reader
         and "disabled_ce13_raw=" in reader
         and "disabled_ce14_raw=" in reader),
        ("RT4 host validation guards revision-3 metadata and the old bit reversal",
         "--compare-raw" in validator
         and "EXACT_MATCH" in validator
         and "EXACT_BIT_REVERSE" in validator
         and "OTHER_DIFFERENCE" in validator
         and "revision-3" in validator),
        ("Device commentary preserves measured mode pins and separate output conductors",
         "pin 2/A5 <- D3.6 <- /PC0" in devices
         and "pin 1/A6 <- D3.4 <- /PC1" in devices
         and "pins 11 and 12 are separate conductors" in devices
         and "pins 11/12 are joined" not in devices),
        ("Runnable twin executes corrected physical D6 outputs directly",
         "wire        rom_sel_n = d6_rom_select_n;" in hdl
         and "wire        roe_n     = d6_roe_physical;" in hdl
         and "~d6_rom_select_n" not in hdl
         and "~d6_roe_physical" not in hdl
         and "decode_prom_functional U_D6_FUNCTIONAL" not in hdl
         and "module decode_prom_functional" in devices),
        ("Structural consumers retain separate ROM/RAM conductors",
         "wire        rom_sel_n = d6_rom_select_n, ram_sel_n = d6_ram_output_n;" in hdl),
        ("Corrected mode path has a reproducible diagnostic",
         "CORRECTED TABLE MATCHES MEASURED MODE PATH" in runtime_report
         and runtime_report.count("D6-RUNTIME-ALL-MODES ba=b37a") == 8),
        ("Raw-row regression and corrected checkpoint suffix are documented",
         "D6-RUNTIME-QUALIFIER mode=011 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=1 ram_d8=ff" in runtime_report
         and "supply suffix `11`" in runtime_report),
        ("Recovered .009 sheet-1 D6 polarity evidence is checksum-guarded",
         all(path.exists() for path in drawing_hashes)),
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
        f"- SHA256: `{sha}`", "- Physical address order: `A0..A7 = BA15, BA14, BA13, BA12, BA11, ~PC0, ~PC1, D7.8 IO_CYCLE_H`",
        "- Raw output order: bit 0..3 = physical D0/pin12, D1/pin11, D2/pin10, D3/pin9", "",
        "The factory programming instruction in `ref/baltijets-tech-docs/007 ROM and ROM programming.pdf`",
        "page 16 identifies D6 `.038` as a КР556РТ4 and says its programming table",
        "was supplied on disk. The 2026-07-19 reader-3 control first reproduced D2",
        "byte-for-byte, then three D6 reads including a power cycle exposed the old",
        "capture as an exact nibble bit reversal. Direct continuity confirms reader-3",
        "D0/pin12 through D3/pin9 packing.", "",
        "## Output words", "", "| Raw word | Rows | D3 D2 D1 D0 | RAM_N D1 | ROM_N D0 |", "| ---: | ---: | --- | ---: | ---: |",
    ]
    for word in words:
        lines.append(f"| `{word:X}` | {counts[word]} | `{word:04b}` | `{(word >> 1) & 1}` | `{word & 1}` |")
    lines += [
        "", "Chip-removed owner continuity proves D6 output pins 11 and 12 are",
        "separate. D6.12 reaches D8.15, while D6.11 reaches D2.15/-WREQ and",
        "does not reach D8.15; the earlier installed-PROM",
        "zero-ohm reading that joined D6.11/D6.12/D13.12 is explicitly invalidated.", "",
        "## Recovered `.009` sheet-1 polarity read", "",
        "Two independent read passes over the native-color detail and an enhanced",
        "high-resolution crop, cross-checked against the sheet overview, close the",
        "critical schematic question. The guarded source frames are:", "",
        f"- `{SHEET1_OVERVIEW.relative_to(ROOT)}` (SHA256 `{EXPECTED_SHEET1_OVERVIEW_SHA256}`)",
        f"- `{SHEET1_DETAIL.relative_to(ROOT)}` (SHA256 `{EXPECTED_SHEET1_DETAIL_SHA256}`; upper-center D6/D8/D9 region)", "",
        "The drawing labels D6 D0/pin 12 `ROM` and carries that conductor",
        "uninterrupted through the R11 1 kOhm pull-up node to D8 `E`/pin 15. It",
        "labels D6 D3/pin 9 `ROE`; that conductor passes the R14 1 kOhm pull-up",
        "node and enters D13 pin 1 directly. D13 is the only inverter symbol on",
        "this path, and D13 pin 2 is the drawn `RAMOUTEN` output. No additional",
        "series inverter, off-sheet inversion, or alternate consumer is drawn on",
        "either D6 output path.", "",
        "This reviewed factory-drawing result agrees with the stronger chip-removed",
        "D6.12-to-D8.15 and D6.9-to-D13.1 continuity measurements and with the",
        "modeled D13 polarity. It therefore rules out an omitted *drawn* inverter",
        "as the cause of the former raw-table contradiction. The corrected reader",
        "instead proved that the original capture labels reversed all four channels.", "",
        "## Mode maps", "", "Each address interval is inclusive. The 32-character signature is one raw",
        "nibble per 2 KiB block from `0000` through `F800`.", "",
        "| D6 A7 A6 A5 | 2 KiB signature | Inclusive address ranges |", "| --- | --- | --- |",
    ]
    for mode in range(8):
        signature = "".join(f"{value:X}" for value in mode_values[mode])
        rendered = "; ".join(f"`{start:04X}-{end:04X}` -> `{word:X}`" for start, end, word in actual_runs[mode])
        lines.append(f"| `{mode:03b}` | `{signature}` | {rendered} |")
    lines += [
        "", "## Direct observations", "", "- With raw `A7=1`, A5 and A6 are don't-cares: `0000-1FFF` emits `B` and",
        "  `2000-FFFF` emits `F`.", "- With raw `A7=0`, all four A6/A5 combinations are distinct. Mode `001`",
        "  contains word `1` at `0000-3FFF` and `C000-D7FF`, word `F` in the",
        "  middle, and word `8` at `D800-FFFF`; mode `010` extends word `1` through `D7FF`.",
        "  Direct continuity proves A6=`~PC1`, A5=`~PC0`, and A7 is the",
        "  D7.8-to-D105.1 `IO_CYCLE_H` qualifier. The raw mode",
        "  numbers remain useful table coordinates, not a claim about A7 semantics.",
        "- D3/pin9 is low only in word `1`; D2/pin10 is high in words `B/F`.", "- These are physical electrical facts, not yet a complete explanation of",
        "  the downstream D8/D13/D92 memory timing. That behavior must be derived",
        "  from the now-separate ROM/RAM conductors and their confirmed consumers.",
        "- Runnable simulation now executes its memory map from THIS physical table",
        "  (the `decode_prom` instance), not the former `decode_prom_functional`",
        "  oracle, which is retired from the boot path. All four physical outputs",
        "  now execute directly with no per-output transform and pass the 6,000-write",
        "  byte-identical boot guard.",
        "- `docs/d6-runtime-path-diagnostic.md` now exhausts every mode without a",
        "  full boot. The corrected table emits word `1` at both low-ROM `0484` and",
        "  RAM target `B37A` for raw row `000`, aligning the direct ROM and ROE paths",
        "  with the runnable behavior without inventing an inverter.",
        "- Raw row `000` emits word `1` at both PC `0484` and RAM target `B37A`,",
        "  but the firmware suffix `11` identifies a different checkpoint row.",
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
