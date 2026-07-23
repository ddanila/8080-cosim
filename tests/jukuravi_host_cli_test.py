#!/usr/bin/env python3
"""Round-trip the real Jukuravi host CLI against the exact D0 cosim ROM."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
sys.path[:0] = [str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_framebuffer as firmware  # noqa: E402
from build_d0_serial import TRAIN_LENGTH  # noqa: E402
import protocol  # noqa: E402


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line
    )


def run_case(
    trace: Path,
    image: bytes,
    metadata: dict[str, int | list[int] | bytes],
    root: Path,
    label: str,
    *,
    ram_fault: str | None = None,
) -> tuple[list[str], dict[str, object]]:
    case = root / label
    case.mkdir()
    rom = case / "diag.bin"
    prefix = case / "checkpoint"
    cosim_stdout = case / "cosim.stdout"
    cosim_stderr = case / "cosim.stderr"
    logs = case / "logs"
    rom.write_bytes(image)

    master, slave = pty.openpty()
    tty.setraw(slave)
    env = os.environ.copy()
    env.update({
        "JUKU_USART_PTY": os.ttyname(slave),
        "JUKU_USART_TRANSFER_CYCLES": "64",
        "JUKU_USART_BYTE_CYCLES": "512",
        "JUKU_CHECKPOINT_PREFIX": str(prefix),
    })
    if ram_fault:
        env["JUKU_RAM_FAULT"] = ram_fault

    with cosim_stdout.open("wb") as stdout_file, cosim_stderr.open("wb") as stderr_file:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "100000000"],
            cwd=case,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
        )
    host = subprocess.run(
        [
            sys.executable,
            str(HOST),
            "--fd", str(master),
            "--timeout", "30",
            "--log-dir", str(logs),
            "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
            "--expect-crc16", f"{int(metadata['checksum']):04X}",
        ],
        cwd=ROOT,
        pass_fds=(master,),
        text=True,
        capture_output=True,
        timeout=40,
    )
    os.close(master)
    os.close(slave)
    try:
        cosim_returncode = cosim.wait(timeout=30)
    except subprocess.TimeoutExpired:
        cosim.kill()
        cosim.wait()
        raise

    failures: list[str] = []
    if host.returncode != 0:
        failures.append(
            f"{label}: host exited {host.returncode}: {host.stderr.strip()}"
        )
    identity_line = (
        f"JUKURAVI: protocol=01 rom={firmware.ROM_VERSION:02X} "
        f"image_crc16={int(metadata['checksum']):04X}"
    )
    if identity_line not in host.stdout:
        failures.append(f"{label}: human-readable image verdict is missing")
    if label == "clean":
        for bit in range(8):
            if f"JUKURAVI: D{84 + bit}/bit{bit} PASS" not in host.stdout:
                failures.append(f"{label}: D{84 + bit} PASS verdict is missing")
        if "JUKURAVI: largest-good-window 4000-FFFF bytes=49152" not in host.stdout:
            failures.append(f"{label}: human-readable window verdict differs")
    else:
        for bit in (3, 5):
            if f"JUKURAVI: D{84 + bit}/bit{bit} bad pages 7A" not in host.stdout:
                failures.append(f"{label}: D{84 + bit} fault verdict is missing")
        if "JUKURAVI: largest-good-window 7B00-FFFF bytes=34048" not in host.stdout:
            failures.append(f"{label}: human-readable window verdict differs")
    if cosim_returncode != 0:
        failures.append(f"{label}: cosim exited {cosim_returncode}")

    json_paths = list(logs.glob("*.json"))
    rx_paths = list(logs.glob("*.rx.bin"))
    tx_paths = list(logs.glob("*.tx.bin"))
    if len(json_paths) != 1 or len(rx_paths) != 1 or len(tx_paths) != 1:
        failures.append(f"{label}: incomplete timestamped log set")
        return failures, {}
    summary = json.loads(json_paths[0].read_text())
    raw_rx = rx_paths[0].read_bytes()
    raw_tx = tx_paths[0].read_bytes()
    if raw_tx != bytes(metadata["ack"]):
        failures.append(f"{label}: ACK log {raw_tx.hex()} differs")
    if not raw_rx.startswith(bytes((0x55,)) * TRAIN_LENGTH):
        failures.append(f"{label}: raw RX log lost the training prefix")
    decoder = protocol.StreamDecoder()
    decoded = decoder.feed(raw_rx)
    if len(decoded) != 195:
        failures.append(f"{label}: raw RX log decodes to {len(decoded)} frames")
    if summary.get("status") != "ok" or summary.get("error") is not None:
        failures.append(f"{label}: summary status is not ok")
    if summary.get("leading_training_bytes") != TRAIN_LENGTH:
        failures.append(f"{label}: training-byte count differs")
    if summary.get("transmitted_bytes") != len(bytes(metadata["ack"])):
        failures.append(f"{label}: transmitted-byte count differs")
    if summary.get("nano_control") != {
        "dtr_reset_requested": False,
        "dtr_sequence_completed": False,
    }:
        failures.append(f"{label}: fd transport unexpectedly requested Nano reset")
    image_summary = summary.get("image", {})
    if image_summary != {
        "protocol_version": protocol.PROTOCOL_VERSION,
        "rom_version": firmware.ROM_VERSION,
        "crc16": f"{int(metadata['checksum']):04X}",
    }:
        failures.append(f"{label}: image summary differs: {image_summary}")
    if len(summary.get("frames", [])) != 195:
        failures.append(f"{label}: JSON frame count differs")
    state = parse_state(prefix.with_suffix(".state"))
    if state.get("pc") != f"{int(metadata['success_halt']) + 1:04X}":
        failures.append(f"{label}: wrong terminal PC {state.get('pc')}")
    if state.get("usart_rx_bytes") != "9":
        failures.append(f"{label}: ROM did not receive the nine-byte ACK")
    return failures, summary


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace "
            "diag-d0-framebuffer.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact framebuffer image is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="jukuravi-host-") as tmp_name:
        root = Path(tmp_name)
        clean_failures, clean = run_case(trace, image, metadata, root, "clean")
        failures.extend(clean_failures)
        fault_failures, fault = run_case(
            trace, image, metadata, root, "fault", ram_fault="7A5C:08:20"
        )
        failures.extend(fault_failures)

        if clean:
            clean_survey = clean["ram_survey"]
            if any(clean_survey["bad_pages_by_chip"].values()):
                failures.append("clean: JSON reports bad RAM pages")
            if clean_survey["largest_good_window"] != {
                "start": "0x4000", "end_exclusive": "0x10000", "bytes": 49152,
            }:
                failures.append("clean: largest-good-window verdict differs")
        if fault:
            fault_survey = fault["ram_survey"]
            expected_bad = {
                f"D{84 + bit}": (["0x7A"] if bit in (3, 5) else [])
                for bit in range(8)
            }
            if fault_survey["bad_pages_by_chip"] != expected_bad:
                failures.append(
                    f"fault: chip/page verdict differs: "
                    f"{fault_survey['bad_pages_by_chip']}"
                )
            if fault_survey["largest_good_window"] != {
                "start": "0x7B00", "end_exclusive": "0x10000", "bytes": 34048,
            }:
                failures.append("fault: largest-good-window verdict differs")

    if failures:
        print("JUKURAVI-HOST-CLI: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-HOST-CLI: PASS "
        "(exact banner/ACK; 195 frames; timestamped RX/TX/JSON; clean and "
        "D87+D89 page-7A verdicts)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
