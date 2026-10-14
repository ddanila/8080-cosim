#!/usr/bin/env python3
"""Fast host boundary checks, independent of the firmware emitter/cosim."""

import os
from pathlib import Path
import pty
import sys
import termios
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spinoffs/jukuravi"))
import host
import protocol


class TransportContractTests(unittest.TestCase):
    def test_pinned_wire_bytes_and_every_split(self):
        wire = bytes.fromhex("a55a25074240007600b756a3")
        self.assertEqual(
            protocol.encode_loader_v2_load(0x42, 0x4000, b"\x76\x00"), wire
        )
        for split in range(len(wire) + 1):
            decoder = protocol.StreamDecoder()
            frames = decoder.feed(wire[:split]) + decoder.feed(wire[split:])
            self.assertEqual(len(frames), 1)
            self.assertEqual(
                protocol.validate_loader_v2_command(frames[0]),
                (0x42, b"\x40\x00\x76\x00"),
            )

    def test_corrupt_frame_noise_and_back_to_back_recovery(self):
        wire = bytes.fromhex("a55a25074240007600b756a3")
        bad = wire[:-1] + bytes([wire[-1] ^ 1])
        decoder = protocol.StreamDecoder()
        frames = []
        for value in b"noise" * 1000 + bad + wire + wire:
            frames.extend(decoder.feed(bytes([value])))
            self.assertLessEqual(len(decoder._buffer), 260)
        self.assertEqual(len(frames), 2)

    def test_serial_open_does_not_pulse_dtr_and_inherited_fd_is_borrowed(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        with patch.object(host, "pulse_nano_dtr") as reset:
            fd, _ = host.open_transport(os.ttyname(slave), None, 2400)
            try:
                attrs = termios.tcgetattr(fd)
                self.assertEqual(attrs[4], termios.B2400)
                self.assertFalse(attrs[2] & (termios.PARENB | termios.CSTOPB))
            finally:
                os.close(fd)
            fd, _ = host.open_transport(None, slave, 2400)
            os.close(fd)
            os.fstat(slave)
            reset.assert_not_called()

    def test_partial_write_and_transient_race_preserve_bytes(self):
        accepted = bytearray()
        results = iter([InterruptedError(), BlockingIOError(), 2, 1])

        def write(fd, data):
            result = next(results)
            if isinstance(result, Exception):
                raise result
            accepted.extend(data[:result])
            return result

        with (
            patch.object(host.select, "select", return_value=([], [7], [])),
            patch.object(host.os, "write", side_effect=write),
        ):
            host.write_all(7, b"abc", host.time.monotonic() + 2)
        self.assertEqual(accepted, b"abc")

    def test_deadline_and_zero_write_fail_without_restarting_transport(self):
        with (
            patch.object(host.time, "monotonic", side_effect=[0, 1, 3]),
            patch.object(host.select, "select", return_value=([], [7], [])),
            patch.object(host.os, "write", return_value=1),
        ):
            with self.assertRaisesRegex(host.SessionError, "timeout"):
                host.write_all(7, b"abc", 2)
        with (
            patch.object(host.select, "select", return_value=([], [7], [])),
            patch.object(
                host.os, "write", side_effect=[0, AssertionError("retried zero write")]
            ),
        ):
            with self.assertRaises(host.SessionError):
                host.write_all(7, b"x", host.time.monotonic() + 2)


if __name__ == "__main__":
    unittest.main()
