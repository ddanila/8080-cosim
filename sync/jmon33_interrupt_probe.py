#!/usr/bin/env python3
"""Probe jmon33's interrupt-driven monitor path in cosim."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-interrupt-probe.md"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, check=False, **kwargs)


def main() -> int:
    max_cycles = int(os.environ.get("JMON33_PROBE_MAX_CYCLES", "5000000"))
    frame_cycles = int(os.environ.get("JMON33_PROBE_FRAME_CYCLES", "200000"))
    cc = os.environ.get("CC", "cc")

    with tempfile.TemporaryDirectory() as td:
        trace = Path(td) / "trace"
        build = run([
            cc,
            "-O2",
            "-I",
            "cosim",
            "-o",
            str(trace),
            "cosim/trace.c",
            "cosim/i8080.c",
            "cosim/juk_disk.c",
            "cosim/juku_fdc.c",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if build.returncode != 0:
            sys.stderr.write(build.stdout)
            sys.stderr.write(build.stderr)
            return build.returncode

        proc = subprocess.run(
            [str(trace), "../roms/jmon33.bin", str(max_cycles), "0", str(frame_cycles)],
            cwd=ROOT / "cosim",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    log = proc.stderr + "\n" + proc.stdout

    checks = {
        "rom_loaded": "loaded 16384 bytes of ROM" in log,
        "pic_programmed": "[OUT] first write port 0x00 = 0x56" in log
        and "[OUT] first write port 0x01 = 0xFF" in log,
        "frame_irq_taken": "[IRQ] taken #1" in log and "vec=FF54" in log,
        "keyboard_scan": "[IN ] first read  port 0x04" in log
        and "[IN ] first read  port 0x05" in log,
        "vram_written": bool(re.search(r"0xD[B-C]00\s+:\s+[1-9]", log)),
    }
    passed = all(checks.values()) and proc.returncode == 0
    status = "JMON33 INTERRUPT PATH READY" if passed else "JMON33 INTERRUPT PATH NOT READY"

    irq_lines = [line for line in proc.stderr.splitlines() if line.startswith("[IRQ]")]
    first_reads = [
        line for line in proc.stderr.splitlines()
        if line.startswith("[IN ] first read") or line.startswith("[OUT] first write")
    ][:24]
    stopped = next((line for line in proc.stderr.splitlines() if line.startswith("stopped ")), "")

    REPORT.write_text("\n".join([
        "# jmon33 interrupt-path probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe exercises the interrupt-driven Juku Monitor 3.3 ROM in cosim.",
        "Unlike ekta37, jmon33 depends on frame interrupts and keyboard/serial",
        "service paths before it becomes useful as an interactive monitor.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_interrupt_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_PROBE_MAX_CYCLES` default `{max_cycles}`",
        f"- `JMON33_PROBE_FRAME_CYCLES` default `{frame_cycles}`",
        "",
        "## Evidence",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| jmon33 ROM loaded | {'PASS' if checks['rom_loaded'] else 'FAIL'} |",
        f"| 8259 programmed for MCS-80 vectoring | {'PASS' if checks['pic_programmed'] else 'FAIL'} |",
        f"| Frame interrupt taken at `0xFF54` | {'PASS' if checks['frame_irq_taken'] else 'FAIL'} |",
        f"| Keyboard matrix ports read | {'PASS' if checks['keyboard_scan'] else 'FAIL'} |",
        f"| Monitor writes video RAM | {'PASS' if checks['vram_written'] else 'FAIL'} |",
        "",
        "## Trace Highlights",
        "",
        "```text",
        *(irq_lines[:4] or ["<no IRQ lines observed>"]),
        stopped or "<no stopped line observed>",
        "```",
        "",
        "First I/O activity:",
        "",
        "```text",
        *(first_reads or ["<no first I/O lines observed>"]),
        "```",
        "",
        "## Remaining Boundary",
        "",
        "- This fast probe proves that the interrupt-driven monitor path is alive in",
        "  cosim; it is not the user-visible completion oracle by itself.",
        "- `docs/jmon33-ready-probe.md` records the stronger cosim monitor-idle",
        "  framebuffer oracle, and `docs/jmon33-hdl-cursor-probe.md` records the",
        "  matching structural-HDL cursor result.",
    ]) + "\n")

    print(f"JMON33-PROBE: {'PASS' if passed else 'FAIL'}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
