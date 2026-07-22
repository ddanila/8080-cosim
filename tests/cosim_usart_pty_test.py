#!/usr/bin/env python3
"""Exercise the cosim 8251 data/status registers through a real PTY."""

from __future__ import annotations

import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROM = bytes(
    [
        0x3E, 0x4E,       # MVI A,4E: async 8-bit mode
        0xD3, 0x09,       # OUT 09: mode
        0x3E, 0x37,       # MVI A,37: TxEN/RxEN/DTR/RTS/error reset
        0xD3, 0x09,       # OUT 09: command
        0xDB, 0x09,       # initial TxRDY+TxEMPTY
        0xE6, 0x05,
        0xFE, 0x05,
        0xC2, 0x43, 0x00,
        0x3E, 0x55,
        0xD3, 0x08,       # transmit 55
        0xDB, 0x09,       # holding register full: TxRDY=TxEMPTY=0
        0xE6, 0x05,
        0xFE, 0x00,
        0xC2, 0x43, 0x00,
        0xDB, 0x09,       # 001E: wait for TxRDY
        0xE6, 0x01,
        0xCA, 0x1E, 0x00,
        0x3E, 0xA5,
        0xD3, 0x08,       # transmit A5
        0xDB, 0x09,       # 0029: wait for TxRDY
        0xE6, 0x01,
        0xCA, 0x29, 0x00,
        0xDB, 0x09,       # 0030: wait for RxRDY
        0xE6, 0x02,
        0xCA, 0x30, 0x00,
        0xDB, 0x08,       # consume received byte; RxRDY must clear
        0xD3, 0x08,       # echo it
        0xDB, 0x09,       # 003B: wait for final TxEMPTY, not merely TxRDY
        0xE6, 0x04,
        0xCA, 0x3B, 0x00,
        0x76,             # HLT success
        0x76,             # HLT failure
    ]
)
assert len(ROM) == 0x44

IO_RE = re.compile(
    r"^\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) "
    r"value=0x([0-9A-Fa-f]{2}) cyc=([0-9]+)"
)


def read_exact(fd: int, count: int, timeout: float = 5.0) -> bytes:
    result = bytearray()
    while len(result) < count:
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            raise RuntimeError(
                f"PTY timeout: wanted {count} bytes, received {result.hex()}"
            )
        result.extend(os.read(fd, count - len(result)))
    return bytes(result)


def exchange(proc: subprocess.Popen[str], fd: int) -> tuple[bytes, bytes, str, str]:
    try:
        outbound = read_exact(fd, 2)
        os.write(fd, b"\x3c")
        echoed = read_exact(fd, 1)
        stdout, stderr = proc.communicate(timeout=5)
    except Exception:
        proc.kill()
        stdout, stderr = proc.communicate()
        print(stdout, file=sys.stderr)
        print(stderr, file=sys.stderr)
        raise
    return outbound, echoed, stdout, stderr


def validate(
    label: str,
    proc: subprocess.Popen[str],
    outbound: bytes,
    echoed: bytes,
    stdout: str,
    stderr: str,
    attach_marker: str,
) -> list[str]:
    failures = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound != b"\x55\xa5":
        failures.append(f"{label}: TX bytes {outbound.hex()} != 55a5")
    if echoed != b"\x3c":
        failures.append(f"{label}: echo byte {echoed.hex()} != 3c")
    if attach_marker not in stderr:
        failures.append(f"{label}: cosim did not report its PTY attachment")
    events = []
    for line in stderr.splitlines():
        match = IO_RE.match(line)
        if match:
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16), int(match.group(4))))
    writes = [event for event in events if event[:3] in (
        ("OUT", 0x08, 0x55), ("OUT", 0x08, 0xA5), ("OUT", 0x08, 0x3C)
    )]
    status = [event for event in events if event[0] == "IN" and event[1] == 0x09]
    if len(writes) != 3 or not status:
        failures.append(f"{label}: missing USART data writes or status reads")
    else:
        initial = [value & 0x05 for _, _, value, cyc in status if cyc < writes[0][3]]
        if initial != [0x05]:
            failures.append(f"{label}: initial TxRDY/TxEMPTY status {initial} != [5]")
        for index, write in enumerate(writes):
            end = writes[index + 1][3] if index + 1 < len(writes) else 1 << 63
            values = [value & 0x05 for _, _, value, cyc in status
                      if write[3] < cyc < end]
            compressed = [value for pos, value in enumerate(values)
                          if pos == 0 or value != values[pos - 1]]
            expected = [0x00, 0x01] if index == 0 else [0x00, 0x01, 0x05]
            if compressed[:len(expected)] != expected:
                failures.append(
                    f"{label}: TX byte {write[2]:02x} status transitions "
                    f"{compressed} do not start {expected}"
                )
    return failures


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/cosim-trace", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        print(f"missing cosim executable: {trace}", file=sys.stderr)
        return 2

    failures = []
    with tempfile.TemporaryDirectory(prefix="juku-usart-pty-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / "usart-pty.bin"
        rom.write_bytes(ROM)
        base_env = os.environ.copy()
        base_env["JUKU_TRACE_IO"] = "1"
        base_env["JUKU_USART_TRANSFER_CYCLES"] = "64"
        base_env["JUKU_USART_BYTE_CYCLES"] = "256"

        master, slave = pty.openpty()
        tty.setraw(slave)
        attached_env = base_env | {"JUKU_USART_PTY": os.ttyname(slave)}
        attached = subprocess.Popen(
            [str(trace), str(rom), "20000000"], cwd=tmp, env=attached_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        outbound, echoed, stdout, stderr = exchange(attached, master)
        os.close(master)
        os.close(slave)
        failures.extend(validate(
            "attached", attached, outbound, echoed, stdout, stderr,
            "[USART] attached PTY=",
        ))

        auto_env = base_env | {"JUKU_USART_PTY": "auto"}
        automatic = subprocess.Popen(
            [str(trace), str(rom), "200000000"], cwd=tmp, env=auto_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        first_stderr = automatic.stderr.readline() if automatic.stderr else ""
        marker = "[USART] PTY slave="
        slave_name = first_stderr.strip().removeprefix(marker)
        if not first_stderr.startswith(marker) or not slave_name:
            automatic.kill()
            stdout, stderr = automatic.communicate()
            failures.append(f"automatic: malformed PTY announcement {first_stderr!r}")
        else:
            auto_slave = os.open(slave_name, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            tty.setraw(auto_slave)
            outbound, echoed, stdout, stderr = exchange(automatic, auto_slave)
            os.close(auto_slave)
            stderr = first_stderr + stderr
            failures.extend(validate(
                "automatic", automatic, outbound, echoed, stdout, stderr, marker,
            ))

    if failures:
        print("COSIM-USART-PTY: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "COSIM-USART-PTY: PASS (attached+automatic PTY, TX 55a5, "
        "RX/echo 3c, distinct TxRDY/TxEMPTY transitions, RxRDY polled)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
