#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

import pcbnew


PLANNING_BUDGET_A = 1.81
FUSE_HOLD_A = 3.0
FUSE_TRIP_A = 5.1
FUSE_VMAX_V = 16.0
FUSE_HOLD_40C_A = 2.6
FUSE_HOLD_60C_A = 2.1
MIN_HOLD_MARGIN = 1.5
MAX_GROSS_FAULT_HOLD_A = 4.0
EXPECTED_FUSE_MPN = "MF-RG300-0-14"
EXPECTED_FUSE_CPN = "C3761779"
EXPECTED_FUSE_FOOTPRINT = "Fuse_Bourns_MF-RG300"


def read_text(path):
    return Path(path).read_text(errors="replace")


def bom_rows(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def expanded_designators(row):
    refs = []
    for token in row.get("Designator", "").replace(",", " ").split():
        if "-" in token and token[0].isalpha():
            prefix = token[0]
            start, end = token[1:].split("-", 1)
            if end.startswith(prefix):
                end = end[1:]
            refs.extend(f"{prefix}{idx}" for idx in range(int(start), int(end) + 1))
        elif token:
            refs.append(token)
    return refs


def bom_row_for(rows, ref):
    return next((row for row in rows if ref in expanded_designators(row)), None)


def row_text(row):
    if not row:
        return ""
    return " ".join(str(value) for value in row.values())


def cpn(row):
    if not row:
        return ""
    return row.get("JLCPCB/LCSC CPN") or row.get("LCSC") or row.get("CPN") or ""


def footprint_by_ref(board):
    return {fp.GetReference().upper(): fp for fp in board.Footprints()}


def pad_net(fp, number):
    pad = fp.FindPadByNumber(str(number)) if fp else None
    return pad.GetNetname() if pad else ""


def pad_nets(fp):
    if not fp:
        return []
    return [pad.GetNetname() for pad in fp.Pads() if pad.GetNetname()]


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName()) if fp else "missing"


def has_doc_phrase(text, phrase):
    normalized_text = " ".join(text.lower().split())
    normalized_phrase = " ".join(phrase.lower().split())
    return normalized_phrase in normalized_text


def check(condition, failures, message):
    if not condition:
        failures.append(message)


