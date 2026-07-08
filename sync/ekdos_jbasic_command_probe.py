#!/usr/bin/env python3
"""Probe EKDOS command entry for the disk-side JBASIC lead."""
from __future__ import annotations

import hashlib
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
DEFAULT_DISK = ROOT / "media" / "disks" / "JUKPROG2.CPM"
LIVE_CANDIDATE = ROOT / "ref" / "extracted-software" / "JUKPROG2_JBASIC_live_candidate.COM"
REPORT = ROOT / "docs" / "ekdos-jbasic-command-probe.md"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_SIZE = 40 * 241
KEYS = "TDD|JBASIC\r"
EXPECTED_KEY_POS = len(KEYS)
EXPECTED_FINAL_VRAM_SHA256 = "60dcda06cf3402a1710e07eb38189518d6a3827c8279888bd8f0d927967ba90b"
EXPECTED_FINAL_LIT_PIXELS = 1175
EXPECTED_NONZERO_LINES = 68


STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
PROMPT_MARKER_RE = re.compile(
    r"\[KBD\] prompt wait marker consumed at g_vw=([0-9]+) cyc=([0-9]+) pos=([0-9]+)"
)
PORT_RE = re.compile(r"^\s*0x([0-9A-Fa-f]{2})\s*:\s*([0-9]+)(?:\s+last=0x([0-9A-Fa-f]{2}))?")


def compile_trace(tmpdir: Path) -> Path:
    cc = os.environ.get("CC", "cc")
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
    return trace


