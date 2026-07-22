"""Helpers for photo-evidence guards that also run without Git LFS objects.

The generic CI job does not materialize every ``ref/photos/**/*.jpg`` object.
In that environment Git leaves a pointer whose ``oid sha256`` is the content
hash, so evidence guards can still prove byte identity while skipping checks
that require the JPEG payload itself.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path


LFS_HEADER = b"version https://git-lfs.github.com/spec/v1\n"


def photo_sha256(path: Path) -> tuple[str, bool]:
    """Return ``(digest, is_lfs_pointer)`` for a photo or Git LFS pointer."""
    payload = path.read_bytes()
    if payload.startswith(LFS_HEADER):
        match = re.search(
            r"^oid sha256:([0-9a-f]{64})$",
            payload.decode("ascii"),
            re.MULTILINE,
        )
        return (match.group(1) if match else "invalid-lfs-pointer"), True
    return hashlib.sha256(payload).hexdigest(), False


def jpeg_dimensions(path: Path) -> list[int]:
    """Read JPEG SOF dimensions without optional image-library dependencies."""
    data = path.read_bytes()
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            return [width, height]
        offset += length
    raise SystemExit(f"cannot read JPEG dimensions: {path}")
