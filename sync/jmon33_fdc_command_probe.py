#!/usr/bin/env python3
"""Pin Monitor 3.3 T-command behavior with and without a disk-backed FDC."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get("JMON33_FDC_COMMAND_REPORT", ROOT / "docs" / "jmon33-fdc-command-probe.md"))
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_STRIDE = 40
VRAM_LINES = 241

STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
IOSEQ_RE = re.compile(
    r"\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) value=0x([0-9A-Fa-f]{2}) "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4}) g_vw=([0-9]+) count=([0-9]+)"
)


@dataclass(frozen=True)
class Scenario:
    name: str
    disk: Path | None


def compile_trace(tmp: Path) -> Path:
    cc = os.environ.get("CC", "cc")
    trace = tmp / "trace"
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
    return trace


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


def pixel(vram: bytes, x: int, y: int) -> int:
    return (vram[y * VRAM_STRIDE + x // 8] >> (7 - (x % 8))) & 1


def solid_block(vram: bytes, x0: int, y0: int, width: int = 8, height: int = 10) -> bool:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return False
    for y in range(y0, y0 + height):
        for x in range(x0, x0 + width):
            if pixel(vram, x, y) != 1:
                return False
    return True


def block_summary(vram: bytes) -> tuple[tuple[int, int], ...]:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return ()
    blocks: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for y in range(0, VRAM_LINES - 9):
        for bx in range(VRAM_STRIDE):
            x = bx * 8
            if (x, y) in seen:
                continue
            if all(vram[(y + row) * VRAM_STRIDE + bx] == 0xFF for row in range(10)):
                blocks.append((x, y))
                for row in range(10):
                    seen.add((x, y + row))
    return tuple(blocks)


def io_summary(stderr: str) -> dict[str, object]:
    events: list[tuple[str, int, int, int, int, int, int, str]] = []
    for line in stderr.splitlines():
        match = IOSEQ_RE.search(line)
        if not match:
            continue
        direction, port, value, cyc, pc, vram_writes, count = match.groups()
        events.append(
            (
                direction.strip(),
                int(port, 16),
                int(value, 16),
                int(cyc),
                int(pc, 16),
                int(vram_writes),
                int(count),
                line,
            )
        )
    fdc = [event for event in events if 0x1C <= event[1] <= 0x1F]
    data_reads = [event for event in fdc if event[0] == "IN" and event[1] == 0x1F]
    status_reads = [event for event in fdc if event[0] == "IN" and event[1] == 0x1C]
    command_writes = [event for event in fdc if event[0] == "OUT" and event[1] == 0x1C]
    return {
        "events": events,
        "fdc": fdc,
        "data_reads": data_reads,
        "status_reads": status_reads,
        "command_writes": command_writes,
        "first_fdc": fdc[0][7] if fdc else "none",
        "last_fdc": fdc[-1][7] if fdc else "none",
        "commands": tuple(event[2] for event in command_writes[:16]),
    }


def run_scenario(trace: Path, scenario: Scenario, tmp: Path) -> dict[str, object]:
    old_vram = tmp / f"old-{scenario.name}.bin"
    had_vram = VRAM.exists()
    if had_vram:
        shutil.copyfile(VRAM, old_vram)

    env = os.environ.copy()
    env["JUKU_KEYBOARD_ENABLE"] = "1"
    env["JUKU_KEYS"] = "T\n"
    env["JUKU_KEY_START_VRAM"] = os.environ.get("JMON33_FDC_COMMAND_START_VRAM", "210")
    env["JUKU_KEY_HOLD_FRAMES"] = os.environ.get("JMON33_FDC_COMMAND_HOLD_FRAMES", "20")
    env["JUKU_KEY_GAP_FRAMES"] = os.environ.get("JMON33_FDC_COMMAND_GAP_FRAMES", "6")
    env["JUKU_TRACE_IO"] = "1"
    if scenario.disk is not None:
        env["JUKU_DISK"] = str(scenario.disk)
    else:
        env.pop("JUKU_DISK", None)

    proc = subprocess.run(
        [
            str(trace),
            "../roms/jmon33.bin",
            os.environ.get("JMON33_FDC_COMMAND_MAX_CYCLES", "60000000"),
            "0",
            os.environ.get("JMON33_FDC_COMMAND_FRAME_CYCLES", "200000"),
        ],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    vram = VRAM.read_bytes() if VRAM.exists() else b""
    if had_vram:
        shutil.copyfile(old_vram, VRAM)
    elif VRAM.exists():
        VRAM.unlink()

    io = io_summary(proc.stderr)
    return {
        "scenario": scenario,
        "proc": proc,
        "stop": parse_stop(proc.stderr),
        "sha": hashlib.sha256(vram).hexdigest() if vram else "",
        "blocks": block_summary(vram),
        "cursor": solid_block(vram, 8, 20),
        "visible_pixels": sum(byte.bit_count() for byte in vram),
        "nonzero_bytes": sum(1 for byte in vram if byte),
        "io": io,
    }


def fmt_blocks(blocks: tuple[tuple[int, int], ...]) -> str:
    return ", ".join(f"`x={x},y={y}`" for x, y in blocks) or "-"


def fmt_commands(commands: tuple[int, ...]) -> str:
    return ", ".join(f"`0x{command:02X}`" for command in commands) or "-"


def main() -> int:
    scenarios = (
        Scenario("no-disk", None),
        Scenario("JUKU1.CPM", Path(os.environ.get("JMON33_FDC_COMMAND_DISK", DISK))),
    )
    with tempfile.TemporaryDirectory(prefix="jmon33-fdc-command.") as tmp_name:
        tmp = Path(tmp_name)
        trace = compile_trace(tmp)
        results = [run_scenario(trace, scenario, tmp) for scenario in scenarios]

    disk_result = next(result for result in results if result["scenario"].disk is not None)
    status = "JMON33 FDC T-COMMAND ORACLE PINNED"
    if disk_result["proc"].returncode != 0:
        status = "JMON33 FDC T-COMMAND ORACLE FAILED"

    lines = [
        "# jmon33 FDC T-command probe",
        "",
        f"Status: **{status}**",
        "",
        "This cosim diagnostic pins Monitor 3.3's `T` command behavior after the",
        "monitor-idle cursor, both with no disk-backed FDC and with the vendored",
        "`media/disks/JUKU1.CPM` image. It provides a command-level oracle for",
        "the current structural HDL FDC probe; keyboard sampling works, while",
        "the resumed `T` path enters heavy FDC I/O.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_fdc_command_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_FDC_COMMAND_MAX_CYCLES` default `{os.environ.get('JMON33_FDC_COMMAND_MAX_CYCLES', '60000000')}`",
        f"- `JMON33_FDC_COMMAND_FRAME_CYCLES` default `{os.environ.get('JMON33_FDC_COMMAND_FRAME_CYCLES', '200000')}`",
        f"- `JMON33_FDC_COMMAND_START_VRAM` default `{os.environ.get('JMON33_FDC_COMMAND_START_VRAM', '210')}`",
        f"- `JMON33_FDC_COMMAND_HOLD_FRAMES` default `{os.environ.get('JMON33_FDC_COMMAND_HOLD_FRAMES', '20')}`",
        f"- `JMON33_FDC_COMMAND_GAP_FRAMES` default `{os.environ.get('JMON33_FDC_COMMAND_GAP_FRAMES', '6')}`",
        f"- `JMON33_FDC_COMMAND_DISK` default `{Path(os.environ.get('JMON33_FDC_COMMAND_DISK', DISK)).relative_to(ROOT)}`",
        "",
        "## Evidence",
        "",
        "| Scenario | Disk | Exit | Stop PC | Cycles | FDC events | FDC data reads | FDC status reads | FDC command writes | First commands | Cursor | Visible blocks | Pixels | VRAM SHA256 |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | --- |",
    ]
    for result in results:
        scenario = result["scenario"]
        stop = result["stop"]
        io = result["io"]
        disk = scenario.disk.relative_to(ROOT).as_posix() if scenario.disk else "none"
        lines.append(
            f"| {scenario.name} | `{disk}` | `{result['proc'].returncode}` | "
            f"`0x{stop.get('pc', 0):04X}` | `{stop.get('cycles', 0)}` | "
            f"`{len(io['fdc'])}` | `{len(io['data_reads'])}` | "
            f"`{len(io['status_reads'])}` | `{len(io['command_writes'])}` | "
            f"{fmt_commands(io['commands'])} | `{'yes' if result['cursor'] else 'no'}` | "
            f"{fmt_blocks(result['blocks'])} | `{result['visible_pixels']}` | `{result['sha'] or 'missing'}` |"
        )
    lines.extend(["", "## FDC Trace Anchors", ""])
    for result in results:
        scenario = result["scenario"]
        io = result["io"]
        lines.extend(
            [
                f"### {scenario.name}",
                "",
                f"- First FDC line: `{io['first_fdc']}`",
                f"- Last FDC line: `{io['last_fdc']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Disposition",
            "",
            "- The no-disk row is the closest cosim comparison for a monitor command",
            "  oracle generated without `JUKU_DISK`.",
            "- The `JUKU1.CPM` row is the disk-backed oracle to compare against HDL",
            "  runs where the structural FDC is visible and serviced.",
            "- With the read-only raw-image backend, command `0xFD` is treated as a",
            "  Type-III write-track command and completes with status `0x40` WRITE",
            "  PROTECT rather than staying BUSY forever. Monitor 3.3 keeps polling",
            "  that status in this bounded run, so the disk-backed row is a stable",
            "  write-protect oracle, not a successful disk operation.",
            "- This is still a command-level oracle, not a full EKDOS boot proof;",
            "  full ROMBIOS `TDD` boot remains tracked by the EKDOS/FDC probes.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if status.endswith("PINNED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
