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
        "first_ppi": first_match(text, r"^- First PPI line: `([^`]+)`$"),
        "first_fdc": first_match(text, r"^- First FDC line: `([^`]+)`$"),
        "fdc_stop": first_match(text, r"^- FDC stop line: `([^`]+)`$"),
        "fdc_data_stop": first_match(text, r"^- FDC data-stop line: `([^`]+)`$"),
        "prompt_line": first_match(text, r"^- EKDOS prompt line: `([^`]+)`$"),
        "cpu_line": first_match(text, r"^- CPU state line: `\[CPU\] ([^`]+)`$"),
        "state_line": first_match(text, r"^- Visible state line: `\[STATE\] ([^`]+)`$"),
        "io_line": first_match(text, r"^- I/O summary line: `\[IO\] ([^`]+)`$"),
        "fdc_state_line": first_match(text, r"^- FDC state line: `\[FDCSTATE\] ([^`]+)`$"),
    }

    for line in (result["cpu_line"], result["state_line"], result["io_line"], result["fdc_state_line"]):
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([0-9A-Fa-fx]+)", line):
            result[key] = value

    for label, key in (
        ("PIC setup trace observed", "pic_observed"),
        ("PPI key-read trace observed", "ppi_key_observed"),
        ("IRQ trace observed", "irq_observed"),
        ("decoded FDC I/O observed", "fdc_observed"),
        ("EKDOS `A>` prompt bitmap observed", "prompt_observed"),
    ):
        result[key] = first_match(text, rf"^\| {re.escape(label)} \| `?([^`|]+)`? \|$")

    return result


def main() -> int:
    if not HDL_REPORT.exists():
        raise SystemExit(f"missing {HDL_REPORT.relative_to(ROOT)}")

    hdl = parse_hdl_report()
    failures: list[str] = []
    if "EKDOS PROMPT REACHED" not in hdl["status"]:
        failures.append("HDL Verilator report is not marked prompt-reached")
    if hdl.get("fdc_ios", "0") in ("0", "missing"):
        failures.append("HDL report has no decoded FDC I/O count")
    if hdl.get("fdc_writes", "0") in ("0", "missing"):
        failures.append("HDL report has no decoded FDC writes")
    if hdl.get("data_reads", "0") != "10752":
        failures.append("HDL report did not drain 10,752 FDC data-register reads")
    if hdl["prompt_line"] in ("none", "missing"):
        failures.append("HDL report has no EKDOS prompt line")
    if hdl["first_pic"] in ("none", "missing"):
        failures.append("HDL report has no first PIC line")

    status = "HDL RESET RUN REACHES EKDOS A> PROMPT"
    if failures:
        status = "INCOMPLETE"

    lines = [
        "# juku_top FDC reset alignment",
        "",
        f"Status: **{status}**",
        "",
        "This report summarizes the [recorded Verilator run](juku-top-fdc-verilator-probe.md)",
        "for `media/disks/JUKU1.CPM`. It checks that report's prompt, PIC and FDC",
        "markers and counts; it does not build or execute the current HDL.",
        "The recorded run drained 10,752 FDC data-register reads and reached",
        "the EKDOS `A>` bitmap at 73,405 framebuffer writes.",
        "See [simulator compatibility](../sync/README.md#simulator-compatibility)",
        "before attempting a current Verilator rerun.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_juku_top_fdc_alignment.py",
        "JUKU_TOP_FDC_SIM=verilator \\",
        "JUKU_TOP_FDC_FRAMEIRQ=0 \\",
        "JUKU_TOP_FDC_FRAMEMCYC=50761 \\",
        "JUKU_TOP_FDC_FRAMEPHASE=49891 \\",
        "JUKU_TOP_FDC_STOPPIC=0 \\",
        "JUKU_TOP_FDC_TRACEFDC=0 \\",
        "JUKU_TOP_FDC_STOPFDC=0 \\",
        "JUKU_TOP_FDC_STOPPROMPT=1 \\",
        "JUKU_TOP_FDC_TIMECAP=12000000000 \\",
        "JUKU_TOP_FDC_MAXVRAM=100000 \\",
        "JUKU_TOP_FDC_TIMEOUT=420 \\",
        "sync/juku_top_fdc_probe.sh",
        "```",
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
        f"| keyboard-port scans | `{hdl.get('ppi_key_reads', 'missing')}` |",
        f"| FDC command/status | `0x{hdl.get('fdc_command', 'missing').upper()}` / `0x{hdl.get('fdc_status', 'missing').upper()}` |",
        f"| FDC track/sector/data | `0x{hdl.get('fdc_track', 'missing').upper()}` / `0x{hdl.get('fdc_sector', 'missing').upper()}` / `0x{hdl.get('fdc_data', 'missing').upper()}` |",
        f"| decoded FDC reads/writes | `{hdl.get('fdc_reads', 'missing')}` / `{hdl.get('fdc_writes', 'missing')}` (`{hdl.get('fdc_ios', 'missing')}` ios) |",
        f"| FDC data-register reads | `{hdl.get('data_reads', 'missing')}` |",
        "",
        "## Scope",
        "",
        "- The recorded configuration uses a machine-cycle frame period of",
        "  50,761 with the first tick at 49,891, rather than the oscillator-period",
        "  frame scheduler. These values align this ROM/disk path with the C oracle.",
        "- `sync/juku_top_fdc_prompt_check.sh` normally checks committed report",
        "  evidence. Set `JUKU_TOP_FDC_PROMPT_DEEP=1` to compile and rerun the HDL.",
        "- Report consistency alone does not establish current-source execution",
        "  or physical FDC qualification.",
        "",
    ]
    if failures:
        lines.extend(["## Missing evidence", ""])
        lines.extend(f"- {failure}" for failure in failures)
        lines.append("")

    REPORT.write_text("\n".join(lines).rstrip() + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