def run_probe(max_cycles: int, frame_cycles: int, disk: Path) -> tuple[subprocess.CompletedProcess[str], str, bytes]:
    with tempfile.TemporaryDirectory(prefix="ekdos-jbasic-command.") as tmp_name:
        tmpdir = Path(tmp_name)
        trace = compile_trace(tmpdir)
        checkpoint_prefix = tmpdir / "final"
        env = os.environ.copy()
        env["JUKU_DISK"] = str(disk)
        env["JUKU_KEYS"] = KEYS
        env["JUKU_KEY_HOLD_FRAMES"] = os.environ.get("JBASIC_KEY_HOLD_FRAMES", "6")
        env["JUKU_KEY_GAP_FRAMES"] = os.environ.get("JBASIC_KEY_GAP_FRAMES", "8")
        env["JUKU_CHECKPOINT_PREFIX"] = str(checkpoint_prefix)
        proc = subprocess.run(
            [str(trace), str(ROM), str(max_cycles), "0", str(frame_cycles)],
            cwd=ROOT / "cosim",
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        state_text = checkpoint_prefix.with_suffix(".state").read_text() if checkpoint_prefix.with_suffix(".state").exists() else ""
        ram = checkpoint_prefix.with_suffix(".ram").read_bytes() if checkpoint_prefix.with_suffix(".ram").exists() else b""
    return proc, state_text, ram


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


def parse_prompt_marker(stderr: str) -> dict[str, int]:
    match = PROMPT_MARKER_RE.search(stderr)
    if not match:
        return {}
    writes, cycles, pos = match.groups()
    return {"vram_writes": int(writes), "cycles": int(cycles), "pos": int(pos)}


def parse_state(state_text: str) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in state_text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            state[key] = value
    return state


def parse_ports(stdout: str) -> dict[str, dict[int, dict[str, int | None]]]:
    section: str | None = None
    ports: dict[str, dict[int, dict[str, int | None]]] = {"out": {}, "in": {}}
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
        ports[section][port] = {
            "count": int(match.group(2)),
            "last": int(match.group(3), 16) if match.group(3) is not None else None,
        }
    return ports


def vram_summary() -> dict[str, int | str]:
    try:
        data = VRAM.read_bytes()
    except FileNotFoundError:
        return {
            "bytes": 0,
            "sha256": "missing",
            "lit_pixels": 0,
            "nonzero_lines": 0,
            "first_nonzero_line": -1,
            "last_nonzero_line": -1,
            "top_bytes": "missing",
        }
    nonzero_lines = [
        y
        for y in range(len(data) // 40)
        if any(data[y * 40 : (y + 1) * 40])
    ]
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "lit_pixels": sum(byte.bit_count() for byte in data) if len(data) == VRAM_SIZE else 0,
        "nonzero_lines": len(nonzero_lines),
        "first_nonzero_line": nonzero_lines[0] if nonzero_lines else -1,
        "last_nonzero_line": nonzero_lines[-1] if nonzero_lines else -1,
        "top_bytes": data[:16].hex(" ") if data else "missing",
    }


def live_candidate_summary(ram: bytes) -> dict[str, int | str | bool]:
    try:
        candidate = LIVE_CANDIDATE.read_bytes()
    except FileNotFoundError:
        return {
            "candidate_sha256": "missing",
            "entry_prefix": 0,
            "match_count": 0,
            "basic_ram": -1,
            "ready_ram": -1,
            "error_ram": -1,
        }
    entry_prefix = 0
    for offset, value in enumerate(candidate):
        addr = 0x0100 + offset
        if addr >= len(ram) or ram[addr] != value:
            break
        entry_prefix += 1
    match_count = sum(
        1
        for offset, value in enumerate(candidate)
        if 0x0100 + offset < len(ram) and ram[0x0100 + offset] == value
    )
    return {
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "candidate_size": len(candidate),
        "entry_prefix": entry_prefix,
        "match_count": match_count,
        "basic_ram": ram.find(b"BASIC"),
        "ready_ram": ram.find(b"READY"),
        "error_ram": ram.find(b"ERROR"),
    }


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def build_report(
    proc: subprocess.CompletedProcess[str],
    state_text: str,
    ram: bytes,
    max_cycles: int,
    frame_cycles: int,
    disk: Path,
) -> tuple[str, bool]:
    marker = parse_prompt_marker(proc.stderr)
    stop = parse_stop(proc.stderr)
    state = parse_state(state_text)
    ports = parse_ports(proc.stdout)
    vram = vram_summary()
    live = live_candidate_summary(ram)
    data_reads = int(ports["in"].get(0x1F, {}).get("count", 0) or 0)
    key_pos = int(state.get("kbd_pos", "0"))
    failures: list[str] = []

    if proc.returncode != 0:
        failures.append(f"trace exited with status {proc.returncode}")
    if "loaded JUKU disk image" not in proc.stderr:
        failures.append("JUKPROG2 disk image was not loaded")
    if not marker:
        failures.append("EKDOS prompt wait marker was not consumed")
    if key_pos < EXPECTED_KEY_POS:
        failures.append(f"keyboard script ended at position {key_pos}, expected {EXPECTED_KEY_POS}")
    if data_reads < 19000:
        failures.append(f"FDC data reads after the command were too low: {data_reads}")
    if vram["sha256"] != EXPECTED_FINAL_VRAM_SHA256:
        failures.append(f"final VRAM hash changed: {vram['sha256']}")
    if int(vram.get("lit_pixels", 0)) != EXPECTED_FINAL_LIT_PIXELS:
        failures.append(f"final fixed-framebuffer lit pixel count changed: {vram.get('lit_pixels', 0)}")
    if int(vram.get("nonzero_lines", 0)) != EXPECTED_NONZERO_LINES:
        failures.append(f"final fixed-framebuffer nonzero line count changed: {vram.get('nonzero_lines', 0)}")
    if live["candidate_sha256"] == "missing":
        failures.append("live JBASIC candidate artifact is missing")
    if int(live.get("entry_prefix", 0)) < 6:
        failures.append(f"live JBASIC entry prefix too short: {live.get('entry_prefix', 0)}")
    for label in ["basic_ram", "ready_ram", "error_ram"]:
        if int(live.get(label, -1)) < 0:
            failures.append(f"{label.replace('_', ' ').upper()} string not present in final RAM")

    status = "EKDOS JBASIC COMMAND BOUNDARY PINNED" if not failures else "REGRESSION"
    command_display = r"TDD|JBASIC\r"
    lines = [
        "# EKDOS JBASIC command probe",
        "",
        f"Status: **{status}**",
        "",
        "This generated report drives the factory ROMBIOS boot sequence to EKDOS,",
        "waits for the `A>` prompt bitmap, then types the disk command",
        "`JBASIC` on the vendored programming disk. The keyboard wait marker is",
        "implemented as `|` in `JUKU_KEYS`; it is not a typed key.",
        "",
        "The result is a bounded command-launch diagnostic, not a BASIC prompt",
        "claim. It proves the post-prompt keyboard path is deterministic and that",
        "the command triggers further FDC traffic from a real directory-backed",
        "`JBASIC.COM` candidate.",
        "",
        "## Command",
        "",
        "```sh",
        (
            f"JUKU_DISK={rel(disk)} JUKU_KEYS=$'{command_display}' "
            f"JUKU_KEY_HOLD_FRAMES=6 JUKU_KEY_GAP_FRAMES=8 "
            f"cosim/trace roms/ekta37.bin {max_cycles} 0 {frame_cycles}"
        ),
        "```",
        "",
        "## Summary",
        "",
        f"- Trace exit code: {proc.returncode}",
        f"- Disk image: `{rel(disk)}`",
        f"- Keyboard script: `TDD|JBASIC\\r` ({EXPECTED_KEY_POS} positions including the wait marker)",
        (
            f"- Prompt wait marker: consumed at {marker['vram_writes']} VRAM writes, "
            f"{marker['cycles']} cycles, position {marker['pos']}"
            if marker
            else "- Prompt wait marker: not consumed"
        ),
        f"- Final keyboard position/phase: `{state.get('kbd_pos', 'missing')}` / `{state.get('kbd_phase', 'missing')}`",
        f"- Stop PC: `{stop.get('pc', 0):04X}`" if stop else "- Stop PC: not parsed",
        f"- Cycles: {stop.get('cycles', 0)}" if stop else "- Cycles: not parsed",
        f"- Mode switches: {stop.get('switches', 0)}" if stop else "- Mode switches: not parsed",
        f"- WD1793 data reads (`0x1F`): {data_reads}",
        f"- Live JBASIC candidate: `{rel(LIVE_CANDIDATE)}`",
        f"- Live JBASIC candidate SHA256: `{live['candidate_sha256']}`",
        f"- Live JBASIC entry prefix at RAM `0x0100`: {live.get('entry_prefix', 0)} bytes",
        f"- Live JBASIC byte matches at RAM `0x0100`: {live.get('match_count', 0)} / {live.get('candidate_size', 0)}",
        f"- Final RAM `ERROR` string: `0x{int(live.get('error_ram', -1)):04X}`",
        f"- Final RAM `READY` string: `0x{int(live.get('ready_ram', -1)):04X}`",
        f"- Final RAM `BASIC` string: `0x{int(live.get('basic_ram', -1)):04X}`",
        f"- Final VRAM SHA256: `{vram['sha256']}`",
        f"- Final lit pixels: {vram['lit_pixels']}",
        f"- Final fixed-framebuffer nonzero lines: {vram.get('nonzero_lines', 0)} (`{vram.get('first_nonzero_line', -1)}`..`{vram.get('last_nonzero_line', -1)}`)",
        f"- Final fixed-framebuffer first bytes: `{vram.get('top_bytes', 'missing')}`",
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
            "- `JUKPROG2.CPM` is used because `docs/basic-disk-extraction.md` now preserves the raw live-load `JBASIC.COM` candidate from that disk.",
            "- The `JUKU1.CPM` `JBASIC.COM` directory entry still matters as catalog evidence, but the current extractor maps it to erased bytes; it is not used for this launch probe.",
            "- The final RAM contains the live candidate entry signature plus relocated `ERROR`, `READY`, and `BASIC` strings, proving the command reaches loaded BASIC code/data.",
            "- The deeper fixed-`0xD800` framebuffer boundary remains a sparse non-text bitmap, not a user-visible BASIC `READY` oracle.",
            "- Next work is a BASIC prompt oracle: decode the post-command screen/text state or identify the exact EKDOS loader/TPA handoff needed by this `JBASIC.COM`.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT
    max_cycles = int(os.environ.get("JBASIC_COMMAND_MAX_CYCLES", "900000000"))
    frame_cycles = int(os.environ.get("JBASIC_COMMAND_FRAME_CYCLES", "200000"))
    disk = Path(os.environ.get("JBASIC_COMMAND_DISK", DEFAULT_DISK)).expanduser()
    proc, state_text, ram = run_probe(max_cycles, frame_cycles, disk)
    report, ok = build_report(proc, state_text, ram, max_cycles, frame_cycles, disk)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(report)
    print(f"Wrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
