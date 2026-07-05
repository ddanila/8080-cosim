#!/usr/bin/env python3
import math
import sys
from pathlib import Path

import pcbnew


MM_PER_IU = 1_000_000.0


def mm(value):
    return value / MM_PER_IU


def point_mm(point):
    return mm(point.x), mm(point.y)


def footprint_by_ref(board):
    return {fp.GetReference().upper(): fp for fp in board.Footprints()}


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName())


def pad_rows(fp):
    rows = []
    for pad in sorted(fp.Pads(), key=lambda item: item.GetNumber()):
        x, y = point_mm(pad.GetPosition())
        rows.append(
            {
                "pad": pad.GetNumber(),
                "net": pad.GetNetname() or "-",
                "x": x,
                "y": y,
                "drill": mm(pad.GetDrillSize().x),
            }
        )
    return rows


def pitch_between(rows, first="1", second="2"):
    a = next((row for row in rows if row["pad"] == first), None)
    b = next((row for row in rows if row["pad"] == second), None)
    if not a or not b:
        return None
    dx = abs(a["x"] - b["x"])
    dy = abs(a["y"] - b["y"])
    return dx, dy, math.hypot(dx, dy)


def fmt_mm(value):
    return f"{value:.2f} mm"


def make_row(ref, fp, status, expected, actual, note):
    return {
        "Designator": ref,
        "Footprint": footprint_name(fp) if fp else "missing",
        "Expected candidate fit": expected,
        "Measured PCB": actual,
        "Status": status,
        "Notes": note,
    }


def build_rows(board):
    fps = footprint_by_ref(board)
    rows = []
    failures = []
    reviews = []

    j1 = fps.get("J1")
    if j1:
        pads = pad_rows(j1)
        pitch = pitch_between(pads)
        measured = "pads 1-2 unavailable"
        if pitch:
            dx, dy, dist = pitch
            measured = f"pad spacing {fmt_mm(dist)} (dx {fmt_mm(dx)}, dy {fmt_mm(dy)}); drill {fmt_mm(pads[0]['drill'])}"
        rows.append(
            make_row(
                "J1",
                j1,
                "REVIEW",
                "KANGNEX WJ2EDGR-5.08-02P-14-00A, 5.08 mm pitch",
                measured,
                "PCB footprint is nominally 5.00 mm. Difference from the 5.08 mm candidate is small, but confirm the terminal drawing and factory THT tolerance before upload.",
            )
        )
        reviews.append("J1: confirm 5.08 mm terminal fit in the nominal 5.00 mm footprint.")
    else:
        rows.append(make_row("J1", None, "FAIL", "+5V terminal footprint", "missing", "Footprint not found."))
        failures.append("J1 footprint missing.")

    f1 = fps.get("F1")
    if f1:
        pads = pad_rows(f1)
        pitch = pitch_between(pads)
        measured = "pads 1-2 unavailable"
        if pitch:
            dx, dy, dist = pitch
            measured = f"pad spacing {fmt_mm(dist)} (dx {fmt_mm(dx)}, dy {fmt_mm(dy)}); drill {fmt_mm(pads[0]['drill'])}"
        rows.append(
            make_row(
                "F1",
                f1,
                "PASS",
                "Bourns MF-RG300-0-14 / C3761779, MF-RG300-class 5.08 mm lead spacing",
                measured,
                "The board uses KiCad's Bourns MF-RG300 footprint. Final current/load and order-time stock still require human review.",
            )
        )
    else:
        rows.append(make_row("F1", None, "FAIL", "+5V PTC footprint", "missing", "Footprint not found."))
        failures.append("F1 footprint missing.")

    u51 = fps.get("U51")
    if u51:
        pads = pad_rows(u51)
        pitch = pitch_between(pads)
        net_order = ", ".join(f"{row['pad']}={row['net']}" for row in pads)
        measured = f"pin pitch {fmt_mm(pitch[2]) if pitch else 'unknown'}; net order {net_order}"
        rows.append(
            make_row(
                "U51",
                u51,
                "REVIEW",
                "MCP130-460DI/TO or MCP130-475DI/TO TO-92 candidate",
                measured,
                "The TO-92 mechanics match 1.27 mm pitch, but the exact Microchip D-bondout pin order must be confirmed before factory population.",
            )
        )
        reviews.append("U51: confirm MCP130 TO-92 D-bondout pin order against board net order before factory population.")
    else:
        rows.append(make_row("U51", None, "FAIL", "TO-92 reset supervisor footprint", "missing", "Footprint not found."))
        failures.append("U51 footprint missing.")

    for ref in ["R30", "R31"]:
        fp = fps.get(ref)
        if fp:
            pads = pad_rows(fp)
            pitch = pitch_between(pads)
            measured = "pads 1-2 unavailable"
            if pitch:
                dx, dy, dist = pitch
                measured = f"pad spacing {fmt_mm(dist)} (dx {fmt_mm(dx)}, dy {fmt_mm(dy)}); drill {fmt_mm(pads[0]['drill'])}"
            rows.append(
                make_row(
                    ref,
                    fp,
                    "REVIEW",
                    "TyoHM RN 1/8W 5K1 F T/B A1 / C433473, electrically correct but smaller than DIN0207",
                    measured,
                    "The smaller 1/8 W body should fit electrically, but placement/lead forming should be checked if factory-installed.",
                )
            )
            reviews.append(f"{ref}: confirm smaller 1/8 W axial body handling on the larger DIN0207 footprint.")
        else:
            rows.append(make_row(ref, None, "FAIL", "USB-C CC pulldown footprint", "missing", "Footprint not found."))
            failures.append(f"{ref} footprint missing.")

    return rows, reviews, failures


def table(rows):
    columns = ["Designator", "Footprint", "Expected candidate fit", "Measured PCB", "Status", "Notes"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            values.append(str(row[column]).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def build_report(board_path):
    board = pcbnew.LoadBoard(str(board_path))
    rows, reviews, failures = build_rows(board)
    status = "NOT READY" if failures else "REVIEW REQUIRED" if reviews else "READY"
    lines = [
        "# Rev A mechanical-fit readiness",
        "",
        f"Board: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report checks the mechanically sensitive factory-assembly rows that",
        "are not covered by socket pin-count matching. It is intentionally a",
        "fit checklist; it does not replace vendor drawing review at order time.",
        "",
        "## Summary",
        "",
        f"- Checked rows: {len(rows)}",
        f"- Mechanical fit failures: {len(failures)}",
        f"- Human fit reviews still required: {len(reviews)}",
        "",
        "## Rows",
        "",
    ]
    lines.extend(table(rows))
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    if reviews:
        lines.extend(["", "## Required Human Reviews", ""])
        lines.extend(f"- {review}" for review in reviews)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, ready = build_report(board_path)
    report_path = out_dir / "assembly" / "mechanical-fit-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
