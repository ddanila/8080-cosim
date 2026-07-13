#!/usr/bin/env python3
"""Guard the complete ДГШ5.109.009 ПЭЗ IC identity census."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/juku-official-009-ic-census.json"
BOARD = ROOT / "kicad/juku.board.json"
REPORT = ROOT / "docs/official-009-ic-census.md"

MARK_TYPE = {
    "КР580ИК80А": "CPU8080", "КР556РТ4": "PROM_RT4", "КР556РТ4А": "PROM_RT4",
    "К561ЛН2": "LN2", "КР580ВА86": "BUF8286", "КР580ВК38": "SYS8238",
    "К555ЛА3": "LA3_GATE", "К155ЛА3": "LA3_GATE", "КР1533ЛА3": "LA3_GATE", "К155РЕ3": "PROM_RE3",
    "К555ИД7": "IO_DEC138", "КР580ВН59": "PIC8259", "КР580ВВ51А": "USART8251",
    "К155ЛА18": "LA18", "К555ТЛ2": "TL2", "К170АП2": "AP2",
    "К573РФ5": "EPROM8K", "К573РФ6": "EPROM8K", "КР580ВА87": "BUS8287",
    "КР580ВВ55А": "PPI8255", "К155ЛН3": "LN3_OC_INV", "КМ555ТМ2": "TM2_DFF",
    "КР531ЛН1": "FAST_INV", "К555ЛП5": "LP5_XOR", "К155ЛН5": "CLK_PHASE",
    "КР531ЛА12": "LA12_GATE", "КР531ЛА1": "LA1_GATE", "КР531ИЕ17": "CT16_CTR",
    "К555ИР16": "IR16", "К555ИЕ7": "IE7_CTR", "КР531КП14": "KP14_MUX",
    "К555КП14": "KP14_MUX", "КР531ИД7": "RASCAS_DEC", "КР580ВИ53": "PIT8253",
    "КМ555АГ3": "AG3_ONESHOT", "К155АГ3": "AG3_ONESHOT", "КР580ИР82": "IR82",
    "К565РУ5Г": "RU5", "К555ЛЕ4": "LE4", "КР1818ВГ93": "VG93_FDC",
    "К555КП12": "KP12_MUX", "К155ЛП11": "LP11_BUF", "К555ИЕ10": "IE10_CTR",
    "К170УП2": "UP2",
}

TYPE_FAMILY = {
    "WAIT_PROM": "PROM_RT4", "DEC_PROM": "PROM_RT4", "RE3_PROM": "PROM_RE3",
    "RE3_PROM_092": "PROM_RE3", "VABUS": "BUS8287", "BUF8287": "BUS8287",
    "LN1_DUAL": "FAST_INV", "LN1_OSC": "FAST_INV",
}

EXACT_MARKING_REFS = {
    "D2", "D7", "D13", "D19", "D33", "D36", "D37", "D38", "D39", "D40",
    "D41", "D42", "D43", "D48", "D49", "D50", "D51", "D52", "D53", "D56",
    "D59", "D84", "D85", "D86", "D87", "D88", "D89", "D90", "D91", "D97",
    "D99", "D102", "D105",
}

EXPECTED_PROGRAMS = {
    "D2": "ДГШ5.106.037",
    "D6": "ДГШ5.106.038",
    "D8": "ДГШ5.106.039",
    "D15": "ДГШ5.106.087",
    "D16": "ДГШ5.106.041",
    "D17": "ДГШ5.106.042",
    "D18": "ДГШ5.106.043",
    "D19": "ДГШ5.106.088",
    "D20": "ДГШ5.106.089",
    "D21": "ДГШ5.106.090",
    "D22": "ДГШ5.106.091",
    "D94": "ДГШ5.106.092",
}


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    source = ROOT / evidence["source"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    chips = {chip["ref"]: chip for chip in board["chips"]}

    census: dict[str, dict] = {}
    duplicates: list[str] = []
    for item in evidence["rows"]:
        for ref in item["refs"]:
            if ref in census:
                duplicates.append(ref)
            census[ref] = item

    missing = sorted(set(census) - set(chips), key=lambda ref: int(ref[1:]))
    type_mismatches: list[str] = []
    marking_mismatches: list[str] = []
    programs = {}
    report_rows = []
    for ref in sorted(census, key=lambda item: int(item[1:])):
        item = census[ref]
        factory = item["marking"]
        effective = item.get("owner_override", factory)
        chip = chips.get(ref, {})
        actual_type = chip.get("type", "MISSING")
        expected_family = MARK_TYPE[effective]
        actual_family = TYPE_FAMILY.get(actual_type, actual_type)
        type_ok = actual_family == expected_family
        if not type_ok:
            type_mismatches.append(f"{ref}: {actual_type} != {expected_family}")
        marking = chip.get("marking", "")
        marking_ok = ref not in EXACT_MARKING_REFS or marking == effective
        if not marking_ok:
            marking_mismatches.append(f"{ref}: {marking or 'unset'} != {effective}")
        if item.get("program"):
            programs[ref] = item["program"]
        disposition = "owner-observed substitution" if item.get("owner_override") else "factory"
        report_rows.append(row([
            ref, item["page"], factory, effective, actual_type,
            "PASS" if type_ok and marking_ok else "FAIL", disposition,
        ]))

    allowed_extra = {f"D{number}" for number in range(60, 84)}
    numeric_board_refs = {
        ref for ref in chips if ref.startswith("D") and ref[1:].isdigit()
    }
    unexplained_extra = sorted(
        numeric_board_refs - set(census) - allowed_extra,
        key=lambda ref: int(ref[1:]),
    )
    checks = [
        ("Factory PDF checksum matches the transcription", digest == evidence["source_sha256"]),
        ("Every factory-listed IC refdes exists in the board model", not missing),
        ("The transcription has no duplicate refdes", not duplicates),
        ("Every factory/owner marking maps to the modeled logic family", not type_mismatches),
        ("Every known marking correction is explicit in board JSON", not marking_mismatches),
        ("Board-only numeric IC refs are only D60-D83 expansion sockets", not unexplained_extra),
        ("Factory programming identities match .037/.038/.039/.041-.043/.087-.092", programs == EXPECTED_PROGRAMS),
    ]
    ok = all(result for _, result in checks)
    status = "OFFICIAL .009 IC CENSUS GUARDED" if ok else "OFFICIAL .009 IC CENSUS FAILED"

    lines = [
        "# Official .009 IC census", "", f"Status: **{status}**", "",
        "This report transcribes both pages of `ДГШ5.109.009 ПЭЗ` and compares",
        "the factory IC population against the authoritative board model. Factory",
        "markings remain visible even where the photographed owner board proves a",
        "later or alternate compatible population. D60-D83 are the only modeled",
        "numeric IC positions absent from the ПЭЗ; they are retained as explicit",
        "empty DRAM expansion sockets, not claimed as factory-populated parts.", "",
        "## Guard checks", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL"]) for name, result in checks)
    lines += [
        "", "## Factory census", "",
        "| Ref | PDF page | Factory marking | Effective owner marking | Model type | Result | Disposition |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
        *report_rows,
        "", "## Programmed positions", "",
        "| Ref | Factory program |", "| --- | --- |",
    ]
    lines.extend(row([ref, program]) for ref, program in programs.items())
    if missing or duplicates or type_mismatches or marking_mismatches or unexplained_extra:
        lines += ["", "## Failures", ""]
        lines.extend(f"- {item}" for item in (
            [f"missing: {', '.join(missing)}"] if missing else []
        ) + ([f"duplicates: {', '.join(duplicates)}"] if duplicates else [])
            + type_mismatches + marking_mismatches
            + ([f"unexplained board-only refs: {', '.join(unexplained_extra)}"] if unexplained_extra else []))
    lines += [
        "", "## Source", "",
        f"- `{evidence['source']}`",
        f"- SHA256 `{evidence['source_sha256']}`",
        "- Machine-readable transcription: `ref/juku-official-009-ic-census.json`", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{status}: {len(census)} factory positions, {len(programs)} programmed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
