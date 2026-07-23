#!/usr/bin/env python3
"""Exercise the cumulative Jukuravi loader through the real cosim PTY."""

from __future__ import annotations

import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "spinoffs" / "jukuravi"),
    str(ROOT / "spinoffs" / "jukuravi" / "firmware"),
]
import build_d2_loader as firmware  # noqa: E402
import protocol  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-D2-LOADER: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


class Session:
    def __init__(self, fd: int) -> None:
        self.fd = fd
        self.raw = bytearray()
        self.frames: list[protocol.Frame] = []
        self.decoder = protocol.StreamDecoder()

    def write(self, data: bytes) -> None:
        view = memoryview(data)
        deadline = time.monotonic() + 5
        while view:
            if time.monotonic() >= deadline:
                fail("timed out writing a host command")
            if not select.select([], [self.fd], [], 0.1)[1]:
                continue
            try:
                count = os.write(self.fd, view)
            except BlockingIOError:
                continue
            view = view[count:]

    def wait_for(
        self, predicate, *, start: int = 0, timeout: float = 30
    ) -> protocol.Frame:
        deadline = time.monotonic() + timeout
        while True:
            for frame in self.frames[start:]:
                if predicate(frame):
                    return frame
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                fail("timed out waiting for loader protocol evidence")
            if not select.select([self.fd], [], [], min(remaining, 0.25))[0]:
                continue
            try:
                data = os.read(self.fd, 4096)
            except BlockingIOError:
                continue
            if not data:
                fail("cosim PTY closed before loader evidence completed")
            self.raw.extend(data)
            self.frames.extend(self.decoder.feed(data))

    def drain(self) -> None:
        while select.select([self.fd], [], [], 0.1)[0]:
            try:
                data = os.read(self.fd, 4096)
            except (BlockingIOError, OSError):
                return
            if not data:
                return
            self.raw.extend(data)
            self.frames.extend(self.decoder.feed(data))

    def transact(self, command: bytes, expected: protocol.Frame) -> None:
        start = len(self.frames)
        self.write(command)
        got = self.wait_for(lambda frame: frame == expected, start=start)
        if got != expected:
            fail(f"loader response differs: {got!r}")


def loader_program() -> bytes:
    # Read and echo one byte through GET/PUT, emit 'B', print a zero-terminated
    # "OK", then return to the loader through its fixed API vector.
    code = bytearray(
        (
            0xCD,
            firmware.LOADER_API_SERIAL_GET & 0xFF,
            firmware.LOADER_API_SERIAL_GET >> 8,
            0xCD,
            firmware.LOADER_API_SERIAL_PUT & 0xFF,
            firmware.LOADER_API_SERIAL_PUT >> 8,
            0x3E,
            0x42,  # MVI A,'B'
            0xCD,
            firmware.LOADER_API_SERIAL_PUT & 0xFF,
            firmware.LOADER_API_SERIAL_PUT >> 8,
            0x21,
            0x20,
            0x40,  # LXI H,4020h
            0xCD,
            firmware.LOADER_API_PRINT & 0xFF,
            firmware.LOADER_API_PRINT >> 8,
            0xC3,
            firmware.LOADER_API_RETURN & 0xFF,
            firmware.LOADER_API_RETURN >> 8,
        )
    )
    code.extend(b"\x00" * (0x20 - len(code)))
    code.extend(b"OK\x00")
    return bytes(code)


def expected_banner(metadata: dict[str, object]) -> protocol.Frame:
    return protocol.Frame(
        protocol.TYPE_BANNER,
        bytes(
            (
                protocol.PROTOCOL_VERSION,
                firmware.ROM_VERSION,
                int(metadata["checksum"]) >> 8,
                int(metadata["checksum"]) & 0xFF,
            )
        ),
    )


def expected_ready() -> protocol.Frame:
    return protocol.Frame(
        protocol.TYPE_LOADER_READY,
        bytes(
            (
                protocol.LOADER_API_VERSION,
                protocol.LOADER_MAX_DATA,
                firmware.LOADER_API_BASE >> 8,
                firmware.LOADER_API_BASE & 0xFF,
            )
        ),
    )


