#!/usr/bin/env python3
"""Prove the framed Jukuravi D0 external handshake and its fault paths."""

from __future__ import annotations

import os
import errno
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_serial as firmware  # noqa: E402
import protocol  # noqa: E402


IO_RE = re.compile(
    r"^\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) "
    r"value=0x([0-9A-Fa-f]{2}) cyc=([0-9]+) pc=([0-9A-Fa-f]{4})"
)
ALIVE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
            (0x1B, 0x50), (0x19, 0x01)]
USART_INIT_IO = [(0x09, 0x00)] * 3 + [
    (0x09, 0x40), (0x09, 0x4E), (0x09, 0x37), (0x08, 0x55),
    (0x1B, 0x34), (0x18, 0x08), (0x18, 0x00),
]
CPU_FAIL_IO = [(0x1B, 0x76), (0x19, 0x40), (0x19, 0x1F)]
USART_FAIL_IO = [(0x1B, 0x76), (0x19, 0xA0), (0x19, 0x0F)]
SERIAL_OK_IO = [(0x1B, 0x76), (0x19, 0xE8), (0x19, 0x03),
                (0x1B, 0x50), (0x19, 0x01)]
SERIAL_DEAD_IO = [(0x1B, 0x76), (0x19, 0x80), (0x19, 0x3E)]


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def run_image(
    trace: Path,
    image: bytes,
    label: str,
    *,
    reply: bytes | None = None,
    expected_outbound: int = 0,
    fault: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str], list[tuple[str, int, int, int]], bytes]:
    with tempfile.TemporaryDirectory(prefix=f"juku-d0-serial-{label}-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / f"{label}.bin"
        prefix = tmp / "checkpoint"
        stdout_path = tmp / "stdout"
        stderr_path = tmp / "stderr"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update({
            "JUKU_TRACE_IO": "1",
            "JUKU_CHECKPOINT_PREFIX": str(prefix),
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
        })
        if fault:
            env["JUKU_USART_FAULT"] = fault
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                [str(trace), str(rom), "10000000"], cwd=tmp, env=env,
                stdout=stdout_file, stderr=stderr_file,
            )
            os.close(slave)
            outbound = bytearray()
            replied = False
            deadline = time.monotonic() + 20
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    process.kill()
                    raise TimeoutError(f"{label}: cosim did not terminate")
                if select.select([master], [], [], 0.02)[0]:
                    try:
                        outbound.extend(os.read(master, 256))
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                if reply is not None and not replied and len(outbound) >= expected_outbound:
                    os.write(master, reply)
                    replied = True
            while select.select([master], [], [], 0)[0]:
                try:
                    outbound.extend(os.read(master, 256))
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    break
            returncode = process.wait()
        os.close(master)
        stdout = stdout_path.read_text(errors="replace")
        stderr = stderr_path.read_text(errors="replace")
        state = parse_state(prefix.with_suffix(".state"))
    events = []
    for line in stderr.splitlines():
        match = IO_RE.match(line)
        if match:
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16), int(match.group(4))))
    completed = subprocess.CompletedProcess([], returncode, stdout, stderr)
    return completed, state, events, bytes(outbound)


