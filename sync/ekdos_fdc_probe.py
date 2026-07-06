#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_C = ROOT / "cosim" / "trace.c"
I8080_C = ROOT / "cosim" / "i8080.c"
ROM = ROOT / "roms" / "ekta37.bin"


PORT_RE = re.compile(r"^\s*0x([0-9A-Fa-f]{2})\s*:\s*([0-9]+)(?:\s+last=0x([0-9A-Fa-f]{2}))?")
STOP_RE = re.compile(r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)")


def run_probe(max_cycles, frame_cycles):
    cc = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="ekdos-fdc-probe.") as tmp:
        tmpdir = Path(tmp)
        trace = tmpdir / "trace"
        subprocess.run(
            [
                cc,
                "-O2",
                "-I",
                str(ROOT / "cosim"),
                "-o",
                str(trace),
                str(TRACE_C),
                str(I8080_C),
                str(ROOT / "cosim" / "juk_disk.c"),
                str(ROOT / "cosim" / "juku_fdc.c"),
            ],
            cwd=ROOT,
            check=True,
        )
        env = os.environ.copy()
        env["JUKU_KEYS"] = "TDD"
        proc = subprocess.run(
            [str(trace), str(ROM), str(max_cycles), "0", str(frame_cycles)],
            cwd=ROOT / "cosim",
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    return proc


def parse_ports(stdout):
    section = None
    ports = {"out": {}, "in": {}}
    for line in stdout.splitlines():
        if line.startswith("==== OUT ports"):
            section = "out"
            continue
        if line.startswith("==== IN ports"):
            section = "in"
            continue
        if line.startswith("==== hottest PCs"):
            section = None
            continue
        if section not in ports:
            continue
        match = PORT_RE.match(line)
        if not match:
            continue
        port = int(match.group(1), 16)
        count = int(match.group(2))
        last = int(match.group(3), 16) if match.group(3) is not None else None
        ports[section][port] = {"count": count, "last": last}
    return ports


def parse_stop(stderr):
    for line in reversed(stderr.splitlines()):
        match = STOP_RE.search(line)
        if match:
            pc, cyc, halted, iff, mode, switches = match.groups()
            return {
                "pc": int(pc, 16),
                "cycles": int(cyc),
                "halted": int(halted),
                "iff": int(iff),
                "mode": int(mode),
                "switches": int(switches),
            }
    return {}


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value is not None else "-" for value in values) + " |"


def build_report(proc, max_cycles, frame_cycles):
    ports = parse_ports(proc.stdout)
    stop = parse_stop(proc.stderr)
    failures = []

    if proc.returncode != 0:
        failures.append(f"trace exited with status {proc.returncode}")
    if ports["out"].get(0x1C, {}).get("count", 0) == 0:
        failures.append("ROMBIOS did not write the WD1793 command/status register at port 0x1C")
    if ports["in"].get(0x1C, {}).get("count", 0) < 1000:
        failures.append("ROMBIOS did not enter the expected WD1793 status polling loop")
    if ports["in"].get(0x1F, {}).get("count", 0) != 512:
        failures.append("ROMBIOS did not perform the expected 512-byte first-sector data read")

    reached_fdc = not failures
    status = "READY FOR FDC MODEL" if reached_fdc else "REGRESSION"
    lines = [
        "# EKDOS/FDC boot-path probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe exercises the factory boot sequence mined from Baltijets doc 003:",
        "`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` from `JUKU-1` toward the",
        "`A>` EKDOS prompt. With no `JUKU_DISK` image selected, cosim preserves",
        "the legacy register-echo FDC boundary; success here means the BIOS reaches",
        "the disk path that the `.juk` backend and WD1793 read-sector model now",
        "need to satisfy with a real EKDOS image.",
        "",
        "## Command",
        "",
        "```sh",
        f"JUKU_KEYS=TDD cosim/trace roms/ekta37.bin {max_cycles} 0 {frame_cycles}",
        "```",
        "",
        "## Summary",
        "",
        f"- Trace exit code: {proc.returncode}",
        f"- Stop PC: {stop.get('pc', 0):04X}" if stop else "- Stop PC: not parsed",
        f"- Cycles: {stop.get('cycles', 0)}" if stop else "- Cycles: not parsed",
        f"- Mode switches: {stop.get('switches', 0)}" if stop else "- Mode switches: not parsed",
        f"- WD1793 status/command writes (`0x1C`): {ports['out'].get(0x1C, {}).get('count', 0)}",
        f"- WD1793 status reads (`0x1C`): {ports['in'].get(0x1C, {}).get('count', 0)}",
        f"- WD1793 data reads (`0x1F`): {ports['in'].get(0x1F, {}).get('count', 0)}",
        f"- Probe failures: {len(failures)}",
        "",
        "## FDC I/O Ports",
        "",
        "| Direction | Port | Count | Last write |",
        "| --- | ---: | ---: | --- |",
    ]
    for direction, label in [("out", "OUT"), ("in", "IN")]:
        for port in [0x1C, 0x1D, 0x1E, 0x1F]:
            row = ports[direction].get(port, {"count": 0, "last": None})
            last = f"0x{row['last']:02X}" if row["last"] is not None else "-"
            lines.append(table_row([label, f"0x{port:02X}", row["count"], last]))

    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- The keyboard/frame-interrupt path is sufficient to drive ROMBIOS into the documented disk boot path.",
            "- The first hard stop is now the expected one: supply a real JUKU/EKDOS image and drive the disk-backed WD1793 read-sector path to the factory `A>` prompt.",
            "- The exact target remains the factory acceptance result `A>` after `<T>, <D>, <D>`.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), reached_fdc


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs" / "ekdos-fdc-probe.md")
    max_cycles = int(os.environ.get("EKDOS_PROBE_MAX_CYCLES", "250000000"))
    frame_cycles = int(os.environ.get("EKDOS_PROBE_FRAME_CYCLES", "200000"))
    proc = run_probe(max_cycles, frame_cycles)
    report, ok = build_report(proc, max_cycles, frame_cycles)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(report)
    print(f"Wrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
