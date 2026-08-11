#!/usr/bin/env python3
"""Guard the CS00024 video-slot refresh experiment snippets and runner.

Static section (no cosim): the arm snippets must replay the exact EktaSoft
D54/D55 boot programming bytes, exclude every D57 write that could disturb
the live link, and the marker/hold layout must account for all 128 physical
MK4564 rows. PTY section (Linux CI): a short hold under a generous decay
deadline must PASS end to end, and a hold crossing the deadline must produce
the runner's no-return decay classification — the deterministic negative
control proving the experiment can observe missing refresh at all. The flat
cosim model implements no video-slot refresh, so simulation cannot and must
not pass the armed long hold; only the physical boards answer that question.

Run with no arguments for the static section only.
"""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUKURAVI = ROOT / "spinoffs" / "jukuravi"
RUNNER = JUKURAVI / "raster_retention.py"
FIRMWARE = JUKURAVI / "firmware"
sys.path[:0] = [str(FIRMWARE), str(JUKURAVI)]
import build_d0_row_refresh as t36  # noqa: E402
import raster  # noqa: E402
import retention  # noqa: E402

# The exact EktaSoft 3.7 boot PIT sequence, transcribed independently from
# roms/ekta37.bin offsets 01D4h..0221h (port, value, reused-A flag).
EXPECTED_ALL_WRITES = (
    (0x13, 0x15, False),
    (0x13, 0x53, False),
    (0x13, 0x93, False),
    (0x17, 0x73, False),
    (0x17, 0x93, False),
    (0x17, 0x34, False),
    (0x14, 0x39, False),
    (0x14, 0x01, False),
    (0x1B, 0x1F, False),
    (0x1B, 0x76, False),
    (0x1B, 0xB0, False),
    (0x10, 0x64, False),
    (0x18, 0x32, False),
    (0x1A, 0xFF, False),
    (0x1A, 0xFF, True),
    (0x11, 0x24, False),
    (0x12, 0x08, False),
    (0x15, 0x72, False),
    (0x15, 0x00, False),
    (0x16, 0x25, False),
)
EXPECTED_RASTER = tuple(
    (port, value) for port, value, _ in EXPECTED_ALL_WRITES if 0x10 <= port <= 0x17
)
FORBIDDEN_LINK_WRITES = ((0x1B, 0x1F), (0x1B, 0x76), (0x18, 0x32))


def fail(message: str) -> None:
    print(f"JUKURAVI-RASTER-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_static() -> None:
    rom = raster.load_ekta37()
    decoded = tuple(
        (write.port, write.value, write.reused_a)
        for write in raster.decode_pit_writes(rom)
    )
    if decoded != EXPECTED_ALL_WRITES:
        fail("decoded EktaSoft PIT sequence differs from the transcription")

    raster_pairs = tuple(
        (write.port, write.value) for write in raster.raster_writes(rom)
    )
    if raster_pairs != EXPECTED_RASTER or len(raster_pairs) != 14:
        fail("raster subset differs from the 14 exact D54/D55 writes")

    syncb = tuple(
        (write.port, write.value, write.reused_a)
        for write in raster.syncb_writes(rom)
    )
    if syncb != ((0x1B, 0xB0, False), (0x1A, 0xFF, False), (0x1A, 0xFF, True)):
        fail("SYNC_B subset is not exactly EktaSoft's channel-2 write")

    for variant in raster.ARM_VARIANTS:
        snippet = raster.build_arm_snippet(variant, rom)
        if snippet[-3:] != bytes((0x3E, raster.ARM_RETURN_A, 0xC9)):
            fail(f"{variant} arm snippet does not end in MVI A/RET")
        ports = set(snippet[index + 1] for index in range(len(snippet) - 3) if snippet[index] == 0xD3)
        for port, value in FORBIDDEN_LINK_WRITES:
            if port in ports and variant == "raster":
                fail("raster arm snippet touches a D57 port")
        body = snippet[:-3].hex()
        for port, value in FORBIDDEN_LINK_WRITES:
            if f"3e{value:02x}d3{port:02x}" in body:
                fail(f"arm snippet replays forbidden link write {value:02X}->{port:02X}")
    if "3eb0d31b3effd31ad31a" not in raster.build_arm_snippet("raster-syncb", rom).hex():
        fail("SYNC_B arm snippet lost EktaSoft's exact bare-OUT reuse shape")

    if raster.MARKER[:32] != retention.MARKER:
        fail("marker first half is not retention.py's proven pattern")
    if raster.MARKER[32:] != bytes(value ^ 0xFF for value in retention.MARKER):
        fail("marker second half is not the bitwise complement")

    outer = raster.outer_for_seconds(25.0, raster.DEFAULT_EFFECTIVE_MHZ)
    if outer != 27:
        fail(f"25 s at 1.702 MHz sized outer={outer}, expected 27")
    estimated = raster.hold_seconds(outer, raster.DEFAULT_EFFECTIVE_MHZ)
    if not 24.0 < estimated < 26.0:
        fail(f"outer=27 estimate {estimated} is outside 24..26 s")

    image = raster.build_hold_image(outer)
    if len(image) != raster.HOLD_IMAGE_SIZE:
        fail("hold image is not exactly 128 bytes")
    code = raster.build_hold_code(outer)
    if image[: len(code)] != code or code[-1] != 0xC9:
        fail("hold image does not begin with the hold code")
    for index in range(len(code), raster.HOLD_IMAGE_SIZE):
        if image[index] != raster.hold_fill_byte(raster.HOLD_ADDRESS + index):
            fail("hold image fill law differs")

    coverage = raster.row_coverage(outer)
    if not coverage["complete"]:
        fail("marker+hold+live rows do not cover all 128 physical rows")
    live = coverage["live_rows_excluded"]
    if min(live) != 0x40 or max(live) != 0x40 + len(code) - 1:
        fail("live-row exclusion does not match the executed hold code span")
    if set(coverage["marker_rows"]) != set(range(0x40)):
        fail("marker does not cover exactly rows 00h..3Fh")

    sample = raster.classify_readback(b"\x00\x01", b"\x00\xFF", 0x4D01)
    if (
        sample["verdict"] != "fail"
        or sample["rows_failed"] != [0x02]
        or sample["differences"][0]["xor"] != "0xFE"
    ):
        fail("classify_readback row mapping differs")
    print("JUKURAVI-RASTER-TEST: static checks passed", flush=True)


def start_cosim(
    trace: Path, rom: Path, temp: Path, retention_cycles: int
) -> tuple[subprocess.Popen[bytes], int, int]:
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="512",
        JUKU_DRAM_RETENTION_CYCLES=str(retention_cycles),
        JUKU_DRAM_RETENTION_ARM_PC="07A9",
    )
    with (temp / "cosim.stdout").open("wb") as stdout, (
        temp / "cosim.stderr"
    ).open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "5000000000"],
            cwd=temp,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
    return cosim, master, slave


