#!/usr/bin/env python3
"""Compare the reset-driven juku_top FDC long-window report against cosim."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "juku-top-fdc-alignment.md"
HDL_REPORT = ROOT / "docs" / "juku-top-fdc-verilator-probe.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"
VRAM_WRITES = "70000"


def compile_trace(tmp: Path) -> Path:
    trace = tmp / "trace"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O2",
            "-I",
            str(ROOT / "cosim"),
            "-o",
            str(trace),
            str(ROOT / "cosim" / "trace.c"),
            str(ROOT / "cosim" / "i8080.c"),
            str(ROOT / "cosim" / "juk_disk.c"),
            str(ROOT / "cosim" / "juku_fdc.c"),
        ],
        cwd=ROOT,
        check=True,
    )
    return trace


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            state[key] = value
    return state


def run_cosim(tmp: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    trace = compile_trace(tmp)
    prefix = tmp / "cosim-70000"
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)
    env = os.environ.copy()
    env["JUKU_KEYS"] = "TDD"
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    proc = subprocess.run(
        [str(trace), str(ROM), "250000000", VRAM_WRITES, "200000"],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    state = parse_state(prefix.with_suffix(".state"))
    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()
    return proc, state


def first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else "missing"


def parse_hdl_report() -> dict[str, str]:
    text = HDL_REPORT.read_text()
    state_line = first_match(text, r"^- Visible state line: `\[STATE\] ([^`]+)`$")
    io_line = first_match(text, r"^- I/O summary line: `\[IO\] ([^`]+)`$")
    cpu_line = first_match(text, r"^- CPU state line: `\[CPU\] ([^`]+)`$")
    stop_line = first_match(text, r"^- VRAM stop line: `([^`]+)`$")
    key_first = first_match(text, r"^- First keyboard line: `([^`]+)`$")
    key_last = first_match(text, r"^- Last keyboard line: `([^`]+)`$")

    result: dict[str, str] = {
        "cpu_line": cpu_line,
        "state_line": state_line,
        "io_line": io_line,
        "stop_line": stop_line,
        "key_first": key_first,
        "key_last": key_last,
    }
    for line in (cpu_line, state_line, io_line):
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([0-9A-Fa-fx]+)", line):
            result[key] = value
    return result


def fmt_hex(value: str, prefix: str = "0x") -> str:
    if value == "missing":
        return value
    return f"{prefix}{value.upper()}"


def main() -> int:
    if not HDL_REPORT.exists():
        raise SystemExit(f"missing {HDL_REPORT.relative_to(ROOT)}")
    with tempfile.TemporaryDirectory(prefix="juku-top-fdc-align.") as tmp_name:
        cosim_proc, cosim = run_cosim(Path(tmp_name))
    hdl = parse_hdl_report()

    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim exited {cosim_proc.returncode}")
    if cosim.get("vram_writes") != VRAM_WRITES:
        failures.append(f"cosim did not stop at {VRAM_WRITES} VRAM writes")
    if hdl.get("vram") != VRAM_WRITES:
        failures.append(f"HDL report did not stop at {VRAM_WRITES} VRAM writes")
    if cosim.get("fdc_data_reads") != "6656":
        failures.append("cosim 70k state no longer has 6,656 FDC data reads")
    if hdl.get("fdc_ios") != "0":
        failures.append("HDL 70k report unexpectedly has decoded FDC I/O; regenerate the alignment")

    status = "HDL RESET PATH DIVERGES BEFORE COSIM FDC WINDOW"
    if failures:
        status = "INCOMPLETE"
    lines = [
        "# juku_top FDC reset alignment",
        "",
        f"Status: **{status}**",
        "",
        "This generated report compares the fast cosim `TDD` path at 70,000",
        "framebuffer writes against the committed reset-driven Verilator",
        "`juku_top` report for the same vendored `media/disks/JUKU1.CPM` path.",
        "It keeps the long HDL run out of CI while making the current M2",
        "alignment gap explicit and freshness-checked.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_juku_top_fdc_alignment.py",
        "JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_MAXVRAM=70000 JUKU_TOP_FDC_TIMEOUT=420 sync/juku_top_fdc_probe.sh",
        "```",
        "",
        "## 70,000-Write State",
        "",
        "| Signal | cosim | juku_top Verilator report |",
        "| --- | ---: | ---: |",
        f"| PC | `{fmt_hex(cosim.get('pc', 'missing'))}` | `{fmt_hex(hdl.get('pc', 'missing'))}` |",
        f"| SP | `{fmt_hex(cosim.get('sp', 'missing'))}` | `{fmt_hex(hdl.get('sp', 'missing'))}` |",
        f"| cycles/mcycles | `{cosim.get('cyc', 'missing')}` | `{hdl.get('mcyc', 'missing')}` |",
        f"| memory mode | `{cosim.get('mode', 'missing')}` | `{hdl.get('mode', 'missing')}` |",
        f"| PPI0 port C | `{fmt_hex(cosim.get('portc', 'missing'))}` | `{fmt_hex(hdl.get('portc', 'missing'))}` |",
        f"| PIC ICW1 | `{fmt_hex(cosim.get('pic_icw1', 'missing'))}` | `{fmt_hex(hdl.get('pic_icw1', 'missing'))}` |",
        f"| PIC ICW2 | `{fmt_hex(cosim.get('pic_icw2', 'missing'))}` | `{fmt_hex(hdl.get('pic_icw2', 'missing'))}` |",
        f"| PIC mask | `{fmt_hex(cosim.get('pic_mask', 'missing'))}` | `{fmt_hex(hdl.get('pic_mask', 'missing'))}` |",
        f"| keyboard position/phase | `{cosim.get('kbd_pos', 'missing')}` / `{cosim.get('kbd_phase', 'missing')}` | visible stimulus only |",
        f"| FDC command | `{fmt_hex(cosim.get('fdc_command', 'missing'))}` | `{fmt_hex(hdl.get('fdc_command', 'missing'))}` |",
        f"| FDC track/sector | `{cosim.get('fdc_track', 'missing')}` / `{cosim.get('fdc_sector', 'missing')}` | `{hdl.get('fdc_track', 'missing')}` / `{hdl.get('fdc_sector', 'missing')}` |",
        f"| FDC data reads | `{cosim.get('fdc_data_reads', 'missing')}` | `{hdl.get('fdc_reads', 'missing')}` decoded reads (`{hdl.get('fdc_ios', 'missing')}` ios) |",
        "",
        "## HDL Report Anchors",
        "",
        f"- Stop line: `{hdl['stop_line']}`",
        f"- CPU line: `{hdl['cpu_line']}`",
        f"- State line: `{hdl['state_line']}`",
        f"- I/O summary line: `{hdl['io_line']}`",
        f"- First keyboard line: `{hdl['key_first']}`",
        f"- Last keyboard line: `{hdl['key_last']}`",
        "",
        "## Disposition",
        "",
    ]
    if failures:
        lines.extend(f"- FAIL: {failure}" for failure in failures)
    else:
        lines.extend(
            [
                "- This is not just a simulator-throughput limitation at the 70,000-write boundary.",
                "- Cosim is already in the interrupt/FDC path with 6,656 data-register reads, while reset-driven `juku_top` has not programmed the PIC and has no decoded FDC I/O.",
                "- The next automatic target is the interval after the proven 30,000-write match and before cosim PC `0x02B9` / first PIC programming.",
            ]
        )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
