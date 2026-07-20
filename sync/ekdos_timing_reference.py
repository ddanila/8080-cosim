#!/usr/bin/env python3
"""Cosim timing reference for the ROMBIOS TDD -> EKDOS path."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ekdos-timing-reference.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"
EXPECTED_FIRSTS = {
    ("OUT", 0x00): {"cyc": "3061541", "pc": "02B9", "g_vw": "30520", "value": "D6"},
    ("OUT", 0x01): {"cyc": "3061556", "pc": "02BC", "g_vw": "30520", "value": "FE"},
    ("IN", 0x05): {"cyc": "3062006", "pc": "1213", "g_vw": "30520", "value": "-"},
    ("OUT", 0x1C): {"cyc": "6666400", "pc": "E5DE", "g_vw": "63085", "value": "02"},
    ("IN", 0x1F): {"cyc": "9039953", "pc": "E5AA", "g_vw": "63095", "value": "-"},
}
EXPECTED_IRQS = [
    {"n": "1", "cyc": "3200001", "pc": "0E21", "vec": "FED4", "g_vw": "33812"},
    {"n": "2", "cyc": "3400004", "pc": "0E25", "vec": "FED4", "g_vw": "38733"},
    {"n": "3", "cyc": "3600000", "pc": "E2E5", "vec": "FED4", "g_vw": "40633"},
]

IOT_RE = re.compile(
    r"^\[IOT\] first (IN |OUT) port 0x([0-9A-Fa-f]{2})(?: val=0x([0-9A-Fa-f]{2}))? "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4}) g_vw=([0-9]+)"
)
IRQ_RE = re.compile(r"^\[IRQ\] taken #([0-9]+) g_vw=([0-9]+) cyc=([0-9]+) pc=([0-9A-Fa-f]{4}).*vec=([0-9A-Fa-f]{4})")


def run_trace() -> subprocess.CompletedProcess[str]:
    cc = os.environ.get("CC", "cc")
    max_cycles = os.environ.get("EKDOS_TIMING_MAX_CYCLES", "250000000")
    frame_cycles = os.environ.get("EKDOS_TIMING_FRAME_CYCLES", "200000")
    with tempfile.TemporaryDirectory(prefix="ekdos-timing.") as tmp:
        trace = Path(tmp) / "trace"
        subprocess.run(
            [
                cc,
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
        env = os.environ.copy()
        env["JUKU_KEYS"] = "TDD"
        env["JUKU_DISK"] = str(DISK)
        env["JUKU_TRACE_TIMING"] = "1"
        return subprocess.run(
            [str(trace), str(ROM), max_cycles, "0", frame_cycles],
            cwd=ROOT / "cosim",
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


def parse(log: str) -> tuple[dict[int, dict[str, str]], dict[int, dict[str, str]], list[dict[str, str]]]:
    first_in: dict[int, dict[str, str]] = {}
    first_out: dict[int, dict[str, str]] = {}
    irqs: list[dict[str, str]] = []
    for line in log.splitlines():
        if match := IOT_RE.match(line):
            direction, port_hex, value, cyc, pc, g_vw = match.groups()
            item = {"cyc": cyc, "pc": pc.upper(), "g_vw": g_vw, "value": value.upper() if value else "-"}
            port = int(port_hex, 16)
            if direction.strip() == "IN":
                first_in[port] = item
            else:
                first_out[port] = item
        elif match := IRQ_RE.match(line):
            n, g_vw, cyc, pc, vec = match.groups()
            irqs.append({"n": n, "g_vw": g_vw, "cyc": cyc, "pc": pc.upper(), "vec": vec.upper()})
    return first_in, first_out, irqs


def row(kind: str, port: int, item: dict[str, str] | None) -> str:
    if not item:
        return f"| {kind} | 0x{port:02X} | - | - | - | - |"
    return f"| {kind} | 0x{port:02X} | {item['value']} | {item['cyc']} | {item['pc']} | {item['g_vw']} |"


def main() -> int:
    proc = run_trace()
    log = (proc.stderr or "") + "\n" + (proc.stdout or "")
    first_in, first_out, irqs = parse(log)
    ports = [0x00, 0x01, 0x04, 0x05, 0x06, 0x07, 0x1C, 0x1D, 0x1E, 0x1F]

    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"trace exited {proc.returncode}")
    for port in (0x00, 0x01, 0x04, 0x05, 0x1C, 0x1F):
        if port not in first_in and port not in first_out:
            failures.append(f"no first-access timing captured for port 0x{port:02X}")
    if not irqs:
        failures.append("no frame IRQ timing captured")
    for (kind, port), expected in EXPECTED_FIRSTS.items():
        actual = first_in.get(port) if kind == "IN" else first_out.get(port)
        if actual != expected:
            failures.append(f"{kind} 0x{port:02X} timing changed: got {actual}, expected {expected}")
    if irqs[:3] != EXPECTED_IRQS:
        failures.append(f"first frame IRQ timing changed: got {irqs[:3]}, expected {EXPECTED_IRQS}")

    lines = [
        "# EKDOS timing reference",
        "",
        f"Status: **{'PASS' if not failures else 'INCOMPLETE'}**",
        "",
        "This is the fast cosim timing reference for the factory `TDD` path with",
        "vendored `media/disks/JUKU1.CPM`. It records where ROMBIOS first touches",
        "the PIC/PPI/FDC ports relative to CPU cycles and framebuffer writes, so",
        "`juku_top` diagnostics can target the right post-banner window.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/ekdos_timing_reference.py",
        "```",
        "",
        "## First I/O Accesses",
        "",
        "| Direction | Port | First value | Cycle | PC | VRAM writes |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for port in ports:
        if port in first_out:
            lines.append(row("OUT", port, first_out[port]))
        if port in first_in:
            lines.append(row("IN", port, first_in[port]))
    lines.extend(["", "## First Frame IRQs", "", "| # | Cycle | PC | Vector | VRAM writes |", "| ---: | ---: | ---: | ---: | ---: |"])
    for irq in irqs[:3]:
        lines.append(f"| {irq['n']} | {irq['cyc']} | {irq['pc']} | {irq['vec']} | {irq['g_vw']} |")
    lines.extend(["", "## Disposition", ""])
    if failures:
        for failure in failures:
            lines.append(f"- FAIL: {failure}")
    else:
        lines.append("- This report is a CI guard for the cosim timing reference, not a gate for HDL prompt readiness.")
        lines.append("- The HDL top-level probe should not expect PPI/FDC activity before the post-banner window shown above.")

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
