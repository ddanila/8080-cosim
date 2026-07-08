#!/usr/bin/env python3
"""Probe jmon33 user-visible command response in cosim."""
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
REPORT = ROOT / "docs" / "jmon33-command-probe.md"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_STRIDE = 40
VRAM_LINES = 241


@dataclass(frozen=True)
class CommandCase:
    name: str
    keys: str | None
    expected_sha256: str
    expected_blocks: tuple[tuple[int, int], ...]


CASES = (
    CommandCase(
        "A-enter",
        "A\n",
        "efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f",
        ((8, 60),),
    ),
    CommandCase(
        "T-enter",
        "T\n",
        "348a571e28b5021fc28ca0a83d19e87100d28a9e32910333814eb71a8573b911",
        ((200, 20), (152, 40)),
    ),
    CommandCase(
        "B-enter",
        "B\n",
        "7de5d7ccbcbe39fc6f644adbeb68b1d38706be9d77616772b3d10686e005d52e",
        ((0, 80),),
    ),
)

STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
IN05_RE = re.compile(r"\[IOSEQ\] IN\s+port=0x05 value=0x([0-9A-Fa-f]{2})")


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


def run_case(trace: Path, case: CommandCase, tmp: Path) -> dict[str, object]:
    old_vram = tmp / "old-vram.bin"
    had_vram = VRAM.exists()
    if had_vram:
        shutil.copyfile(VRAM, old_vram)

    env = os.environ.copy()
    env["JUKU_KEYBOARD_ENABLE"] = "1"
    env["JUKU_KEY_START_VRAM"] = "0"
    env["JUKU_KEY_HOLD_FRAMES"] = os.environ.get("JMON33_COMMAND_HOLD_FRAMES", "20")
    env["JUKU_KEY_GAP_FRAMES"] = os.environ.get("JMON33_COMMAND_GAP_FRAMES", "6")
    if case.keys is not None:
        env["JUKU_KEYS"] = case.keys
    if os.environ.get("JMON33_COMMAND_TRACE_IO", "1") != "0":
        env["JUKU_TRACE_IO"] = "1"

    proc = subprocess.run(
        [
            str(trace),
            "../roms/jmon33.bin",
            os.environ.get("JMON33_COMMAND_MAX_CYCLES", "60000000"),
            "0",
            os.environ.get("JMON33_COMMAND_FRAME_CYCLES", "200000"),
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

    sha = hashlib.sha256(vram).hexdigest() if vram else ""
    in05_values = tuple(int(match.group(1), 16) for match in IN05_RE.finditer(proc.stderr))
    active_values = tuple(sorted(set(value for value in in05_values if value != 0xCF)))
    blocks = block_summary(vram)
    expected_blocks_ok = all(solid_block(vram, x, y) for x, y in case.expected_blocks)
    return {
        "case": case,
        "proc": proc,
        "sha": sha,
        "stop": parse_stop(proc.stderr),
        "in05_count": len(in05_values),
        "active_values": active_values[:8],
        "blocks": blocks,
        "expected_blocks_ok": expected_blocks_ok,
        "visible_pixels": sum(byte.bit_count() for byte in vram),
        "nonzero_bytes": sum(1 for byte in vram if byte),
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jmon33-command.") as tmp_name:
        tmp = Path(tmp_name)
        trace = compile_trace(tmp)
        results = [run_case(trace, case, tmp) for case in CASES]

    passed = all(
        result["proc"].returncode == 0
        and result["sha"] == result["case"].expected_sha256
        and result["expected_blocks_ok"]
        for result in results
    )
    status = "JMON33 COMMAND SURFACE READY" if passed else "JMON33 COMMAND SURFACE CHANGED"

    lines = [
        "# jmon33 command-surface probe",
        "",
        f"Status: **{status}**",
        "",
        "This cosim guard exercises Monitor 3.3 with frame interrupts and keyboard",
        "stimulus long enough for the jmon33 scan loop. It proves typed",
        "command/return paths produce deterministic visible screen states, which",
        "is a stronger user-visible command-surface boundary than the plain idle",
        "cursor oracle in `docs/jmon33-ready-probe.md`.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_command_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_COMMAND_MAX_CYCLES` default `{os.environ.get('JMON33_COMMAND_MAX_CYCLES', '60000000')}`",
        f"- `JMON33_COMMAND_FRAME_CYCLES` default `{os.environ.get('JMON33_COMMAND_FRAME_CYCLES', '200000')}`",
        f"- `JMON33_COMMAND_HOLD_FRAMES` default `{os.environ.get('JMON33_COMMAND_HOLD_FRAMES', '20')}`",
        f"- `JMON33_COMMAND_GAP_FRAMES` default `{os.environ.get('JMON33_COMMAND_GAP_FRAMES', '6')}`",
        "",
        "## Evidence",
        "",
        "| Case | Keys | Exit | Stop PC | Cycles | Port `0x05` samples | Active key values | Visible blocks | Pixels | VRAM SHA256 | Result |",
        "| --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for result in results:
        case = result["case"]
        stop = result["stop"]
        active = ", ".join(f"`0x{value:02X}`" for value in result["active_values"]) or "-"
        blocks = ", ".join(f"`x={x},y={y}`" for x, y in result["blocks"]) or "-"
        ok = (
            result["proc"].returncode == 0
            and result["sha"] == case.expected_sha256
            and result["expected_blocks_ok"]
        )
        lines.append(
            f"| {case.name} | `{case.keys.encode('unicode_escape').decode() if case.keys is not None else '<none>'}` | "
            f"`{result['proc'].returncode}` | `0x{stop.get('pc', 0):04X}` | "
            f"`{stop.get('cycles', 0)}` | `{result['in05_count']}` | {active} | "
            f"{blocks} | `{result['visible_pixels']}` | `{result['sha'] or 'missing'}` | "
            f"{'PASS' if ok else 'FAIL'} |"
        )

    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- `JUKU_KEY_START_VRAM`, `JUKU_KEY_HOLD_FRAMES`, and",
            "  `JUKU_KEY_GAP_FRAMES` make the cosim keyboard stimulus usable for",
            "  both ekta37's long banner path and jmon33's short cursor path.",
            "- This proves jmon33 is accepting keyboard input and moving its visible",
            "  command cursor deterministically. It does not prove the BASIC prompt;",
            "  the BASIC pairing remains tracked by `docs/basic-launch-probe.md` and",
            "  `docs/basic-factory-command-probe.md`.",
        ]
    )
    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(f"JMON33-COMMAND-PROBE: {'PASS' if passed else 'FAIL'}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