def run_clean(trace: Path, image: bytes, metadata: dict[str, object], root: Path) -> None:
    rom = root / "loader.bin"
    rom.write_bytes(image)
    master, slave = pty.openpty()
    tty.setraw(slave)
    os.set_blocking(master, False)
    env = os.environ.copy()
    env.update(
        {
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
        }
    )
    stdout_path = root / "cosim.stdout"
    stderr_path = root / "cosim.stderr"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "2000000000"],
            cwd=root,
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
    session = Session(master)
    try:
        banner = session.wait_for(
            lambda frame: frame.record_type == protocol.TYPE_BANNER
        )
        if banner != expected_banner(metadata):
            fail(f"loader banner differs: {banner!r}")
        session.write(protocol.encode_frame(protocol.TYPE_ACK, banner.payload))

        ready = expected_ready()
        session.wait_for(lambda frame: frame == ready, timeout=40)
        survey = protocol.decode_ram_survey(session.frames)
        if any(survey.masks):
            fail("clean loader session reported a RAM fault")

        bad_crc = bytearray(protocol.encode_load_frame(0x4000, b"\x00"))
        bad_crc[-1] ^= 0x01
        session.transact(
            bytes(bad_crc),
            protocol.Frame(
                protocol.TYPE_LOADER_ERROR,
                bytes((protocol.LOADER_STATUS_BAD_CRC,)),
            ),
        )
        session.transact(
            protocol.encode_frame(protocol.TYPE_LOAD, b"\x40\x00"),
            protocol.Frame(
                protocol.TYPE_LOAD_RESULT,
                bytes((protocol.LOADER_STATUS_BAD_LENGTH,)),
            ),
        )
        session.transact(
            protocol.encode_load_frame(0xD7FF, b"\x11\x22"),
            protocol.Frame(
                protocol.TYPE_LOAD_RESULT,
                bytes((protocol.LOADER_STATUS_BAD_RANGE,)),
            ),
        )
        session.transact(
            protocol.encode_frame(0x7E, b""),
            protocol.Frame(
                protocol.TYPE_LOADER_ERROR,
                bytes((protocol.LOADER_STATUS_BAD_COMMAND,)),
            ),
        )
        session.transact(
            protocol.encode_run_frame(0xD800),
            protocol.Frame(
                protocol.TYPE_LOADER_ERROR,
                bytes((protocol.LOADER_STATUS_BAD_RANGE,)),
            ),
        )

        program = loader_program()
        session.transact(
            protocol.encode_load_frame(0x4000, program),
            protocol.Frame(
                protocol.TYPE_LOAD_RESULT,
                bytes((protocol.LOADER_STATUS_OK,)),
            ),
        )
        raw_start = len(session.raw)
        frame_start = len(session.frames)
        session.write(protocol.encode_run_frame(0x4000))
        session.wait_for(
            lambda frame: frame == protocol.Frame(protocol.TYPE_RUN_ACK, b""),
            start=frame_start,
        )
        session.write(b"G")
        session.wait_for(lambda frame: frame == ready, start=frame_start)
        if b"GBOK" not in bytes(session.raw[raw_start:]):
            fail("uploaded program did not execute GET/PUT/PRINT APIs")
    finally:
        os.close(master)
        os.close(slave)
        cosim.terminate()
        try:
            cosim.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cosim.kill()
            cosim.wait()