def verify_common(
    label: str,
    result: tuple[subprocess.CompletedProcess[str], dict[str, str],
                  list[tuple[str, int, int, int]], bytes],
    expected_writes: list[tuple[int, int]],
    expected_pc: int,
) -> list[str]:
    proc, state, events, _ = result
    failures: list[str] = []
    writes = [(port, value) for direction, port, value, _ in events if direction == "OUT"]
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if writes != expected_writes:
        failures.append(f"{label}: I/O writes differ: {writes}")
    if state.get("pc") != f"{expected_pc + 1:04X}":
        failures.append(f"{label}: PC {state.get('pc')} != {expected_pc + 1:04X}")
    for key, expected in (("sp", "0000"), ("halted", "1"), ("iff", "0"),
                          ("mode", "0"), ("mode_switches", "0")):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    if "==== RAM write density (pages >0) ====\n  0x" in proc.stdout:
        failures.append(f"{label}: ROM wrote RAM")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-serial.bin", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    built, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != built:
        print("trace executable or exact serial diagnostic ROM is missing", file=sys.stderr)
        return 2

    if (protocol.crc8_atm(b"123456789") != 0xF4 or
            protocol.crc16_ccitt_false(b"123456789") != 0x29B1):
        print("JUKURAVI-D0-SERIAL: FAIL standard CRC check vectors", file=sys.stderr)
        return 1

    checksum_image = bytearray(built)
    for offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        print("JUKURAVI-D0-SERIAL: FAIL self-checksum contract", file=sys.stderr)
        return 1

    banner = bytes(metadata["banner"])
    ack = bytes(metadata["ack"])
    outbound_expected = bytes((firmware.USART_TEST_BYTE,)) * firmware.TRAIN_LENGTH + banner
    data_writes = [(firmware.USART_DATA, value) for value in outbound_expected[1:]]
    base_writes = ALIVE_IO + USART_INIT_IO + data_writes
    failures: list[str] = []

    valid = run_image(trace, built, "valid", reply=ack,
                      expected_outbound=len(outbound_expected))
    failures.extend(verify_common(
        "valid", valid, base_writes + SERIAL_OK_IO, int(metadata["serial_ok_halt"])
    ))
    if valid[3] != outbound_expected:
        failures.append(f"valid: outbound {valid[3].hex()} != {outbound_expected.hex()}")
    decoder = protocol.StreamDecoder()
    frames = decoder.feed(valid[3])
    if frames != [protocol.Frame(protocol.TYPE_BANNER, banner[4:-1])]:
        failures.append(f"valid: decoded frames differ: {frames}")
    corrupt_banner = bytearray(banner)
    corrupt_banner[-1] ^= 1
    resync_decoder = protocol.StreamDecoder()
    if resync_decoder.feed(bytes(corrupt_banner) + banner) != [
            protocol.Frame(protocol.TYPE_BANNER, banner[4:-1])]:
        failures.append("valid: decoder did not resynchronize after corrupt frame")
    for key, expected in (("a", "01"), ("e", "D0"), ("usart_rx_bytes", str(len(ack))),
                          ("usart_tx_bytes", str(len(outbound_expected)))):
        if valid[1].get(key) != expected:
            failures.append(f"valid: {key}={valid[1].get(key, 'missing')} != {expected}")

    malformed_ack = bytearray(ack)
    malformed_ack[-1] ^= 1
    malformed = run_image(trace, built, "malformed", reply=bytes(malformed_ack),
                          expected_outbound=len(outbound_expected))
    failures.extend(verify_common(
        "malformed", malformed, base_writes + SERIAL_DEAD_IO,
        int(metadata["serial_dead_halt"]),
    ))
    if malformed[3] != outbound_expected:
        failures.append("malformed: outbound stream changed")

    timeout = run_image(trace, built, "timeout")
    failures.extend(verify_common(
        "timeout", timeout, base_writes + SERIAL_DEAD_IO,
        int(metadata["serial_dead_halt"]),
    ))
    rx_wait_reads = sum(direction == "IN" and port == firmware.USART_CONTROL
                        and value & 0x02 == 0 for direction, port, value, _ in timeout[2])
    if rx_wait_reads < firmware.TIMEOUT_COUNT:
        failures.append(f"timeout: only {rx_wait_reads} not-ready reads")

    tx_stuck = run_image(trace, built, "tx-stuck", fault="tx_stuck")
    failures.extend(verify_common(
        "tx-stuck", tx_stuck, ALIVE_IO + USART_INIT_IO + USART_FAIL_IO,
        int(metadata["usart_fail_halt"]),
    ))
    if tx_stuck[3]:
        failures.append(f"tx-stuck: unexpectedly transmitted {tx_stuck[3].hex()}")

    cpu_bad_image = bytearray(built)
    cpu_bad_image[int(metadata["signature_expected_offset"])] ^= 1
    cpu_bad = run_image(trace, bytes(cpu_bad_image), "cpu-bad")
    failures.extend(verify_common(
        "cpu-bad", cpu_bad, ALIVE_IO + CPU_FAIL_IO,
        int(metadata["cpu_fail_halt"]),
    ))
    if cpu_bad[3]:
        failures.append(f"cpu-bad: unexpectedly transmitted {cpu_bad[3].hex()}")

    if failures:
        print("JUKURAVI-D0-SERIAL: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-SERIAL: PASS "
        f"(train={firmware.TRAIN_LENGTH}, banner={banner.hex()}, ack={ack.hex()}, "
        "CRC/malformed/timeout/local-stuck/CPU-bad, SP=0, RAM writes=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
