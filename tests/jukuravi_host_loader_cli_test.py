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


HEARTBEAT_COUNT = 3
LOAD_ADDRESS = 0x4000


def fail(message: str) -> None:
    print(f"JUKURAVI-HOST-LOADER: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line
    )


def heartbeat_program() -> tuple[bytes, int]:
    """Emit three framed heartbeats through SERIAL_PUT, drain, and halt."""
    code = bytearray()
    for sequence in range(HEARTBEAT_COUNT):
        for byte in protocol.encode_heartbeat_frame(sequence):
            code.extend(
                (
                    0x3E,
                    byte,  # MVI A,byte
                    0xCD,
                    firmware.LOADER_API_SERIAL_PUT & 0xFF,
                    firmware.LOADER_API_SERIAL_PUT >> 8,
                )
            )
    # Wait well beyond one modeled byte time so HLT cannot close the PTY while
    # the final CRC byte is still in the 8251 shift register.
    loop_address = LOAD_ADDRESS + len(code) + 3
    code.extend(
        (
            0x01,
            0x00,
            0x10,  # LXI B,1000h
            0x0B,  # DCX B
            0x78,  # MOV A,B
            0xB1,  # ORA C
            0xC2,
            loop_address & 0xFF,
            loop_address >> 8,  # JNZ loop
            0x76,  # HLT
        )
    )
    halt_pc = LOAD_ADDRESS + len(code)
    if len(code) > 300:
        raise AssertionError("heartbeat fixture exceeds two-chunk upload size")
    code.extend((index * 37 + 11) & 0xFF for index in range(300 - len(code)))
    return bytes(code), halt_pc


def run_heartbeat_timeout(
    trace: Path,
    image: bytes,
    metadata: dict[str, object],
    root: Path,
) -> None:
    case = root / "heartbeat-timeout"
    case.mkdir()
    rom = case / "loader.bin"
    program = case / "spin.bin"
    logs = case / "logs"
    rom.write_bytes(image)
    program_bytes = bytes((0xC3, 0x00, 0x40)) + bytes(
        (index * 19 + 7) & 0xFF for index in range(297)
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
        }
    )
    with (case / "cosim.stdout").open("wb") as stdout, (
        case / "cosim.stderr"
    ).open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "2000000000"],
            cwd=case,
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
    try:
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
                "--heartbeat-count",
                "1",
                "--heartbeat-timeout",
                "0.1",
            ],
            cwd=ROOT,
            pass_fds=(master,),
            text=True,
            capture_output=True,
            timeout=60,
        )
    finally:
        cosim.terminate()
        try:
            cosim.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cosim.kill()
            cosim.wait()
        os.close(master)
        os.close(slave)

    error = "heartbeat timeout after 0/1 records"
    if host.returncode != 1 or error not in host.stderr:
        fail(
            "heartbeat timeout did not fail the real CLI exactly: "
            f"rc={host.returncode} stderr={host.stderr.strip()!r}"
        )
    json_paths = list(logs.glob("*.json"))
    rx_paths = list(logs.glob("*.rx.bin"))
    tx_paths = list(logs.glob("*.tx.bin"))
    if len(json_paths) != 1 or len(rx_paths) != 1 or len(tx_paths) != 1:
        fail("heartbeat-timeout evidence set is incomplete")
    summary = json.loads(json_paths[0].read_text())
    loader = summary.get("loader")
    if not isinstance(loader, dict):
        fail("heartbeat-timeout loader evidence is missing")
    heartbeat = loader.get("heartbeat")
    expected_heartbeat = {
        "required": 1,
        "received": 0,
        "timeout_seconds": 0.1,
        "status": "error",
        "error": error,
        "events": [],
    }
    if heartbeat != expected_heartbeat:
        fail(f"heartbeat-timeout evidence differs: {heartbeat!r}")
    if loader.get("status") != "error" or loader.get("error") != error:
        fail("loader did not retain the heartbeat timeout")
    if summary.get("status") != "error" or summary.get("error") != error:
        fail("session did not retain the heartbeat timeout")
    attempts = summary.get("attempts", [])
    if (
        len(attempts) != 1
        or attempts[0].get("outcome") != "heartbeat_timeout"
        or attempts[0].get("error") != error
        or attempts[0].get("loader") != loader
    ):
        fail(
            "heartbeat timeout was retried or lost from attempt evidence: "
            f"{attempts!r}"
        )

    first = program_bytes[: protocol.LOADER_MAX_DATA]
    second = program_bytes[protocol.LOADER_MAX_DATA :]
    expected_tx = (
        bytes(metadata["ack"])
        + protocol.encode_load_frame(LOAD_ADDRESS, first)
        + protocol.encode_load_frame(LOAD_ADDRESS + len(first), second)
        + protocol.encode_run_frame(LOAD_ADDRESS)
    )
    if tx_paths[0].read_bytes() != expected_tx:
        fail("heartbeat-timeout TX evidence differs")
    decoded = protocol.StreamDecoder().feed(rx_paths[0].read_bytes())
    if len(decoded) != 199 or decoded[-1] != protocol.Frame(
        protocol.TYPE_RUN_ACK, b""
    ):
        fail("heartbeat timeout did not occur immediately after RUN_ACK")


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
        # The executable prefix proves post-RUN heartbeat supervision and HLT;
        # deterministic padding still forces exact 253 + 47 byte chunks.
        program_bytes, halt_pc = heartbeat_program()
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
                "--heartbeat-count",
                str(HEARTBEAT_COUNT),
                "--heartbeat-timeout",
                "5",
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
            "JUKURAVI: heartbeat 3/3 last=02 timeout=5.0s",
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
        if len(decoded) != 202:
            fail(f"raw RX log decodes to {len(decoded)} frames instead of 202")

        expected_loader = {
            "requested": True,
            "status": "heartbeat_complete",
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
            "heartbeat": {
                "required": HEARTBEAT_COUNT,
                "received": HEARTBEAT_COUNT,
                "timeout_seconds": 5.0,
                "status": "complete",
                "error": None,
                "events": [
                    {"index": 0, "frame_index": 199, "sequence": 0},
                    {"index": 1, "frame_index": 200, "sequence": 1},
                    {"index": 2, "frame_index": 201, "sequence": 2},
                ],
            },
        }
        if summary.get("loader") != expected_loader:
            fail(f"loader JSON differs: {summary.get('loader')!r}")
        if summary.get("status") != "ok" or summary.get("error") is not None:
            fail("host summary did not finish successfully")
        if len(summary.get("frames", [])) != 202:
            fail("JSON frame evidence does not include loader responses")
        attempts = summary.get("attempts", [])
        if (
            len(attempts) != 1
            or attempts[0].get("decoded_frames") != 202
            or attempts[0].get("loader") != expected_loader
        ):
            fail("attempt evidence does not cover the complete loader workflow")
        if summary.get("transmitted_bytes") != len(expected_tx):
            fail("JSON transmitted-byte count differs")

        state = parse_state(prefix.with_suffix(".state"))
        if state.get("pc") != f"{halt_pc:04x}" or state.get("halted") != "1":
            fail(f"uploaded heartbeat fixture did not halt: {state.get('pc')}")
        if state.get("usart_rx_bytes") != str(len(expected_tx)):
            fail("cosim did not receive the complete host command stream")

        run_heartbeat_timeout(trace, image, metadata, root)

    print(
        "JUKURAVI-HOST-LOADER: PASS "
        "(real CLI; RUN; sequenced heartbeats; exact timeout evidence)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
