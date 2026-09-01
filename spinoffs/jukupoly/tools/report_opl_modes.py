#!/usr/bin/env python3
"""Report OPL3 new-mode, four-operator, and hardware-rhythm pack use."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
DEFAULT_REPORT = ROOT / "spinoffs" / "jukupoly" / "OPL-M7-MODES.json"
KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def track_record(name: str, payload: bytes) -> dict:
    data = gzip.decompress(payload)
    info, writes = vgz.parse_vgm(data)
    opl3 = False
    four_mask = 0
    rhythm = False
    previous_sample = 0
    opl3_samples = 0
    four_samples = 0
    rhythm_samples = 0
    opl3_enable_writes = 0
    nonzero_four_writes = 0
    rhythm_enable_writes = 0
    maximum_four_pairs = 0
    for write in writes:
        elapsed = write.sample - previous_sample
        opl3_samples += elapsed if opl3 else 0
        four_samples += elapsed if four_mask else 0
        rhythm_samples += elapsed if rhythm else 0
        previous_sample = write.sample
        if write.bank == 1 and write.register == 0x05:
            opl3 = bool(write.value & 0x01)
            opl3_enable_writes += int(opl3)
        elif write.bank == 1 and write.register == 0x04:
            four_mask = write.value & 0x3F
            nonzero_four_writes += int(bool(four_mask))
            maximum_four_pairs = max(maximum_four_pairs, four_mask.bit_count())
        elif write.bank == 0 and write.register == 0xBD:
            rhythm = bool(write.value & 0x20)
            rhythm_enable_writes += int(rhythm)
    elapsed = info.total_samples - previous_sample
    opl3_samples += elapsed if opl3 else 0
    four_samples += elapsed if four_mask else 0
    rhythm_samples += elapsed if rhythm else 0
    return {
        "name": name,
        "compressed_sha256": hashlib.sha256(payload).hexdigest(),
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "chip": info.chip,
        "banks": info.banks,
        "duration_samples": info.total_samples,
        "opl3_enable_writes": opl3_enable_writes,
        "opl3_enabled_samples": opl3_samples,
        "nonzero_four_operator_writes": nonzero_four_writes,
        "four_operator_enabled_samples": four_samples,
        "maximum_enabled_four_operator_pairs": maximum_four_pairs,
        "rhythm_enable_writes": rhythm_enable_writes,
        "rhythm_enabled_samples": rhythm_samples,
    }


def generate(archives: list[Path]) -> dict:
    archive_records = []
    for path in archives:
        payload = path.read_bytes()
        archive_hash = hashlib.sha256(payload).hexdigest()
        pack = KNOWN_PACKS.get(archive_hash)
        if pack is None:
            raise ValueError(f"unrecognized archive hash: {path}")
        with zipfile.ZipFile(path) as source:
            names = sorted(
                name for name in source.namelist()
                if name.lower().endswith(".vgz") and "/" not in name
            )
            tracks = [track_record(name, source.read(name)) for name in names]
        archive_records.append({
            "pack": pack, "name": path.name, "sha256": archive_hash,
            "tracks": tracks,
        })
    tracks = [
        track for archive in archive_records for track in archive["tracks"]
    ]
    result = {
        "schema": "jukupoly-opl-m7-mode-audit-v1",
        "policy": (
            "exact timed register-state audit; absence supports no-demand "
            "stopping points, not a general claim that Juku emulates modes"
        ),
        "archives": archive_records,
        "totals": {
            "tracks": len(tracks),
            "opl3_tracks": sum(item["opl3_enabled_samples"] > 0 for item in tracks),
            "four_operator_tracks": sum(
                item["four_operator_enabled_samples"] > 0 for item in tracks
            ),
            "hardware_rhythm_tracks": sum(
                item["rhythm_enabled_samples"] > 0 for item in tracks
            ),
            "four_operator_enabled_samples": sum(
                item["four_operator_enabled_samples"] for item in tracks
            ),
            "rhythm_enabled_samples": sum(
                item["rhythm_enabled_samples"] for item in tracks
            ),
        },
    }
    result["report_sha256"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate([path.resolve() for path in args.archives])
    except (OSError, ValueError, zipfile.BadZipFile, vgz.VgmError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = args.output.resolve()
    if args.check:
        if output.read_text() != rendered:
            raise SystemExit(f"{output} is missing or stale")
        action = "checked"
    else:
        output.write_text(rendered)
        action = "wrote"
    totals = result["totals"]
    print(
        f"JUKUPOLY-M7-MODES: {action} {output} tracks={totals['tracks']} "
        f"four-op={totals['four_operator_tracks']} "
        f"rhythm={totals['hardware_rhythm_tracks']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