def run_verify_fault(
    trace: Path, image: bytes, metadata: dict[str, object], root: Path
) -> None:
    rom = root / "loader-fault.bin"
    rom.write_bytes(image)
    master, slave = pty.openpty()
    tty.setraw(slave)
    os.set_blocking(master, False)
    env = os.environ.copy()
    env.update(
        {
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
            "JUKU_RAM_FAULT": "4000:01:00",
        }
    )
    with (root / "fault.stdout").open("wb") as stdout, (
        root / "fault.stderr"
    ).open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "2000000000"],
            cwd=root,
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
    session = Session(master)
    try:
        banner = session.wait_for(
            lambda frame: frame.record_type == protocol.TYPE_BANNER
        )
        if banner != expected_banner(metadata):
            fail("fault-session loader banner differs")
        session.write(protocol.encode_frame(protocol.TYPE_ACK, banner.payload))
        session.wait_for(lambda frame: frame == expected_ready(), timeout=40)
        survey = protocol.decode_ram_survey(session.frames)
        if survey.masks[0] & 0x01 == 0:
            fail("injected D84/address-4000 fault was absent from the survey")
        session.transact(
            protocol.encode_load_frame(0x4000, b"\x01"),
            protocol.Frame(
                protocol.TYPE_LOAD_RESULT,
                bytes((protocol.LOADER_STATUS_VERIFY_FAILED,)),
            ),
        )
    finally:
        os.close(master)
        os.close(slave)
        cosim.terminate()
        try:
            cosim.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cosim.kill()
            cosim.wait()


def run_corrupt_guard(
    trace: Path, image: bytes, metadata: dict[str, object], root: Path
) -> None:
    corrupt = bytearray(image)
    corrupt[int(metadata["loader_extension_end"]) - 1] ^= 0x01
    rom = root / "loader-corrupt.bin"
    rom.write_bytes(corrupt)
    master, slave = pty.openpty()
    tty.setraw(slave)
    os.set_blocking(master, False)
    env = os.environ.copy()
    env.update(
        {
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
        }
    )
    stderr_path = root / "corrupt.stderr"
    with (root / "corrupt.stdout").open("wb") as stdout, stderr_path.open(
        "wb"
    ) as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "2000000000"],
            cwd=root,
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
    session = Session(master)
    try:
        banner = session.wait_for(
            lambda frame: frame.record_type == protocol.TYPE_BANNER
        )
        session.write(protocol.encode_frame(protocol.TYPE_ACK, banner.payload))
        session.wait_for(
            lambda frame: frame.record_type == protocol.TYPE_RAM_END, timeout=40
        )
        try:
            returncode = cosim.wait(timeout=15)
        except subprocess.TimeoutExpired:
            fail("corrupt loader extension did not reach the ROM-fail halt")
        session.drain()
        if returncode != 0:
            fail(f"corrupt-extension cosim exited {returncode}")
        if any(
            frame.record_type == protocol.TYPE_LOADER_READY
            for frame in session.frames
        ):
            fail("corrupt loader extension announced READY")
        expected_pc = int(metadata["rom_fail_halt"]) + 1
        if f"stopped pc=0x{expected_pc:04X}" not in stderr_path.read_text():
            fail("corrupt loader extension did not select the ROM-fail halt")
    finally:
        os.close(master)
        os.close(slave)
        if cosim.poll() is None:
            cosim.terminate()
            cosim.wait(timeout=5)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d2-loader.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact loader image is missing", file=sys.stderr)
        return 2

    if len(protocol.encode_load_frame(0x4000, bytes(protocol.LOADER_MAX_DATA))) != 260:
        fail("maximum loader frame length differs")
    for address, data in (
        (-1, b"x"),
        (0x10000, b"x"),
        (0x4000, b""),
        (0x4000, bytes(protocol.LOADER_MAX_DATA + 1)),
    ):
        try:
            protocol.encode_load_frame(address, data)
        except ValueError:
            pass
        else:
            fail("invalid host load request was accepted")
    for address in (-1, 0x10000):
        try:
            protocol.encode_run_frame(address)
        except ValueError:
            pass
        else:
            fail("invalid host run request was accepted")

    with tempfile.TemporaryDirectory(prefix="jukuravi-loader-") as tmp_name:
        root = Path(tmp_name)
        run_clean(trace, image, metadata, root)
        run_verify_fault(trace, image, metadata, root)
        run_corrupt_guard(trace, image, metadata, root)
    print(
        "JUKURAVI-D2-LOADER: PASS "
        "(CRC/range guards; verified load; fixed get/put/print/return APIs; run)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
