#!/usr/bin/env python3
"""Regression for Juku logical-to-native floppy track ordering."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukupoly" / "firmware"))
import build_doom_library as library  # noqa: E402


class JukuDiskLayoutTest(unittest.TestCase):
    def test_source_confirmed_articulation_priority_is_scoped(self) -> None:
        self.assertEqual(
            library.ARTICULATION_PRIORITY,
            {("doom1", 4)},
        )

    def test_side_major_tracks_become_cylinder_interleaved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jukupoly-layout.") as name:
            source = Path(name) / "logical.cpm"
            native = Path(name) / "native.cpm"
            source.write_bytes(b"".join(
                bytes((track,)) * library.JUKU_TRACK_BYTES
                for track in range(library.JUKU_LOGICAL_TRACKS)
            ))
            library.logical_to_native(source, native)
            image = native.read_bytes()
            self.assertEqual(len(image), library.JUKU_DISK_BYTES)
            for logical_track in range(library.JUKU_LOGICAL_TRACKS):
                physical_track = (
                    (logical_track % 80) * 2 + logical_track // 80
                )
                offset = physical_track * library.JUKU_TRACK_BYTES
                self.assertEqual(
                    image[offset:offset + library.JUKU_TRACK_BYTES],
                    bytes((logical_track,)) * library.JUKU_TRACK_BYTES,
                )


if __name__ == "__main__":
    unittest.main()
