#!/usr/bin/env python3
"""Boot vendored and optional external Juku systems through NetBios/Janet."""

from __future__ import annotations

import concurrent.futures
import os
import pty
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.janet_netboot import (  # noqa: E402
    SYSTEM_BYTES,
    SYSTEM_LOAD_ADDRESS,
    SYSTEM_PREFIX,
    prepare_image,
    serve,
)


def system_images() -> tuple[Path, ...]:
    images = list(sorted((ROOT / "media" / "system").glob("*.BIN")))
    external = os.environ.get("JUKU_NETBOOT_SYSTEM")
    if external:
        images.append(Path(external).resolve())
    return tuple(images)


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line)


def run_one(trace: Path, image_path: Path, root: Path) -> dict[str, object]:
    started = time.monotonic()
    source = image_path.read_bytes()
    prepared = prepare_image(source)
    expected_system = source[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES]
    case = root / image_path.stem.lower()
    case.mkdir()
    prefix = case / "checkpoint"
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="2300",
        JUKU_KEYS="TN0201",
        JUKU_KEY_HOLD_FRAMES="6",
        JUKU_KEY_GAP_FRAMES="8",
        JUKU_STOP_PC="0xCA00",
        JUKU_STOP_PC_AFTER_USART_RX="1000",
        JUKU_CHECKPOINT_PREFIX=str(prefix),
    )
    stdout_path = case / "stdout.txt"
    stderr_path = case / "stderr.txt"
    with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
        process = subprocess.Popen(
            [str(trace), str(ROOT / "roms" / "ekta37.bin"),
             "1000000000000", "0", "100000"],
            cwd=case,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
        os.close(slave)
        try:
            protocol = serve(master, source, timeout=120, verbose=False)
            process.wait(timeout=20)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)

    failures: list[str] = []
    if process.returncode != 0:
        failures.append(f"cosim exited {process.returncode}")
    if prepared.load_address != 0x0100 or prepared.entry != 0x0100:
        failures.append("JUKUSYS image was not wrapped as a 0100h executable")
    if len(prepared.data) != 0x1A80:
        failures.append(f"staging executable is {len(prepared.data)} bytes")
    if protocol["image_bytes"] != len(prepared.data):
        failures.append("protocol byte count differs from staging image")
    if protocol["ack_08"] != 1 + (len(prepared.data) // 128) * 3 + 1:
        failures.append(f"positive ACK count is {protocol['ack_08']}")

    state_path = prefix.with_suffix(".state")
    ram_path = prefix.with_suffix(".ram")
    if not state_path.is_file() or not ram_path.is_file():
        failures.append("cosim did not write the CA00h checkpoint")
        state: dict[str, str] = {}
        ram = b""
    else:
        state = parse_state(state_path)
        ram = ram_path.read_bytes()
        if state.get("pc") != "CA00":
            failures.append(f"cold-start PC is {state.get('pc')}")
        if state.get("mode") != "1":
            failures.append(f"memory mode is {state.get('mode')}")
        if state.get("usart_mode") != "5E":
            failures.append(f"8251 mode is {state.get('usart_mode')}")
        if state.get("usart_command") != "35":
            failures.append(f"8251 command is {state.get('usart_command')}")
        if state.get("port_18", "").split(",", 1)[0] != "last:08":
            failures.append(f"D57 divisor state is {state.get('port_18')}")
        staged = ram[0x0100:0x0100 + len(prepared.data)]
        if staged != prepared.data:
            failures.append("received 0100h staging executable differs")
        installed = ram[SYSTEM_LOAD_ADDRESS:SYSTEM_LOAD_ADDRESS + SYSTEM_BYTES]
        if installed != expected_system:
            failures.append("installed B400h system payload differs")

    return {
        "name": image_path.name,
        "failures": failures,
        "seconds": time.monotonic() - started,
        "sent": protocol["sent_frames"],
        "retries": protocol["ack_09"],
        "rx": state.get("usart_rx_bytes", "missing"),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/cosim-trace",
              file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    systems = system_images()
    if not trace.is_file() or len(systems) < 5 or any(not path.is_file() for path in systems):
        print("missing cosim executable or system image", file=sys.stderr)
        return 2
    jobs = max(1, min(len(systems), int(os.environ.get("JUKU_NETBOOT_JOBS", "5"))))
    with tempfile.TemporaryDirectory(prefix="juku-netboot.") as temp_name:
        temp = Path(temp_name)
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(run_one, trace, image, temp) for image in systems]
            results = [future.result() for future in futures]

    failures = []
    for result in results:
        verdict = "PASS" if not result["failures"] else "FAIL"
        print(
            f"{result['name']}: {verdict} "
            f"({result['seconds']:.1f}s, sent={result['sent']}, "
            f"REJ/retry={result['retries']}, rx={result['rx']})"
        )
        failures.extend(f"{result['name']}: {item}"
                        for item in result["failures"])
    if failures:
        print("JANET-NETBOOT-TEST: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"JANET-NETBOOT-TEST: PASS (all {len(systems)} systems reached CA00h byte-exactly)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
