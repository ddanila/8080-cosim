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
        "The no-key keyboard scan now matches the cosim anchor; the remaining",
        "reset-run mismatch is now narrowed to the pre-FDC interrupt/CPU path",
        "after the first calibrated frame IRQ.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_juku_top_fdc_alignment.py",
        "JUKU_TOP_FDC_SIM=verilator \\",
        "JUKU_TOP_FDC_FRAMEIRQ=200000 \\",
        "JUKU_TOP_FDC_FRAMEPHASE=0 \\",
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
        f"| keyboard-port scans | `{hdl.get('ppi_key_reads', 'missing')}` |",
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
        f"- First PPI line: `{hdl['first_ppi']}`",
        f"- First FDC line: `{hdl['first_fdc']}`",
        f"- FDC stop line: `{hdl['fdc_stop']}`",
        f"- CPU line: `[CPU] {hdl['cpu_line']}`",
        f"- State line: `[STATE] {hdl['state_line']}`",
        f"- I/O summary line: `[IO] {hdl['io_line']}`",
        "",
        "## Frame Calibration Check",
        "",
        "The no-frame calibration bound used for the current diagnosis is:",
        "",
        "```sh",
        "JUKU_TOP_FDC_SIM=verilator \\",
        "JUKU_TOP_FDC_FRAMEIRQ=0 \\",
        "JUKU_TOP_FDC_STOPFDC=0 \\",
        "JUKU_TOP_FDC_MAXVRAM=33812 \\",
        "JUKU_TOP_FDC_TIMECAP=1200000000 \\",
        "JUKU_TOP_FDC_TIMEOUT=180 \\",
        "sync/juku_top_fdc_probe.sh",
        "```",
        "",
        "It reaches `[VRAM] 33812 writes (mcyc=852989) -- dump` with no frame IRQ",
        "and no decoded FDC I/O, matching the cosim first-frame-IRQ framebuffer",
        "position before the reset-run timer currently diverts into the early FDC",
        "helper.",
        "",
        "## Machine-Cycle Frame Probe",
        "",
        "The top-level FDC wrapper also has an opt-in machine-cycle frame scheduler:",
        "",
        "```sh",
        "JUKU_TOP_FDC_SIM=verilator \\",
        "JUKU_TOP_FDC_FRAMEIRQ=0 \\",
        "JUKU_TOP_FDC_FRAMEMCYC=80000 \\",
        "JUKU_TOP_FDC_FRAMEPHASE=52989 \\",
        "JUKU_TOP_FDC_TRACEIRQ=2 \\",
        "JUKU_TOP_FDC_MAXVRAM=50000 \\",
        "JUKU_TOP_FDC_TIMECAP=300000000 \\",
        "JUKU_TOP_FDC_TIMEOUT=90 \\",
        "sync/juku_top_fdc_probe.sh",
        "```",
        "",
        "That calibration moves the first accepted HDL frame IRQ to the cosim",
        "framebuffer/mcycle anchor: `[IRQ] intr rise count=1 pc=0x0244",
        "sp=0xd44e osc=6727121 mcyc=852989 vram=33811`, followed by INTA",
        "bytes `0xCD 0xD4 0xFE` at VRAM `33812`. This proves the sim-only",
        "8259 CALL-vector injection still returns the expected `0xFED4` vector",
        "at the calibrated point.",
        "",
        "It does not yet make the uninterrupted run match the cosim CPU path:",
        "`docs/ekdos-timing-reference.md` records the first cosim IRQ at PC",
        "`0x0E21`, while the no-frame HDL state at the same 33,812-write",
        "boundary is PC `0x0244`. A no-frame stop-PC probe for `0x0E21` did not",
        "hit by 90,000 VRAM writes and ended at PC `0x0484`, so the next target",
        "is the pre-FDC CPU/video timing path rather than only the frame phase.",
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
                "- The first HDL keyboard-port read is now visible and matches the cosim no-key anchor: `IN 0x05 = 0xCF` at PC `0x1213`, VRAM `30520`.",
                "- With `JUKU_TOP_FDC_FRAMEIRQ=200000`, the uninterrupted reset run programs the PIC, takes frame interrupts, writes WD1793 sector/data/command registers, and enters data-register reads.",
                "- The oscillator-period reset run still takes its first IRQ too early: current reset-run IRQ is at VRAM `30524`, while `docs/ekdos-timing-reference.md` pins the cosim first frame IRQ at VRAM `33812`.",
                "- The new machine-cycle scheduler can align the first accepted frame IRQ to `mcyc=852989` / VRAM `33811..33812` and injects the expected `0xFED4` vector, but HDL is still at PC `0x0244` there instead of cosim PC `0x0E21`.",
                "- The remaining uninterrupted HDL target is now the pre-FDC CPU/video timing path that leads from the calibrated frame IRQ through the cosim ROMBIOS `TDD` sequence: first command `0x02`, sector `0x02`, and then EKDOS `A>`.",
            ]
        )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
