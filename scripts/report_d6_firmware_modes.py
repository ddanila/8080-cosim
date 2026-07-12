#!/usr/bin/env python3
"""Trace firmware Port-C writes and distinguish physical D6 modes from emulator banking."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/d6-firmware-mode-coverage.md"
IO_RE = re.compile(r"\[IOSEQ\] OUT port=0x(06|07) value=0x([0-9A-F]{2}) cyc=(\d+) pc=([0-9A-F]{4}) g_vw=(\d+)")


def main() -> int:
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
    physical_modes = {0}
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
        physical = (portc >> 2) & 7
        legacy = portc & 3
        physical_modes.add(physical)
        legacy_modes.add(legacy)
        events.append((int(cyc), pc, int(writes), port, value, before, portc, physical, legacy))

    if len(events) != 24:
        raise SystemExit(f"unexpected early Port-C event count: {len(events)}")
    if physical_modes != {0}:
        raise SystemExit(f"early ROM unexpectedly exercises physical D6 modes {physical_modes}")
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
        "# D6 firmware mode coverage", "", "Status: **PHYSICAL MODES 000/001 OBSERVED / 010-111 UNEXERCISED**", "",
        "This generated report traces authentic ROMBIOS Port-C writes and separates",
        "the physical D6 inputs `PC4..PC2` from the historical emulator's unrelated",
        "two-bit banking convention `PC1..PC0`.", "", "## Reproduction", "",
        "```sh", "python3 scripts/report_d6_firmware_modes.py", "```", "",
        "The generator builds the C trace harness, runs `ekta37` through 32,000 video",
        "writes with `JUKU_TRACE_IO=1`, and replays every PPI0 port `06/07` update.", "",
        "## Early ROM trace", "", f"- Port-C events: `{len(events)}`",
        f"- Physical D6 modes observed (`PC4..PC2`): `{', '.join(f'{mode:03b}' for mode in sorted(physical_modes))}`",
        f"- Legacy emulator modes observed (`PC1..PC0`): `{', '.join(f'{mode:02b}' for mode in sorted(legacy_modes))}`", "",
        "| Cycle | PC | VRAM writes | Port/value | Port C before -> after | Physical D6 | Legacy view |",
        "| ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for cyc, pc, writes, port, value, before, after, physical, legacy in events:
        lines.append(f"| {cyc} | `{pc}` | {writes} | `0x{port}=0x{value:02X}` | `0x{before:02X}->0x{after:02X}` | `{physical:03b}` | `{legacy:02b}` |")
    lines += [
        "", "ROMBIOS toggles `0x00/0x01` sixteen times around its high-ROM transition.",
        "Those writes change PC0 and the emulator view, but they do not change any",
        "physical D6 address input. The structural `juku_top` therefore remains in",
        "physical mode `000` throughout this trace and still boots byte-identically.", "",
        "## Later FDC/EKDOS evidence", "",
        "The guarded long-run/checkpoint reports below all finish with Port C `0x04`,",
        "which sets PC2 and therefore exercises physical D6 mode `001`:", "",
        "| Evidence | Port C | Physical D6 mode |", "| --- | ---: | --- |",
    ]
    for rel, value in later_values.items():
        lines.append(f"| `{rel}` | `0x{value:02X}` | `{(value >> 2) & 7:03b}` |")
    lines += [
        "", "## Coverage boundary", "",
        "- Physical modes `000` and `001` have firmware execution evidence.",
        "- Modes `010` through `111` are truth-table guarded but not observed in the",
        "  current ROM/EKDOS/BASIC paths. Their functions must not be assigned from",
        "  the legacy emulator's `PC1..PC0` mode numbers.",
        "- This trace guards firmware writes, not the unresolved downstream meaning of",
        "  every D6 output word; see `docs/d6-physical-decode.md`.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Status: PHYSICAL MODES 000/001 OBSERVED / 010-111 UNEXERCISED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
