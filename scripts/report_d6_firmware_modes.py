#!/usr/bin/env python3
"""Trace firmware Port-C writes and distinguish physical D6 modes from emulator banking."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/d6-firmware-mode-coverage.md"
BOARD_JSON = ROOT / "kicad/juku.board.json"
D6_RAW = ROOT / "ref/physical-proms/validated/d6_038.raw.bin"
IO_RE = re.compile(r"\[IOSEQ\] OUT port=0x(06|07) value=0x([0-9A-F]{2}) cyc=(\d+) pc=([0-9A-F]{4}) g_vw=(\d+)")


def main() -> int:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    io_cycle_nodes = {
        tuple(map(str, node)) for node in board["nets"]["IO_CYCLE_H"]["nodes"]
    }
    if io_cycle_nodes != {("D6", "15"), ("D105", "1"), ("D7", "8")}:
        raise SystemExit(f"D6 A7 IO_CYCLE_H continuity changed: {sorted(io_cycle_nodes)}")
    d6_raw = D6_RAW.read_bytes()
    a7_high_words = set(d6_raw[0x80:])
    if len(d6_raw) != 256 or a7_high_words != {0xB, 0xF}:
        raise SystemExit(
            f"D6 A7=1 table boundary changed: bytes={len(d6_raw)} "
            f"words={sorted(a7_high_words)}"
        )
    with tempfile.TemporaryDirectory(prefix="d6-firmware-modes.") as tmp_name:
        tmp = Path(tmp_name)
        trace = tmp / "trace"
        subprocess.run([
            os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"), "-o", str(trace),
            str(ROOT / "cosim/trace.c"), str(ROOT / "cosim/i8080.c"),
            str(ROOT / "cosim/juk_disk.c"), str(ROOT / "cosim/juku_fdc.c"),
        ], check=True, cwd=tmp)
        env = os.environ.copy()
        env["JUKU_TRACE_IO"] = "1"
        proc = subprocess.run(
            [str(trace), str(ROOT / "roms/ekta37.bin"), "50000000", "32000"],
            cwd=tmp, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )

    events = []
    portc = 0
    physical_suffixes = {3}
    legacy_modes = {0}
    for match in IO_RE.finditer(proc.stderr):
        port, value_hex, cyc, pc, writes = match.groups()
        value = int(value_hex, 16)
        before = portc
        if port == "06":
            portc = value
        elif value & 0x80:
            portc = 0
        else:
            bit = (value >> 1) & 7
            if value & 1:
                portc |= 1 << bit
            else:
                portc &= ~(1 << bit)
        physical = (~portc) & 3
        legacy = portc & 3
        physical_suffixes.add(physical)
        legacy_modes.add(legacy)
        events.append((int(cyc), pc, int(writes), port, value, before, portc, physical, legacy))

    if len(events) != 24:
        raise SystemExit(f"unexpected early Port-C event count: {len(events)}")
    if physical_suffixes != {2, 3}:
        raise SystemExit(f"early ROM unexpectedly exercises D6 A6/A5 suffixes {physical_suffixes}")
    if legacy_modes != {0, 1}:
        raise SystemExit(f"legacy emulator modes changed: {legacy_modes}")

    later_docs = [
        "docs/juku-top-fdc-alignment.md",
        "docs/juku-top-fdc-verilator-probe.md",
        "docs/juku-top-jbasic-verilator-probe.md",
        "docs/ekdos-jbasic-command-probe.md",
    ]
    later_values = {}
    for rel in later_docs:
        text = (ROOT / rel).read_text()
        match = re.search(r"portc(?:=| latch: `0x)([0-9A-Fa-f]{2})", text)
        if match:
            later_values[rel] = int(match.group(1), 16)
    if not later_values or any(value != 0x04 for value in later_values.values()):
        raise SystemExit(f"later checkpoint Port-C evidence changed: {later_values}")

    lines = [
        "# D6 firmware mode coverage", "", "Status: **A6/A5 11/10 OBSERVED / A7 IO-CYCLE SOURCE CLOSED**", "",
        "This generated report traces authentic ROMBIOS Port-C writes and separates",
        "the measured physical D6 inputs A6=`/PC1`, A5=`/PC0` from the historical",
        "emulator's non-inverted `PC1..PC0` banking convention. Owner continuity",
        "closes D6 A7 through D105.1 to D7.8, the I/O-cycle-active-high NAND of raw",
        "`/IORD` and `/IOWR`.", "", "## Reproduction", "",
        "```sh", "python3 scripts/report_d6_firmware_modes.py", "```", "",
        "The generator builds the C trace harness, runs `ekta37` through 32,000 video",
        "writes with `JUKU_TRACE_IO=1`, and replays every PPI0 port `06/07` update.", "",
        "## Early ROM trace", "", f"- Port-C events: `{len(events)}`",
        f"- Physical D6 A6/A5 suffixes observed (`/PC1,/PC0`): `{', '.join(f'{mode:02b}' for mode in sorted(physical_suffixes))}`",
        f"- Legacy emulator modes observed (`PC1..PC0`): `{', '.join(f'{mode:02b}' for mode in sorted(legacy_modes))}`", "",
        "| Cycle | PC | VRAM writes | Port/value | Port C before -> after | D6 A6/A5 | Legacy view |",
        "| ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for cyc, pc, writes, port, value, before, after, physical, legacy in events:
        lines.append(f"| {cyc} | `{pc}` | {writes} | `0x{port}=0x{value:02X}` | `0x{before:02X}->0x{after:02X}` | `{physical:02b}` | `{legacy:02b}` |")
    lines += [
        "", "ROMBIOS toggles `0x00/0x01` sixteen times around its high-ROM transition.",
        "Those writes change PC0 and therefore toggle physical D6 A5 after the D3",
        "inverter. Port C alone determines only suffix `11` or `10`; A7 is independent.",
        "During memory cycles D7.8 is low, so the runnable table rows are `011` and",
        "`010`. During the OUT event itself A7 is high, but those rows do not select",
        "a firmware memory map.", "",
        "## Later FDC/EKDOS evidence", "",
        "The guarded long-run/checkpoint reports below all finish with Port C `0x04`,",
        "which sets PC2 but leaves PC1/PC0 clear. It therefore retains A6/A5=`11`:", "",
        "| Evidence | Port C | D6 A6/A5 |", "| --- | ---: | --- |",
    ]
    for rel, value in later_values.items():
        lines.append(f"| `{rel}` | `0x{value:02X}` | `{(~value) & 3:02b}` |")
    lines += [
        "", "## Coverage boundary", "",
        "- Physical A6/A5 suffixes `11` and `10` have firmware execution evidence.",
        "- A7 is not a Port-C bit: owner continuity proves D7.8 drives D105.1/D6.15",
        "  high only while raw `/IORD` or `/IOWR` is asserted. Memory-map selection",
        "  therefore uses A7=`0`.",
        "- Every physical A7=`1` row emits only `B` or `F`; both release ROM/RAM",
        "  selects, so the I/O-cycle quadrant cannot express a competing memory map.",
        "- This trace guards firmware writes, not the unresolved downstream meaning of",
        "  every D6 output word; see `docs/d6-physical-decode.md`.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Status: A6/A5 11/10 OBSERVED / A7 IO-CYCLE SOURCE CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
