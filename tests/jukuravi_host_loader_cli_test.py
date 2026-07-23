#!/usr/bin/env python3
"""Round-trip the real host CLI's chunked upload against the Stage D2 ROM."""

from __future__ import annotations

import hashlib
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
sys.path[:0] = [
    str(ROOT / "spinoffs" / "jukuravi"),
    str(ROOT / "spinoffs" / "jukuravi" / "firmware"),
]
import build_d2_loader as firmware  # noqa: E402
from build_d0_serial import TRAIN_LENGTH  # noqa: E402
import protocol  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-HOST-LOADER: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d2-loader.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom_arg = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom_arg.is_file() or rom_arg.read_bytes() != image:
        print("trace executable or exact loader image is missing", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="jukuravi-host-loader-") as tmp_name:
        root = Path(tmp_name)
        rom = root / "loader.bin"
        program = root / "program.bin"
        logs = root / "logs"
        prefix = root / "checkpoint"
        rom.write_bytes(image)
        # HLT at the entry proves RUN. The remaining deterministic bytes force
        # two host chunks (253 + 47) without being executed.
        program_bytes = bytes((0x76,)) + bytes(
            (index * 37 + 11) & 0xFF for index in range(299)
        )
        program.write_bytes(program_bytes)

        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update(
            {
                "JUKU_USART_PTY": os.ttyname(slave),
                "JUKU_USART_TRANSFER_CYCLES": "64",
                "JUKU_USART_BYTE_CYCLES": "512",
                "JUKU_CHECKPOINT_PREFIX": str(prefix),
            }
        )
        with (root / "cosim.stdout").open("wb") as stdout, (
            root / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "2000000000"],
                cwd=root,
                env=env,
                stdout=stdout,
                stderr=stderr,
            )
        host = subprocess.run(
            [
                sys.executable,
                str(HOST),
                "--fd",
                str(master),
                "--timeout",
                "30",
                "--loader-timeout",
                "30",
                "--log-dir",
                str(logs),
                "--expect-rom-version",
                f"{firmware.ROM_VERSION:02X}",
                "--expect-crc16",
                f"{int(metadata['checksum']):04X}",
                "--load",
                str(program),
                "--load-address",
                "4000",
                "--run-address",
                "4000",
            ],
            cwd=ROOT,
            pass_fds=(master,),
            text=True,
            capture_output=True,
            timeout=60,
        )
        os.close(master)
        os.close(slave)
        try:
            cosim_returncode = cosim.wait(timeout=15)
        except subprocess.TimeoutExpired:
            cosim.kill()
            cosim.wait()
            fail("uploaded HLT program did not stop cosim")

        if host.returncode != 0:
            fail(f"host exited {host.returncode}: {host.stderr.strip()}")
        if cosim_returncode != 0:
            fail(f"cosim exited {cosim_returncode}")
        expected_lines = (
            "JUKURAVI: loader api=01 base=0x0A00 max_chunk=253",
            f"JUKURAVI: loaded {program} bytes=300 address=0x4000 chunks=2",
            "JUKURAVI: run acknowledged address=0x4000",
        )
        for line in expected_lines:
            if line not in host.stdout:
                fail(f"human loader verdict is missing: {line}")

        json_paths = list(logs.glob("*.json"))
        rx_paths = list(logs.glob("*.rx.bin"))
        tx_paths = list(logs.glob("*.tx.bin"))
        if len(json_paths) != 1 or len(rx_paths) != 1 or len(tx_paths) != 1:
            fail("timestamped loader evidence set is incomplete")
        summary = json.loads(json_paths[0].read_text())
        raw_rx = rx_paths[0].read_bytes()
        raw_tx = tx_paths[0].read_bytes()

        first = program_bytes[: protocol.LOADER_MAX_DATA]
        second = program_bytes[protocol.LOADER_MAX_DATA :]
        expected_tx = (
            bytes(metadata["ack"])
            + protocol.encode_load_frame(0x4000, first)
            + protocol.encode_load_frame(0x4000 + len(first), second)
            + protocol.encode_run_frame(0x4000)
        )
        if raw_tx != expected_tx:
            fail("raw TX log differs from exact ACK/LOAD/LOAD/RUN stream")
        if not raw_rx.startswith(bytes((0x55,)) * TRAIN_LENGTH):
            fail("raw RX log lost the training prefix")
        decoded = protocol.StreamDecoder().feed(raw_rx)
        if len(decoded) != 199:
            fail(f"raw RX log decodes to {len(decoded)} frames instead of 199")

        expected_loader = {
            "requested": True,
            "status": "run_acknowledged",
            "error": None,
            "source": str(program),
            "sha256": hashlib.sha256(program_bytes).hexdigest(),
            "address": "0x4000",
            "end_exclusive": "0x412C",
            "bytes": 300,
            "ready": {
                "api_version": protocol.LOADER_API_VERSION,
                "max_data_bytes": protocol.LOADER_MAX_DATA,
                "api_base": "0x0A00",
            },
            "chunks": [
                {
                    "index": 0,
                    "address": "0x4000",
                    "bytes": 253,
                    "status": "ok",
                },
                {
                    "index": 1,
                    "address": "0x40FD",
                    "bytes": 47,
                    "status": "ok",
                },
            ],
            "run": {
                "requested": True,
                "address": "0x4000",
                "acknowledged": True,
            },
        }
        if summary.get("loader") != expected_loader:
            fail(f"loader JSON differs: {summary.get('loader')!r}")
        if summary.get("status") != "ok" or summary.get("error") is not None:
            fail("host summary did not finish successfully")
        if len(summary.get("frames", [])) != 199:
            fail("JSON frame evidence does not include loader responses")
        attempts = summary.get("attempts", [])
        if len(attempts) != 1 or attempts[0].get("decoded_frames") != 199:
            fail("attempt evidence does not cover the complete loader workflow")
        if summary.get("transmitted_bytes") != len(expected_tx):
            fail("JSON transmitted-byte count differs")

        state = parse_state(prefix.with_suffix(".state"))
        if state.get("pc") != "4001" or state.get("halted") != "1":
            fail(f"uploaded entry did not halt at 4000: {state.get('pc')}")
        if state.get("usart_rx_bytes") != str(len(expected_tx)):
            fail("cosim did not receive the complete host command stream")

    print(
        "JUKURAVI-HOST-LOADER: PASS "
        "(real CLI; advertised 253-byte chunks; exact logs; RUN to uploaded HLT)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
