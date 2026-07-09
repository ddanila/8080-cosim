#!/usr/bin/env python3
"""Summarize the committed reset-driven juku_top FDC boundary report."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "juku-top-fdc-alignment.md"
HDL_REPORT = ROOT / "docs" / "juku-top-fdc-verilator-probe.md"


def first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else "missing"


def parse_hdl_report() -> dict[str, str]:
    text = HDL_REPORT.read_text()
    result: dict[str, str] = {
        "status": first_match(text, r"^Status: \*\*(.+)\*\*$"),
        "current_values": first_match(text, r"^Current values: `([^`]+)`\.?$"),
        "disk_line": first_match(text, r"^- Disk line: `([^`]+)`$"),
        "first_vram": first_match(text, r"^- First VRAM line: `([^`]+)`$"),
        "last_progress": first_match(text, r"^- Last VRAM progress line: `([^`]+)`$"),
        "vram_stop": first_match(text, r"^- VRAM stop line: `([^`]+)`$"),
        "first_pic": first_match(text, r"^- First PIC line: `([^`]+)`$"),
        "first_irq": first_match(text, r"^- First IRQ line: `([^`]+)`$"),
        "first_ppi_key": first_match(text, r"^- First PPI key-read line: `([^`]+)`$"),
        "first_fdc": first_match(text, r"^- First FDC line: `([^`]+)`$"),
        "fdc_stop": first_match(text, r"^- FDC stop line: `([^`]+)`$"),
        "cpu_line": first_match(text, r"^- CPU state line: `\[CPU\] ([^`]+)`$"),
        "state_line": first_match(text, r"^- Visible state line: `\[STATE\] ([^`]+)`$"),
        "io_line": first_match(text, r"^- I/O summary line: `\[IO\] ([^`]+)`$"),
    }

    for line in (result["cpu_line"], result["state_line"], result["io_line"]):
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([0-9A-Fa-fx]+)", line):
            result[key] = value

    for label, key in (
        ("PIC setup trace observed", "pic_observed"),
        ("PPI key-read trace observed", "ppi_key_observed"),
        ("IRQ trace observed", "irq_observed"),
        ("decoded FDC I/O observed", "fdc_observed"),
    ):
        result[key] = first_match(text, rf"^\| {re.escape(label)} \| `?([^`|]+)`? \|$")

    return result


def main() -> int:
    if not HDL_REPORT.exists():
        raise SystemExit(f"missing {HDL_REPORT.relative_to(ROOT)}")

    hdl = parse_hdl_report()
    failures: list[str] = []
    if "FDC PATH OBSERVED" not in hdl["status"]:
        failures.append("HDL Verilator report is not marked FDC-observed")
    if hdl.get("fdc_ios", "0") in ("0", "missing"):
        failures.append("HDL report has no decoded FDC I/O count")
    if hdl.get("fdc_writes", "0") in ("0", "missing"):
        failures.append("HDL report has no decoded FDC writes")
    if hdl["first_fdc"] in ("none", "missing"):
        failures.append("HDL report has no first FDC line")
    if hdl["first_pic"] in ("none", "missing"):
        failures.append("HDL report has no first PIC line")

    status = "HDL RESET RUN REACHES DECODED FDC COMMAND I/O"
    if failures:
        status = "INCOMPLETE"

    lines = [
        "# juku_top FDC reset alignment",
        "",
        f"Status: **{status}**",
        "",
        "This generated report summarizes the committed reset-driven Verilator",
        "`juku_top` FDC probe for the vendored `media/disks/JUKU1.CPM` path.",
        "The old post-30,180 reset-run divergence is resolved. The current",
        "uninterrupted boundary reaches decoded WD1793 command/data I/O, but",
        "lands in an early interrupt-path read-sector attempt with sector `0xAA`",
        "rather than the cosim `TDD` sector sequence.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_juku_top_fdc_alignment.py",
        "JUKU_TOP_FDC_SIM=verilator \\",
        "JUKU_TOP_FDC_FRAMEIRQ=200000 \\",
        "JUKU_TOP_FDC_STOPPIC=0 \\",
        "JUKU_TOP_FDC_STOPFDC=80 \\",
        "JUKU_TOP_FDC_TIMECAP=2400000000 \\",
        "JUKU_TOP_FDC_MAXVRAM=90000 \\",
        "JUKU_TOP_FDC_TIMEOUT=300 \\",
        "sync/juku_top_fdc_probe.sh",
        "```",
        "",
        f"Current HDL probe values: `{hdl['current_values']}`.",
        "",
        "## Boundary",
        "",
        "| Signal | juku_top Verilator report |",
        "| --- | ---: |",
        f"| PC | `0x{hdl.get('pc', 'missing').upper()}` |",
        f"| SP | `0x{hdl.get('sp', 'missing').upper()}` |",
        f"| M-cycles | `{hdl.get('mcyc', 'missing')}` |",
        f"| VRAM writes | `{hdl.get('vram', 'missing')}` |",
        f"| memory mode | `{hdl.get('mode', 'missing')}` |",
        f"| PPI0 port C | `0x{hdl.get('portc', 'missing').upper()}` |",
        f"| PIC ICW1/ICW2/mask | `0x{hdl.get('pic_icw1', 'missing').upper()}` / `0x{hdl.get('pic_icw2', 'missing').upper()}` / `0x{hdl.get('pic_mask', 'missing').upper()}` |",
        f"| frame ticks / IRQ edges | `{hdl.get('frame_ticks', 'missing')}` / `{hdl.get('intr_edges', 'missing')}` |",
        f"| FDC command/status | `0x{hdl.get('fdc_command', 'missing').upper()}` / `0x{hdl.get('fdc_status', 'missing').upper()}` |",
        f"| FDC track/sector/data | `0x{hdl.get('fdc_track', 'missing').upper()}` / `0x{hdl.get('fdc_sector', 'missing').upper()}` / `0x{hdl.get('fdc_data', 'missing').upper()}` |",
        f"| decoded FDC reads/writes | `{hdl.get('fdc_reads', 'missing')}` / `{hdl.get('fdc_writes', 'missing')}` (`{hdl.get('fdc_ios', 'missing')}` ios) |",
        "",
        "## HDL Report Anchors",
        "",
        f"- Disk line: `{hdl['disk_line']}`",
        f"- First VRAM line: `{hdl['first_vram']}`",
        f"- Last VRAM progress line: `{hdl['last_progress']}`",
        f"- VRAM stop line: `{hdl['vram_stop']}`",
        f"- First PIC line: `{hdl['first_pic']}`",
        f"- First IRQ line: `{hdl['first_irq']}`",
        f"- First PPI key-read line: `{hdl['first_ppi_key']}`",
        f"- First FDC line: `{hdl['first_fdc']}`",
        f"- FDC stop line: `{hdl['fdc_stop']}`",
        f"- CPU line: `[CPU] {hdl['cpu_line']}`",
        f"- State line: `[STATE] {hdl['state_line']}`",
        f"- I/O summary line: `[IO] {hdl['io_line']}`",
        "",
        "## Disposition",
        "",
    ]

    if failures:
        lines.extend(f"- FAIL: {failure}" for failure in failures)
    else:
        lines.extend(
            [
                "- The D6 reset-overlay ROM decode now covers `0x0000..0x3FFF`, so the high-BIOS checksum path matches cosim past the old 30,181-write split.",
                "- The HDL WD1793 status read now reflects live motor/disk readiness, so the reset run exits the stale not-ready poll and reaches command/data-register traffic.",
                "- With `JUKU_TOP_FDC_FRAMEIRQ=200000`, the uninterrupted reset run programs the PIC, takes frame interrupts, writes WD1793 sector/data/command registers, and enters data-register reads.",
                "- The remaining uninterrupted HDL target is to align this early interrupt-path read-sector attempt with the cosim ROMBIOS `TDD` sequence: first command `0x02`, sector `0x02`, and then EKDOS `A>`.",
            ]
        )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
