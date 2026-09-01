#!/usr/bin/env python3
"""Report direct versus timbre-only AM evidence across OPL pack archives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import build_doom_library as doom_library  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402


KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def am_path(signature: tuple[int, ...]) -> str:
    """Classify AM from the two-operator patch and connection bits."""
    modulator_am = bool(signature[0] & 0x80)
    carrier_am = bool(signature[4] & 0x80)
    additive = bool(signature[10] & 1)
    if carrier_am or additive and modulator_am:
        return "direct"
    if modulator_am:
        return "fm_modulator_only"
    return "none"


def analyze_track(name: str, payload: bytes, overrides: set[str]) -> dict:
    data = gzip.decompress(payload)
    info, writes = vgz.parse_vgm(data)
    events, counts = vgz.key_events(writes, info)
    melodic = vgz.melodic_signatures(events, counts)
    signatures = {vgz.signature_id(item): item for item in counts}
    unknown = sorted(overrides - signatures.keys())
    if unknown:
        raise ValueError(f"{name}: unknown melodic overrides: {unknown}")
    melodic.update(signatures[item] for item in overrides)
    keyons = Counter(am_path(event.signature)
                     for event in events if event.signature in melodic)
    melodic_signatures = {event.signature for event in events
                          if event.signature in melodic}
    signature_paths = Counter(am_path(item) for item in melodic_signatures)
    return {
        "name": name,
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "melodic_keyons": sum(keyons.values()),
        "direct_am_keyons": keyons["direct"],
        "fm_modulator_only_am_keyons": keyons["fm_modulator_only"],
        "no_am_keyons": keyons["none"],
        "melodic_signatures": len(melodic_signatures),
        "direct_am_signatures": signature_paths["direct"],
        "fm_modulator_only_am_signatures": signature_paths[
            "fm_modulator_only"
        ],
    }


def analyze_archive(path: Path) -> dict:
    payload = path.read_bytes()
    archive_sha = hashlib.sha256(payload).hexdigest()
    pack = KNOWN_PACKS.get(archive_sha)
    with zipfile.ZipFile(path) as archive:
        names = sorted(name for name in archive.namelist()
                       if name.lower().endswith(".vgz"))
        tracks = []
        for number, name in enumerate(names, 1):
            overrides = doom_library.MELODIC_OVERRIDES.get(
                (pack, number), set(),
            ) if pack is not None else set()
            tracks.append(analyze_track(name, archive.read(name), overrides))
    return {
        "name": path.name,
        "sha256": archive_sha,
        "known_policy_pack": pack,
        "tracks": tracks,
    }


def report(paths: list[Path]) -> dict:
    archives = [analyze_archive(path) for path in paths]
    tracks = [track for archive in archives for track in archive["tracks"]]
    fields = (
        "melodic_keyons", "direct_am_keyons",
        "fm_modulator_only_am_keyons", "no_am_keyons",
        "melodic_signatures", "direct_am_signatures",
        "fm_modulator_only_am_signatures",
    )
    totals = {"tracks": len(tracks)}
    totals.update({field: sum(track[field] for track in tracks)
                   for field in fields})
    totals["tracks_with_direct_am"] = sum(
        track["direct_am_keyons"] > 0 for track in tracks
    )
    totals["tracks_with_fm_modulator_only_am"] = sum(
        track["fm_modulator_only_am_keyons"] > 0 for track in tracks
    )
    result = {
        "schema": "jukupoly-opl-tremolo-pack-report-v1",
        "policy": (
            "AM on the carrier or an additive modulator is direct amplitude "
            "evidence; AM only on an FM modulator is timbre-only and cannot "
            "enable Juku volume tremolo without separate oracle evidence"
        ),
        "archives": archives,
        "totals": totals,
    }
    result["report_sha256"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = report(args.archives)
    except (OSError, ValueError, zipfile.BadZipFile, vgz.VgmError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)
    totals = result["totals"]
    print(
        "JUKUPOLY-OPL-TREMOLO-REPORT: PASS "
        f"tracks={totals['tracks']} direct={totals['direct_am_keyons']} "
        f"indirect={totals['fm_modulator_only_am_keyons']} "
        f"sha256={result['report_sha256']}",
        file=sys.stderr if args.output is None else sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