def build_report(board_path, bom_path, budget_doc_path):
    board = pcbnew.LoadBoard(str(board_path))
    fps = footprint_by_ref(board)
    rows = bom_rows(bom_path)
    doc = read_text(budget_doc_path)
    failures = []

    f1 = fps.get("F1")
    j1 = fps.get("J1")
    j3 = fps.get("J3")
    r30 = fps.get("R30")
    r31 = fps.get("R31")
    f1_row = bom_row_for(rows, "F1")
    f1_text = row_text(f1_row)
    hold_margin = FUSE_HOLD_A / PLANNING_BUDGET_A

    budget_marker = f"**{PLANNING_BUDGET_A:.2f} A**"
    check(budget_marker in doc, failures, f"power budget doc does not record the {PLANNING_BUDGET_A:.2f} A planning budget")
    check(EXPECTED_FUSE_MPN in doc, failures, f"power budget doc does not mention {EXPECTED_FUSE_MPN}")
    check(EXPECTED_FUSE_CPN in doc, failures, f"power budget doc does not mention {EXPECTED_FUSE_CPN}")
    check("Hold current: 3.0 A at 23 C" in doc, failures, "power budget doc does not record the 3 A / 23 C hold point")
    check("Trip current: 5.1 A at 23 C" in doc, failures, "power budget doc does not record the 5.1 A / 23 C trip point")
    check("Maximum voltage: 16 V" in doc, failures, "power budget doc does not record the 16 V maximum")
    check("2.6 A at 40 C" in doc and "2.1 A at 60 C" in doc, failures, "power budget doc does not carry the F1 thermal-derating points")
    check(has_doc_phrase(doc, "gross short / wiring fault protection"), failures, "power budget doc does not state the fuse role")
    check(has_doc_phrase(doc, "do not assume it can supply the full planning budget"), failures, "power budget doc does not carry the USB-C current caveat")

    check(f1 is not None, failures, "F1 footprint missing")
    check(EXPECTED_FUSE_FOOTPRINT in footprint_name(f1), failures, f"F1 footprint is not {EXPECTED_FUSE_FOOTPRINT}")
    check(pad_net(f1, 1) == "VCC_RAW", failures, "F1.1 is not on VCC_RAW")
    check(pad_net(f1, 2) == "VCC", failures, "F1.2 is not on VCC")

    check(f1_row is not None, failures, "F1 engineering BOM row missing")
    check(EXPECTED_FUSE_MPN in f1_text, failures, f"F1 engineering BOM row does not mention {EXPECTED_FUSE_MPN}")
    check(cpn(f1_row) == EXPECTED_FUSE_CPN, failures, f"F1 engineering BOM CPN is not {EXPECTED_FUSE_CPN}")
    check("VCC_RAW" in f1_text and "fused VCC" in f1_text, failures, "F1 engineering BOM notes do not describe raw-to-fused VCC")
    check((f1_row or {}).get("Assembly", "") == "Factory preferred", failures, "F1 engineering BOM assembly policy is not Factory preferred")

    check(j1 is not None, failures, "J1 footprint missing")
    check("VCC_RAW" in pad_nets(j1), failures, "J1 does not feed VCC_RAW")
    check("GND" in pad_nets(j1), failures, "J1 does not provide GND")
    check(j3 is not None, failures, "J3 footprint missing")
    check(pad_net(j3, "A9") == "VCC_RAW" and pad_net(j3, "B9") == "VCC_RAW", failures, "J3 VBUS pads are not on VCC_RAW")
    check("GND" in pad_nets(j3), failures, "J3 does not provide GND")
    check(pad_net(r30, 1) == "USB_CC1" and pad_net(r30, 2) == "GND", failures, "R30 is not USB_CC1 to GND")
    check(pad_net(r31, 1) == "USB_CC2" and pad_net(r31, 2) == "GND", failures, "R31 is not USB_CC2 to GND")

    check(hold_margin >= MIN_HOLD_MARGIN, failures, f"F1 hold margin {hold_margin:.2f}x is below {MIN_HOLD_MARGIN:.2f}x")
    check(FUSE_HOLD_A <= MAX_GROSS_FAULT_HOLD_A, failures, f"F1 hold current {FUSE_HOLD_A:.2f} A is above {MAX_GROSS_FAULT_HOLD_A:.2f} A gross-fault guardrail")

    status = "READY" if not failures else "NOT READY"
    rows_out = [
        ("Planning +5V budget", f"{PLANNING_BUDGET_A:.2f} A", "PASS" if budget_marker in doc else "FAIL"),
        ("F1 hold current", f"{FUSE_HOLD_A:.2f} A", "PASS" if hold_margin >= MIN_HOLD_MARGIN else "FAIL"),
        ("F1 trip current at 23 C", f"{FUSE_TRIP_A:.2f} A", "PASS"),
        ("F1 maximum voltage", f"{FUSE_VMAX_V:.0f} V", "PASS"),
        ("F1 hold current at 40/60 C", f"{FUSE_HOLD_40C_A:.1f} / {FUSE_HOLD_60C_A:.1f} A", "PASS"),
        ("F1 hold/budget margin", f"{hold_margin:.2f}x", "PASS" if hold_margin >= MIN_HOLD_MARGIN else "FAIL"),
        ("F1 candidate", f"{EXPECTED_FUSE_MPN} / {EXPECTED_FUSE_CPN}", "PASS" if f1_row and cpn(f1_row) == EXPECTED_FUSE_CPN else "FAIL"),
        ("F1 topology", "VCC_RAW -> F1 -> VCC", "PASS" if pad_net(f1, 1) == "VCC_RAW" and pad_net(f1, 2) == "VCC" else "FAIL"),
        ("J1 input", "VCC_RAW + GND", "PASS" if "VCC_RAW" in pad_nets(j1) and "GND" in pad_nets(j1) else "FAIL"),
        ("J3 USB-C input", "VBUS to VCC_RAW, CC1/CC2 pulldowns", "PASS" if pad_net(j3, "A9") == "VCC_RAW" and pad_net(j3, "B9") == "VCC_RAW" and pad_net(r30, 2) == "GND" and pad_net(r31, 2) == "GND" else "FAIL"),
    ]

    lines = [
        "# Rev A power budget readiness",
        "",
        f"Board: `{board_path}`",
        f"BOM: `{bom_path}`",
        f"Budget doc: `{budget_doc_path}`",
        f"Status: **{status}**",
        "",
        "This report machine-checks the Rev A +5V planning budget against the",
        "selected input fuse, engineering BOM row, and PCB power-entry topology.",
        "It does not replace order-time review of trace width, connector rating,",
        "ambient derating, final IC choices, or vendor stock.",
        "",
        "## Summary",
        "",
        f"- Planning budget: {PLANNING_BUDGET_A:.2f} A",
        f"- Fuse hold current: {FUSE_HOLD_A:.2f} A",
        f"- Hold-current margin over planning budget: {hold_margin:.2f}x",
        f"- Fuse candidate: {EXPECTED_FUSE_MPN} / {EXPECTED_FUSE_CPN}",
        f"- F1 footprint: {footprint_name(f1)}",
        f"- Power-budget failures: {len(failures)}",
        "",
        "## Checked Items",
        "",
        "| Item | Value | Status |",
        "| --- | --- | --- |",
    ]
    for label, value, row_status in rows_out:
        lines.append(f"| {label} | {value} | {row_status} |")
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.extend(
        [
            "",
            "## Remaining Human Review",
            "",
            "- Recheck the guarded exact PTC datasheet, stock, and assembly availability at order time.",
            "- Qualify the PTC against actual ambient/board rise and first-article insertion.",
            "- Confirm J1/J3 current rating and selected power source behavior.",
            "- Review +5V trace width, connector thermal margin, ambient derating, and final socketed IC choices.",
            "",
        ]
    )
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    bom_path = Path(sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a.bom.csv")
    budget_doc_path = Path(sys.argv[3] if len(sys.argv) > 3 else "spinoffs/minimal-vga/docs/rev-a-power-budget.md")
    out_dir = Path(sys.argv[4] if len(sys.argv) > 4 else "fab/minimal-vga")
    report, ready = build_report(board_path, bom_path, budget_doc_path)
    report_path = out_dir / "power-budget-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
