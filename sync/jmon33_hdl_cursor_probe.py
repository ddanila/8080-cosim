#!/usr/bin/env python3
"""Bounded diagnostic for the jmon33 HDL cursor-oracle boundary."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-hdl-cursor-probe.md"
VRAM_TOP = ROOT / "hdl" / "sim" / "vram_top.bin"
ROM_HEX = ROOT / "hdl" / "sim" / "jmon33.hex"
EXPECTED_CURSOR_SHA256 = "f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397"
BLANK_VRAM_SHA256 = "559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d"
VRAM_STRIDE = 40
VRAM_LINES = 241


FIRST_RE = re.compile(r"first video write @0x([0-9A-Fa-f]+) mcyc=([0-9]+)")
COUNT_RE = re.compile(r"\[VRAM\] ([0-9]+) writes \(mcyc=([0-9]+)\) -- dump")
CURSOR_RE = re.compile(r"jmon33 cursor oracle reached \(mcyc=([0-9]+) writes=([0-9]+)\)")
PROGRESS_RE = re.compile(r"\[VRAM\] progress writes=([0-9]+) mcyc=([0-9]+)")
TIMECAP_RE = re.compile(r"time cap mcyc=([0-9]+) vram_writes=([0-9]+)")


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def text_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def write_rom_hex() -> None:
    rom = (ROOT / "roms" / "jmon33.bin").read_bytes()
    ROM_HEX.write_text("\n".join(f"{byte:02x}" for byte in rom) + "\n")


def parse_output(output: str) -> dict[str, int | str | bool]:
    result: dict[str, int | str | bool] = {"cursor_reached": False}
    if match := FIRST_RE.search(output):
        result["first_addr"] = match.group(1).lower()
        result["first_mcyc"] = int(match.group(2))
    if match := COUNT_RE.search(output):
        result["stop_writes"] = int(match.group(1))
        result["stop_mcyc"] = int(match.group(2))
        result["stop_reason"] = "maxvram"
    if match := CURSOR_RE.search(output):
        result["cursor_reached"] = True
        result["stop_mcyc"] = int(match.group(1))
        result["stop_writes"] = int(match.group(2))
        result["stop_reason"] = "cursor"
    progress = tuple(PROGRESS_RE.finditer(output))
    if progress:
        match = progress[-1]
        result["last_progress_writes"] = int(match.group(1))
        result["last_progress_mcyc"] = int(match.group(2))
    if match := TIMECAP_RE.search(output):
        result["stop_mcyc"] = int(match.group(1))
        result["stop_writes"] = int(match.group(2))
        result["stop_reason"] = "timecap"
    return result


def cursor_block_ok(vram: bytes) -> bool:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return False
    for y in range(20, 30):
        if vram[y * VRAM_STRIDE + 1] != 0xFF:
            return False
    return True


def visible_pixels(vram: bytes) -> int:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return 0
    return sum(byte.bit_count() for byte in vram)


def nonzero_bytes(vram: bytes) -> int:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return 0
    return sum(1 for byte in vram if byte != 0x00)


def main() -> int:
    max_vram = int(os.environ.get("JMON33_HDL_CURSOR_MAXVRAM", "300"))
    frame_irq = int(os.environ.get("JMON33_HDL_CURSOR_FRAMEIRQ", "200000"))
    timecap = int(os.environ.get("JMON33_HDL_CURSOR_TIMECAP", "1200000000"))
    trace_progress = int(os.environ.get("JMON33_HDL_CURSOR_TRACEPROGRESS", "0"))
    timeout_s = int(os.environ.get("JMON33_HDL_CURSOR_TIMEOUT", "90"))
    old_vram = VRAM_TOP.read_bytes() if VRAM_TOP.exists() else None

    try:
        with tempfile.TemporaryDirectory(prefix="jmon33-hdl-cursor.") as tmp:
            tmpdir = Path(tmp)
            sim = tmpdir / "juku_top_jmon33"
            write_rom_hex()
            build = run(
                [
                    "iverilog",
                    "-g2012",
                    "-o",
                    str(sim),
                    "hdl/vendor/vm80a.v",
                    "hdl/devices.v",
                    "hdl/juku_top.v",
                    "hdl/sim/juku_top_tb.v",
                ]
            )
            if build.returncode != 0:
                sys.stderr.write(build.stdout)
                sys.stderr.write(build.stderr)
                return build.returncode
            try:
                vvp_cmd = [
                    "vvp",
                    str(sim),
                    "+rom=hdl/sim/jmon33.hex",
                    f"+frameirq={frame_irq}",
                    "+cursorstop=1",
                    f"+maxvram={max_vram}",
                    f"+timecap={timecap}",
                    f"+traceprogress={trace_progress}",
                ]
                if shutil.which("stdbuf"):
                    vvp_cmd = ["stdbuf", "-oL", "-eL", *vvp_cmd]
                proc = run(vvp_cmd, timeout=timeout_s)
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                proc = subprocess.CompletedProcess(
                    exc.cmd,
                    124,
                    text_output(exc.stdout),
                    text_output(exc.stderr),
                )
                timed_out = True

        output = (proc.stdout or "") + (proc.stderr or "")
        parsed = parse_output(output)
        vram = VRAM_TOP.read_bytes() if VRAM_TOP.exists() else b""
    finally:
        if old_vram is None:
            VRAM_TOP.unlink(missing_ok=True)
        else:
            VRAM_TOP.write_bytes(old_vram)

    sha = hashlib.sha256(vram).hexdigest() if vram else ""
    cursor_ok = cursor_block_ok(vram)
    pixels = visible_pixels(vram)
    nonzero = nonzero_bytes(vram)
    cursor_reached = bool(parsed.get("cursor_reached")) and sha == EXPECTED_CURSOR_SHA256 and cursor_ok
    first_ok = parsed.get("first_addr") == "ff40"
    bounded_ok = proc.returncode == 0 and first_ok and sha in {EXPECTED_CURSOR_SHA256, BLANK_VRAM_SHA256}
    status = "JMON33 HDL CURSOR ORACLE REACHED" if cursor_reached else "JMON33 HDL CURSOR ORACLE NOT YET REACHED"

    lines = [
        "# jmon33 HDL cursor-boundary probe",
        "",
        f"Status: **{status}**",
        "",
        "This bounded diagnostic runs Monitor 3.3 on `juku_top` with frame",
        "interrupts enabled and the `+cursorstop=1` testbench hook active. It",
        "records whether the structural HDL reaches the same monitor-idle cursor",
        "oracle that cosim records in `docs/jmon33-ready-probe.md`.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_hdl_cursor_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_HDL_CURSOR_MAXVRAM` default `{max_vram}`",
        f"- `JMON33_HDL_CURSOR_FRAMEIRQ` default `{frame_irq}`",
        f"- `JMON33_HDL_CURSOR_TIMECAP` default `{timecap}`",
        f"- `JMON33_HDL_CURSOR_TRACEPROGRESS` default `{trace_progress}`",
        f"- `JMON33_HDL_CURSOR_TIMEOUT` default `{timeout_s}` seconds",
        "",
        "## Evidence",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| vvp exit code | `{proc.returncode}` |",
        f"| subprocess timeout | {'YES' if timed_out else 'NO'} |",
        f"| first jmon33 video write is `0xFF40` | {'PASS' if first_ok else 'FAIL'} |",
        f"| cursor hook reached | {'PASS' if bool(parsed.get('cursor_reached')) else 'NO'} |",
        f"| framebuffer cursor bytes match cosim | {'PASS' if cursor_ok else 'NO'} |",
        f"| visible framebuffer pixels | `{pixels}` |",
        f"| nonzero framebuffer bytes | `{nonzero}` |",
        f"| framebuffer SHA256 | `{sha or 'missing'}` |",
        f"| cosim cursor SHA256 | `{EXPECTED_CURSOR_SHA256}` |",
        "",
        "## Stop State",
        "",
        f"- Stop reason: `{parsed.get('stop_reason', 'timeout' if timed_out else 'unknown')}`",
        f"- Stop writes: `{parsed.get('stop_writes', 'unknown')}`",
        f"- Stop machine cycle: `{parsed.get('stop_mcyc', 'unknown')}`",
        f"- Last progress writes: `{parsed.get('last_progress_writes', 'unknown')}`",
        f"- Last progress machine cycle: `{parsed.get('last_progress_mcyc', 'unknown')}`",
        f"- First-write machine cycle: `{parsed.get('first_mcyc', 'unknown')}`",
        "",
        "## Disposition",
        "",
    ]
    if cursor_reached:
        lines.append("- `juku_top` reached the cosim monitor-idle cursor boundary in this bounded run.")
    else:
        lines.extend(
            [
                "- The fast HDL jmon33 first-write guard remains the automated passing gate.",
                "- This bounded run documents that the stronger cursor boundary is still open",
                "  for `juku_top`; the next step is reducing the long interrupt/high-memory",
                "  path enough to complete this comparison reproducibly.",
            ]
        )
    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(f"JMON33-HDL-CURSOR-PROBE: {'PASS' if bounded_ok else 'FAIL'}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if bounded_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