def stop_cosim(cosim: subprocess.Popen[bytes], master: int, slave: int) -> None:
    cosim.terminate()
    try:
        cosim.wait(timeout=5)
    except subprocess.TimeoutExpired:
        cosim.kill()
        cosim.wait()
    os.close(master)
    os.close(slave)


def run_stage(
    trace: Path,
    rom: Path,
    temp_root: Path,
    name: str,
    retention_cycles: int,
    arm: str,
    run_timeout: float,
) -> tuple[int, dict[str, object]]:
    temp = temp_root / name
    logs = temp / "logs"
    temp.mkdir()
    cosim, master, slave = start_cosim(trace, rom, temp, retention_cycles)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--fd",
                str(master),
                "--arm",
                arm,
                "--hold-seconds",
                "0.5",
                "--loader-guard-ms",
                "0",
                "--run-timeout",
                str(run_timeout),
                "--log-dir",
                str(logs),
            ],
            cwd=ROOT,
            pass_fds=(master,),
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )
    finally:
        stop_cosim(cosim, master, slave)
    json_files = sorted(logs.glob("*.json"))
    if len(json_files) != 1:
        print(completed.stdout, file=sys.stderr)
        print(completed.stderr, file=sys.stderr)
        fail(f"{name}: expected one JSON capture, found {len(json_files)}")
    summary = json.loads(json_files[0].read_text())
    experiment = summary.get("raster_experiment")
    if not isinstance(experiment, dict):
        fail(f"{name}: capture has no raster_experiment record")
    print(
        f"JUKURAVI-RASTER-TEST: {name} exit={completed.returncode} "
        f"verdict={experiment.get('verdict')}",
        flush=True,
    )
    return completed.returncode, experiment


def main() -> int:
    check_static()
    if len(sys.argv) == 1:
        print("JUKURAVI-RASTER-TEST: PASS (static only)", flush=True)
        return 0
    if len(sys.argv) != 3:
        fail("usage: test.py [/path/to/trace diag-d0-row-refresh.bin]")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = t36.build()
    if not trace.is_file() or not rom_arg.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T36 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-raster-") as tmp:
        temp_root = Path(tmp)
        t36_rom = temp_root / "t36.bin"
        t36_rom.write_bytes(image)

        # Short hold, deadline far beyond it: the full staged flow must pass.
        code, experiment = run_stage(
            trace,
            t36_rom,
            temp_root,
            "armed-short-hold",
            retention_cycles=50_000_000,
            arm="raster",
            run_timeout=120.0,
        )
        if code != 0 or experiment["verdict"] != "pass":
            fail("armed short hold did not pass under a generous deadline")
        if experiment["arm_operation_return_a"] != f"0x{raster.ARM_RETURN_A:02X}":
            fail("arm snippet return marker differs")
        if experiment["marker_readback"]["differing_bytes"] != 0:
            fail("short-hold marker readback differs")
        if experiment["hold_image_readback"]["differing_bytes"] != 0:
            fail("short-hold image readback differs")

        # Same hold across a short decay deadline: the runner must classify
        # the decayed board (no RETURN, or decayed readback) — the negative
        # control proving the experiment observes missing refresh. The flat
        # model has no video-slot refresh, so arming cannot rescue it here.
        code, experiment = run_stage(
            trace,
            t36_rom,
            temp_root,
            "control-decayed-hold",
            retention_cycles=350_000,
            arm="none",
            run_timeout=60.0,
        )
        if code == 0 or experiment["verdict"] not in ("no_return", "decayed"):
            fail(
                "decay-deadline control did not produce a decay verdict "
                f"(exit={code}, verdict={experiment['verdict']})"
            )
    print("JUKURAVI-RASTER-TEST: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
