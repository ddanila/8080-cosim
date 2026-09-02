#!/usr/bin/env python3
"""Regression for Juku logical-to-native floppy track ordering."""

from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukupoly" / "firmware"))
import build_doom_library as library  # noqa: E402


class JukuDiskLayoutTest(unittest.TestCase):
    def test_replacement_manifest_is_strict_and_hash_checked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jukupoly-replacements.") as name:
            directory = Path(name)
            payload = directory / "track.jps"
            data = bytearray(16)
            data[:4] = b"JPS\2"
            data[4:6] = (16).to_bytes(2, "little")
            data[7] = 3
            payload.write_bytes(data)
            manifest = directory / "manifest.json"
            manifest.write_text(json.dumps({
                "schema": "jukupoly-library-replacements-v1",
                "tracks": [{
                    "pack": "doom1", "local_track": 3,
                    "source_name": "03 The Imp's Song.vgz",
                    "payload": payload.name, "bytes": len(data),
                    "sha256": library.sha256(payload), "capability": 3,
                }],
            }))
            records, capabilities = library.load_replacements(
                manifest, directory,
            )
            self.assertEqual(capabilities, 3)
            self.assertEqual(records[("doom1", 3)]["data"], bytes(data))
            document = json.loads(manifest.read_text())
            document["tracks"][0]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "payload mismatch"):
                library.load_replacements(manifest, directory)

    def test_source_confirmed_articulation_priority_is_scoped(self) -> None:
        self.assertEqual(
            library.ARTICULATION_PRIORITY,
            {("doom1", 4)},
        )

    def test_generic_policy_has_no_song_specific_exceptions(self) -> None:
        for pack, count in library.EXPECTED_TRACKS.items():
            for local_track in range(1, count + 1):
                self.assertEqual(
                    library.track_policy(pack, local_track, True),
                    (set(), False),
                )
        self.assertTrue(library.track_policy("doom1", 1, False)[0])
        self.assertTrue(library.track_policy("doom1", 4, False)[1])

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
