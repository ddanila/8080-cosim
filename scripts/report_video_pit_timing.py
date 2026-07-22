#!/usr/bin/env python3
"""Guard ROM-programmed autonomous Juku PIT raster timing."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "roms" / "ekta37.bin"
BOARD = ROOT / "kicad" / "juku.board.json"
MAME = ROOT / "ref" / "mame_juku.cpp"
DEVICES = ROOT / "hdl" / "devices.v"
TOP = ROOT / "hdl" / "juku_top.v"
TB = ROOT / "hdl" / "sim" / "video_pit_timing_tb.v"
REPORT = ROOT / "docs" / "video-pit-timing.md"

EXPECTED_WRITES = [
    (0x13, 0x15), (0x13, 0x53), (0x13, 0x93),
    (0x17, 0x73), (0x17, 0x93), (0x17, 0x34),
    (0x14, 0x39), (0x14, 0x01),
    (0x10, 0x64), (0x11, 0x24), (0x12, 0x08),
    (0x15, 0x72), (0x15, 0x00), (0x16, 0x25),
]


def nodes(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(item) for item in board["nets"][name]["nodes"]}


def mame_constant(text: str, name: str, known: dict[str, int]) -> int:
    match = re.search(rf"static constexpr int {name} = ([^;]+);", text)
    if not match:
        raise ValueError(f"missing MAME constant {name}")
    value = int(eval(match.group(1), {"__builtins__": {}}, known))
    known[name] = value
    return value


def main() -> int:
    rom = ROM.read_bytes()
    writes: list[tuple[int, int]] = []
    for offset in range(0x01D4, 0x0223):
        if rom[offset] == 0x3E and rom[offset + 2] == 0xD3:
            port, value = rom[offset + 3], rom[offset + 1]
            if 0x10 <= port <= 0x17:
                writes.append((port, value))

    board = json.loads(BOARD.read_text(encoding="utf-8"))
    devices = DEVICES.read_text(encoding="utf-8")
    top = TOP.read_text(encoding="utf-8")
    mame = MAME.read_text(encoding="utf-8")
    known: dict[str, int] = {}
    width = mame_constant(mame, "DEFAULT_WIDTH", known)
    height = mame_constant(mame, "DEFAULT_HEIGHT", known)
    hfront = mame_constant(mame, "HORIZ_FRONT_PORCH", known)
    hback = mame_constant(mame, "HORIZ_BACK_PORCH", known)
    hperiod = mame_constant(mame, "HORIZ_PERIOD", known)
    vfront = mame_constant(mame, "VERT_FRONT_PORCH", known)
    vback = mame_constant(mame, "VERT_BACK_PORCH", known)
    vperiod = mame_constant(mame, "VERT_PERIOD", known)

    with tempfile.TemporaryDirectory(prefix="juku-video-pit-") as tmp_name:
        sim = Path(tmp_name) / "video_pit_timing"
        subprocess.run(
            [
                "iverilog", "-g2012", "-s", "video_pit_timing_tb", "-o", str(sim),
                "hdl/vendor/vm80a.v", "hdl/devices.v", "hdl/juku_top.v",
                "hdl/sim/video_pit_timing_tb.v",
            ],
            cwd=ROOT,
            check=True,
        )
        run = subprocess.run(
            ["vvp", str(sim)], cwd=ROOT, check=True, text=True, capture_output=True
        )

    pass_line = next(
        (line for line in run.stdout.splitlines() if line.startswith("VIDEO-PIT-TIMING: PASS")),
        "missing",
    )
    board_chain_ok = (
        nodes(board, "PIT_HCHAIN")
        == {("D54", "10"), ("D54", "14"), ("D54", "16"), ("D55", "9")}
        and nodes(board, "PIT_HSYNC_DSL") == {("D54", "17"), ("D56", "10")}
        and nodes(board, "PIT_VCHAIN") == {("D55", "10"), ("D55", "14"), ("D55", "16")}
        and nodes(board, "VERT_SYNC") == {("D55", "17"), ("D56", "2")}
        and nodes(board, "D56_Q2N_TAG16") == {("D56", "12"), ("D55", "15"), ("D55", "18")}
        and nodes(board, "HOR_RTR") == {("D54", "13")}
        and nodes(board, "VERT_RTR") == {("D55", "13"), ("D35", "9")}
    )
    mame_ok = (
        (width, height, hfront, hback, hperiod, vfront, vback, vperiod)
        == (320, 241, 64, 128, 512, 25, 47, 313)
    )
    checks = [
        (
            "Exact ekta37 PIT write sequence remains present",
            writes == EXPECTED_WRITES,
            "ROM offsets 0x01D4..0x0222, filtered to ports 0x10..0x17",
        ),
        (
            "8253 model implements the video-used BCD and modes 1/2",
            all(
                marker in devices
                for marker in (
                    "normalized_count", "3'd1: if (running[0])",
                    "3'd2: if (!gate0)", "RL=00",
                )
            ),
            "BCD reload conversion, hardware one-shot, rate generator, latch-command preservation",
        ),
        (
            "Autonomous top-level PIT/one-shot timing passes",
            pass_line != "missing",
            pass_line,
        ),
        (
            "Physical PIT/D56 cascade endpoints remain exact",
            board_chain_ok,
            "board JSON D54/D55/D56 plus HOR_RTR/VER_RTR endpoint sets",
        ),
        (
            "Independent MAME raster geometry agrees with the ROM divisors",
            mame_ok,
            "512x313 total, 320x241 active, H porches 64/128 px, V porches 25/47 lines",
        ),
        (
            "Unresolved slot and D34 signal boundaries remain explicit",
            "assign probe_slot_schedule_known = 1'b0" in top
            and "probe_d34_sig" not in top.lower(),
            "no framebuffer-slot or D34_SIG promotion",
        ),
    ]
    ok = all(result for _, result, _ in checks)

    lines = [
        "# ROM-programmed Juku video timing",
        "",
        "Status: **AUTONOMOUS PIT RASTER TIMING GUARDED / DRAM SLOT + D34_SIG OPEN**."
        if ok else "Status: **VIDEO PIT TIMING CHECK FAILED**.",
        "",
        "This generated report executes the exact `ekta37` D54/D55 programming",
        "bytes through the PIT bus pins of `juku_top`, with its 16 MHz input running",
        "the source-proved D40 1 MHz divider. It measures the autonomous D54 -> D55",
        "-> D56 -> D34_SYNC chain; no synthetic frame tick or forced sync net is used.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_video_pit_timing.py",
        "```",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, result, evidence in checks:
        lines.append(f"| {name} | {'PASS' if result else 'FAIL'} | {evidence} |")
    lines.extend([
        "",
        "## Recovered programmed contract",
        "",
        "| Stage | Control/count | Meaning |",
        "| --- | --- | --- |",
        "| D54 counter 0 | mode 2, BCD `0x64` | 64 one-microsecond byte clocks per line |",
        "| D54 counter 1 | mode 1, BCD `0x24` | 24 us horizontal blank interval |",
        "| D54 counter 2 | mode 1, BCD `0x08` | 8 us horizontal front porch |",
        "| D55 counter 0 | mode 2, binary `0x0139` | 313 lines per frame |",
        "| D55 counter 1 | mode 1, BCD `0x0072` | 72-line vertical blank interval |",
        "| D55 counter 2 | mode 1, BCD `0x25` | 25-line vertical front porch |",
        "",
        "The remaining intervals follow without guessed constants: 40 active byte",
        "clocks = 320 pixels, 16 us horizontal back porch, 241 active lines, and a",
        "47-line vertical back porch. With the traced clocks this gives 15.625 kHz",
        "horizontal and `1 MHz / (64 * 313) = 49.920128 Hz` frame rate.",
        "",
        "## Executed result",
        "",
        "```text",
        pass_line,
        "```",
        "",
        "The test also verifies the typical modeled D56 pulse widths (5.04 us and",
        "223 us) and the traced `D34_SYNC = D56.Q2 XOR D56.Q_N` truth.",
        "",
        "## Deliberate boundary",
        "",
        "This closes autonomous digital raster timing, not video memory arbitration.",
        "D41/D50/D51/D52/D53 slot control, D34_SIG, fetched framebuffer bytes, the",
        "VT2 stage, and loaded X7 voltage remain separate open boundaries. The",
        "abstract `vid_out` is still only a framebuffer oracle and is not composite.",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(lines[2])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
