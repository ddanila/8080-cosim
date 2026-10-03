#!/usr/bin/env python3
"""Guard jmon33's stable monitor-idle framebuffer state in cosim."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-ready-probe.md"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_STRIDE = 40
VRAM_LINES = 241
EXPECTED_VRAM_SHA256 = "f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397"
CURSOR_X = 8
CURSOR_Y = 20
CURSOR_W = 8
CURSOR_H = 10


STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
PAGE_RE = re.compile(r"^\s+0x([0-9A-Fa-f]{2})00\s+:\s+([0-9]+)")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, check=False, **kwargs)


def parse_stop(stderr: str) -> dict[str, int]:
    for line in reversed(stderr.splitlines()):
        match = STOP_RE.search(line)
        if match:
            pc, cycles, halted, iff, mode, switches = match.groups()
            return {
                "pc": int(pc, 16),
                "cycles": int(cycles),
                "halted": int(halted),
                "iff": int(iff),
                "mode": int(mode),
                "switches": int(switches),
            }
    return {}


def parse_write_pages(stdout: str) -> dict[int, int]:
    pages: dict[int, int] = {}
    in_density = False
    for line in stdout.splitlines():
        if line.startswith("==== RAM write density"):
            in_density = True
            continue
        if not in_density:
            continue
        match = PAGE_RE.match(line)
        if match:
            pages[int(match.group(1), 16)] = int(match.group(2))
    return pages


def vram_pixel(vram: bytes, x: int, y: int) -> int:
    byte = vram[y * VRAM_STRIDE + (x // 8)]
    return (byte >> (7 - (x % 8))) & 1


def cursor_block_ok(vram: bytes) -> bool:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return False
    for y in range(CURSOR_Y, CURSOR_Y + CURSOR_H):
        for x in range(CURSOR_X, CURSOR_X + CURSOR_W):
            if vram_pixel(vram, x, y) != 1:
                return False
    return True


def main() -> int:
    max_cycles = int(os.environ.get("JMON33_READY_MAX_CYCLES", "20000000"))
    frame_cycles = int(os.environ.get("JMON33_READY_FRAME_CYCLES", "200000"))
    cc = os.environ.get("CC", "cc")
    old_vram = VRAM.read_bytes() if VRAM.exists() else None

    with tempfile.TemporaryDirectory(prefix="jmon33-ready.") as tmp:
        tmpdir = Path(tmp)
        trace = tmpdir / "trace"
        build = run(
            [
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
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
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

    vram = VRAM.read_bytes() if VRAM.exists() else b""
    if old_vram is None:
        VRAM.unlink(missing_ok=True)
    else:
        VRAM.write_bytes(old_vram)
    actual_sha256 = hashlib.sha256(vram).hexdigest() if vram else ""
    stop = parse_stop(proc.stderr)
    pages = parse_write_pages(proc.stdout)
    checks = {
        "trace_exit": proc.returncode == 0,
        "rom_loaded": "loaded 16384 bytes of ROM" in proc.stderr,
        "pic_programmed": "[OUT] first write port 0x00 = 0x56" in proc.stderr
        and "[OUT] first write port 0x01 = 0xFF" in proc.stderr,
        "frame_irq_taken": "[IRQ] frame #1" in proc.stderr and "vec=FF54" in proc.stderr,
        "keyboard_scan": "[IN ] first read  port 0x04" in proc.stderr
        and "[IN ] first read  port 0x05" in proc.stderr,
        "vram_size": len(vram) == VRAM_STRIDE * VRAM_LINES,
        "vram_hash": actual_sha256 == EXPECTED_VRAM_SHA256,
        "cursor_block": cursor_block_ok(vram),
        "monitor_pages": pages.get(0xD6, 0) > 0 and pages.get(0xD7, 0) > 0,
        "visible_pages": pages.get(0xDB, 0) > 0 and pages.get(0xDC, 0) > 0,
    }
    passed = all(checks.values())
    status = "JMON33 MONITOR-IDLE ORACLE READY" if passed else "JMON33 MONITOR-IDLE ORACLE NOT READY"


    def result(name: str) -> str:
        return "PASS" if checks[name] else "FAIL"

    lines = [
        "# jmon33 monitor-idle oracle",
        "",
        f"Status: **{status}**",
        "",
        "This probe runs the default Juku Monitor 3.3 ROM under cosim with the",
        "frame interrupt enabled for a fixed cycle budget, then checks the final",
        "framebuffer. It does not stop when idle is first reached or measure settling",
        "time. The visible oracle is a solid 8x10 cursor block at",
        f"`x={CURSOR_X}`, `y={CURSOR_Y}` plus the full VRAM SHA256.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_ready_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        "- `JMON33_READY_MAX_CYCLES` default `20000000`",
        "- `JMON33_READY_FRAME_CYCLES` default `200000`",
        "",
        f"This run requested `{max_cycles}` cycles and a `{frame_cycles}`-cycle frame interval.",
        "Overrides can change the sampled cursor phase and fail the fixed VRAM oracle.",
        "",
        "## Evidence",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Trace exits cleanly | {result('trace_exit')} |",
        f"| ROM load reports 16384 bytes (explicit `roms/jmon33.bin` input) | {result('rom_loaded')} |",
        f"| Initial PIC writes are `00h=56h`, `01h=FFh` | {result('pic_programmed')} |",
        f"| First frame IRQ logged; IRQ trace contains vector `FF54h` | {result('frame_irq_taken')} |",
        f"| Keyboard ports `04h` and `05h` each read | {result('keyboard_scan')} |",
        f"| VRAM dump is `{VRAM_STRIDE * VRAM_LINES}` bytes | {result('vram_size')} |",
        f"| VRAM SHA256 equals `{EXPECTED_VRAM_SHA256}` | {result('vram_hash')} |",
        f"| Solid cursor block at `x={CURSOR_X}`, `y={CURSOR_Y}` | {result('cursor_block')} |",
        f"| Monitor work pages `0xD600`/`0xD700` written | {result('monitor_pages')} |",
        f"| Visible pages `0xDB00`/`0xDC00` written | {result('visible_pages')} |",
        "",
        "## Summary",
        "",
        f"- Stop PC: `0x{stop.get('pc', 0):04X}`" if stop else "- Stop PC: not parsed",
        f"- Cycles: `{stop.get('cycles', 0)}`" if stop else "- Cycles: not parsed",
        f"- Mode: `{stop.get('mode', 0)}`" if stop else "- Mode: not parsed",
        f"- Mode switches: `{stop.get('switches', 0)}`" if stop else "- Mode switches: not parsed",
        f"- Actual VRAM SHA256: `{actual_sha256 or 'missing'}`",
        f"- Write pages: `{', '.join(f'0x{page:02X}00={count}' for page, count in sorted(pages.items()))}`",
        "",
        "## Remaining Boundary",
        "",
        "- This is the reproducible cosim monitor-idle oracle. The typed jmon33",
        "  command surface is guarded separately by `sync/jmon33_command_probe.py`.",
        "- [HDL cursor probe](jmon33-hdl-cursor-probe.md) records the structural",
        "  comparison status. Cartridge BASIC has a separate",
        "  [artifact/procedure boundary](cartridge-basic-boundary.md).",
        "",
    ]
    REPORT.write_text("\n".join(lines))
    print(f"JMON33-READY-PROBE: {'PASS' if passed else 'FAIL'}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
