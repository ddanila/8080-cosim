#!/usr/bin/env python3
"""Full cosim I/O sequence reference for the ROMBIOS TDD -> FDC window."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ekdos-ioseq-reference.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"

IOSEQ_RE = re.compile(
    r"^\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) value=0x([0-9A-Fa-f]{2}) "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4}) g_vw=([0-9]+) count=([0-9]+)"
)


def run_trace() -> subprocess.CompletedProcess[str]:
    cc = os.environ.get("CC", "cc")
    max_cycles = os.environ.get("EKDOS_IOSEQ_MAX_CYCLES", "7000000")
    frame_cycles = os.environ.get("EKDOS_IOSEQ_FRAME_CYCLES", "200000")
    with tempfile.TemporaryDirectory(prefix="ekdos-ioseq.") as tmp:
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
        env["JUKU_TRACE_IO"] = "1"
        return subprocess.run(
            [str(trace), str(ROM), max_cycles, "0", frame_cycles],
            cwd=ROOT / "cosim",
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


def parse(log: str) -> list[dict[str, str | int]]:
    events: list[dict[str, str | int]] = []
    for line in log.splitlines():
        match = IOSEQ_RE.match(line)
        if not match:
            continue
        direction, port, value, cyc, pc, g_vw, count = match.groups()
        events.append(
            {
                "dir": direction.strip(),
                "port": int(port, 16),
                "value": int(value, 16),
                "cyc": int(cyc),
                "pc": pc.upper(),
                "g_vw": int(g_vw),
                "count": int(count),
            }
        )
    return events


def find_event(events: list[dict[str, str | int]], direction: str, port: int, value: int | None = None):
    for event in events:
        if event["dir"] != direction or event["port"] != port:
            continue
        if value is not None and event["value"] != value:
            continue
        return event
    return None


def row(label: str, event) -> str:
    if not event:
        return f"| {label} | - | - | - | - | - |"
    return (
        f"| {label} | {event['dir']} 0x{event['port']:02X} | "
        f"0x{event['value']:02X} | {event['cyc']} | {event['pc']} | {event['g_vw']} |"
    )


def main() -> int:
    proc = run_trace()
    log = (proc.stderr or "") + "\n" + (proc.stdout or "")
    events = parse(log)
    first_fdc = find_event(events, "OUT", 0x1C)
    first_pic = find_event(events, "OUT", 0x00, 0xD6)
    pic_icw2 = find_event(events, "OUT", 0x01, 0xFE)
    pic_unmask = find_event(events, "OUT", 0x01, 0xDF)
    first_kbd_read = find_event(events, "IN", 0x05)
    first_t_read = find_event(events, "IN", 0x05, 0x88)
    first_motor_on = find_event(events, "OUT", 0x06, 0x04)

    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"trace exited {proc.returncode}")
    if len(events) < 100:
        failures.append(f"too few IOSEQ events captured: {len(events)}")
    expected = [
        ("PIC ICW1", first_pic, "02B9", 30520, 0xD6),
        ("PIC ICW2", pic_icw2, "02BC", 30520, 0xFE),
        ("PIC unmask", pic_unmask, "02D6", 30524, 0xDF),
        ("first keyboard read", first_kbd_read, "1213", 30520, 0xCF),
        ("shifted T keyboard read", first_t_read, "1463", 42543, 0x88),
        ("FDC motor on", first_motor_on, "D7EF", 63085, 0x04),
        ("first FDC command", first_fdc, "E5DE", 63085, 0x02),
    ]
    for label, event, pc, g_vw, value in expected:
        if event is None:
            failures.append(f"{label} not observed")
            continue
        if event["pc"] != pc or event["g_vw"] != g_vw or event["value"] != value:
            failures.append(
                f"{label} changed: got pc={event['pc']} g_vw={event['g_vw']} "
                f"value=0x{event['value']:02X}; expected pc={pc} g_vw={g_vw} value=0x{value:02X}"
            )

    status = "PASS" if not failures else "REGRESSION"
    lines = [
        "# EKDOS I/O sequence reference",
        "",
        f"Status: **{status}**",
        "",
        "This is the full cosim I/O-sequence reference for the vendored",
        "`media/disks/JUKU1.CPM` factory `TDD` path, captured with",
        "`JUKU_TRACE_IO=1`. It pins the exact ROMBIOS keyboard/PIC/PPI/FDC",
        "events that the `juku_top` direct-bus harness mirrors at the current",
        "post-banner boundary.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/ekdos_ioseq_reference.py",
        "```",
        "",
        "## Evidence",
        "",
        f"- Trace exit code: `{proc.returncode}`",
        f"- Captured I/O events: `{len(events)}`",
        "",
        "| Event | Access | Value | Cycle | PC | VRAM writes |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
        row("PIC ICW1", first_pic),
        row("PIC ICW2", pic_icw2),
        row("PIC unmask IR5", pic_unmask),
        row("First keyboard read", first_kbd_read),
        row("Shifted T keyboard read", first_t_read),
        row("FDC motor on", first_motor_on),
        row("First FDC command", first_fdc),
        "",
        "## Boundary",
        "",
        "- This is a cosim reference, not an HDL prompt proof.",
        "- `docs/juku-top-periph-bus-check.md` proves the corresponding top-level",
        "  keyboard/PIC/PPI/FDC hardware path works when driven directly.",
        "- Uninterrupted HDL CPU execution now reaches decoded FDC I/O and the EKDOS",
        "  prompt; this reference remains the fast event-sequence oracle for regressions.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
