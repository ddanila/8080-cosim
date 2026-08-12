#!/usr/bin/env python3
"""Prove cosim's 8251 wire-rate overrun and ER recovery semantics."""

from __future__ import annotations

import os
import pty
import re
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


# Configure 8-bit async receive, delay for several wire characters without
# reading, report status, issue ER, report status again, then report the byte
# which must have remained in the receive register.
ROM = bytes((
    0x3E, 0x4E,       # MVI A,4E
    0xD3, 0x09,       # OUT USART control: mode
    0x3E, 0x34,       # MVI A,34: RxEN + ER + RTS, Tx disabled
    0xD3, 0x09,       # OUT command
    0x01, 0x00, 0x20, # LXI B,2000h
    0x0B,             # delay: DCX B
    0x78,             # MOV A,B
    0xB1,             # ORA C
    0xC2, 0x0B, 0x00, # JNZ delay
    0xDB, 0x09,       # IN status: must have RxRDY + OE
    0x3E, 0x34,       # ER while the byte remains unread
    0xD3, 0x09,
    0xDB, 0x09,       # status: RxRDY remains, OE clears
    0xDB, 0x08,       # consume oldest byte
    0x76,
))

IO_RE = re.compile(r"^\[IOSEQ\] IN  port=0x(09|08) value=0x([0-9A-Fa-f]{2}) ")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/cosim-trace", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="juku-usart-overrun-") as name:
        work = Path(name)
        rom = work / "overrun.bin"
        rom.write_bytes(ROM)
        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="16",
            JUKU_USART_BYTE_CYCLES="256",
            JUKU_TRACE_IO="1",
        )
        process = subprocess.Popen(
            [str(trace), str(rom), "20000000"], cwd=work, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        os.write(master, b"\x11\x22\x33")
        try:
            stdout, stderr = process.communicate(timeout=5)
        except Exception:
            process.kill()
            stdout, stderr = process.communicate()
            print(stdout, file=sys.stderr)
            print(stderr, file=sys.stderr)
            raise
        finally:
            os.close(master)
            os.close(slave)

        reads = [(int(match.group(1), 16), int(match.group(2), 16))
                 for line in stderr.splitlines()
                 if (match := IO_RE.match(line))]
        if len(reads) < 3:
            print(f"COSIM-USART-OVERRUN: FAIL: reads={reads!r}\n{stderr}", file=sys.stderr)
            return 1
        before, after, retained = (reads[-3][1], reads[-2][1], reads[-1][1])
        failures = []
        if not before & 0x02 or not before & 0x10:
            failures.append(f"pre-ER status 0x{before:02x} lacks RxRDY+OE")
        if not after & 0x02 or after & 0x38:
            failures.append(f"post-ER status 0x{after:02x} did not retain RxRDY/clear errors")
        if retained != 0x11:
            failures.append(f"retained byte 0x{retained:02x} != oldest byte 0x11")
        if process.returncode != 0:
            failures.append(f"cosim exited {process.returncode}: {stderr[-500:]}")
        if failures:
            print("COSIM-USART-OVERRUN: FAIL", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(
            "COSIM-USART-OVERRUN: PASS "
            "(wire continues while RxRDY full; OE latches; ER preserves oldest byte)"
        )
        # D57 channel 0 is left by EktaSoft in LSB-only BCD mode 3. Intel defines
        # two as the minimum periodic count in modes 2/3, so count one cannot be
        # treated as a 1.23 MHz clock for an otherwise tempting 8251 x64/19,200
        # configuration. This exact false-positive reached a physical bench run.
        invalid_rom = work / "invalid-pit-divisor.bin"
        invalid_rom.write_bytes(bytes((
            0x3E, 0x1F,       # D57 counter 0: LSB, mode 3, BCD
            0xD3, 0x1B,
            0x3E, 0x01,       # invalid periodic divisor 1
            0xD3, 0x18,
            0x3E, 0x5F,       # 8251 x64, 8O1
            0xD3, 0x09,
            0x3E, 0x35,
            0xD3, 0x09,
            0x3E, 0xA5,
            0xD3, 0x08,
            0xDB, 0x09,       # a valid clock would eventually set TxEMPTY
            0xE6, 0x04,
            0xCA, 0x14, 0x00,
            0x76,
        )))
        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_PIT_CLOCK="1",
        )
        invalid = subprocess.run(
            [str(trace), str(invalid_rom), "200000"], cwd=work, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5,
        )
        os.set_blocking(master, False)
        try:
            emitted = os.read(master, 16)
        except BlockingIOError:
            emitted = b""
        finally:
            os.close(master)
            os.close(slave)
        marker = "[USART] invalid D57 mode=3 divisor=1; no periodic baud clock"
        if invalid.returncode != 0 or emitted or marker not in invalid.stderr:
            print(
                "COSIM-USART-OVERRUN: FAIL: invalid mode-3 divisor produced "
                f"bytes={emitted.hex()} rc={invalid.returncode}\n{invalid.stderr}",
                file=sys.stderr,
            )
            return 1
        print(
            "COSIM-USART-PIT-BOUNDARY: PASS "
            "(mode 3 divisor 1 rejected; no false x64/19,200 clock)"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
