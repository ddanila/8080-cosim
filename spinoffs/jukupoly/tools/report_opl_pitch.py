#!/usr/bin/env python3
"""Report representable vibrato paths and held-key pitch writes in OPL packs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import build_doom_library as doom_library  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_vibrato  # noqa: E402


KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}


@dataclass(frozen=True)
class HeldPitchChange:
    sample: int
    bank: int
    channel: int
    before_code: int
    after_code: int
    cents: float
    signature: tuple[int, ...]


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def vibrato_path(signature: tuple[int, ...]) -> str:
    """Classify whether operator VIB can map truthfully to one pulse voice."""
    modulator = bool(signature[0] & 0x40)
    carrier = bool(signature[4] & 0x40)
    additive = bool(signature[10] & 1)
    if modulator and carrier or carrier and not additive:
        return "direct_common_pitch"
    if additive and modulator != carrier:
        return "additive_partial_pitch"
    if modulator:
        return "fm_modulator_only"
    return "none"


def pitch_code(registers: list[list[int]], bank: int, channel: int) -> int:
    low = registers[bank][0xA0 + channel]
    high = registers[bank][0xB0 + channel]
    return (low | (high & 3) << 8) << ((high >> 2) & 7)


def held_pitch_changes(writes: list[vgz.RegisterWrite], banks: int
                       ) -> tuple[list[HeldPitchChange], int]:
    """Coalesce changed A0/B0 writes at one timestamp while key stays held."""
    registers = [[0] * 256 for _ in range(2)]
    active: dict[tuple[int, int], tuple[int, ...]] = {}
    raw_changes = 0
    pending: dict[tuple[int, int, int], list[object]] = {}

    for write in writes:
        is_a = 0xA0 <= write.register <= 0xA8
        is_b = 0xB0 <= write.register <= 0xB8
        if write.bank >= banks:
            raise ValueError("write uses absent OPL bank")
        if is_a or is_b:
            channel = write.register & 0x0F
            key = write.bank, channel
            before_key = bool(registers[write.bank][0xB0 + channel] & 0x20)
            before_code = pitch_code(registers, write.bank, channel)
        registers[write.bank][write.register] = write.value
        if not (is_a or is_b):
            continue

        after_key = bool(registers[write.bank][0xB0 + channel] & 0x20)
        after_code = pitch_code(registers, write.bank, channel)
        if not before_key and after_key:
            active[key] = vgz.instrument_signature(
                registers, write.bank, channel,
            )
            continue
        if before_key and not after_key:
            active.pop(key, None)
            continue
        if not (before_key and after_key and before_code != after_code):
            continue

        signature = active.get(key)
        if signature is None:
            raise ValueError("held pitch write has no active signature")
        raw_changes += 1
        event_key = write.sample, write.bank, channel
        if event_key not in pending:
            pending[event_key] = [before_code, after_code, signature]
        else:
            pending[event_key][1] = after_code

    result = []
    for (sample, bank, channel), (before, after, signature) in pending.items():
        if before <= 0 or after <= 0 or before == after:
            continue
        result.append(HeldPitchChange(
            sample=sample, bank=bank, channel=channel,
            before_code=int(before), after_code=int(after),
            cents=1200.0 * math.log2(int(after) / int(before)),
            signature=signature,
        ))
    result.sort(key=lambda item: (item.sample, item.bank, item.channel))
    return result, raw_changes


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

    keyed_paths = Counter(
        vibrato_path(event.signature)
        for event in events if event.signature in melodic
    )
    signature_paths = Counter(
        vibrato_path(signature) for signature in melodic
    )
    changes, raw_changes = held_pitch_changes(writes, info.banks)
    melodic_changes = [item for item in changes if item.signature in melodic]
    magnitudes = [abs(item.cents) for item in melodic_changes]
    return {
        "name": name,
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "melodic_keyons": sum(keyed_paths.values()),
        "vibrato_keyons": dict(sorted(keyed_paths.items())),
        "vibrato_signatures": dict(sorted(signature_paths.items())),
        "held_pitch": {
            "raw_changed_writes_all_channels": raw_changes,
            "coalesced_events_all_channels": len(changes),
            "coalesced_events_melodic": len(melodic_changes),
            "up_events_melodic": sum(item.cents > 0 for item in melodic_changes),
            "down_events_melodic": sum(item.cents < 0 for item in melodic_changes),
            "under_5_cent_events_melodic": sum(
                value < 5 for value in magnitudes
            ),
            "5_to_50_cent_events_melodic": sum(
                5 <= value < 50 for value in magnitudes
            ),
            "at_least_50_cent_events_melodic": sum(
                value >= 50 for value in magnitudes
            ),
            "maximum_absolute_cents_melodic": (
                round(max(magnitudes), 6) if magnitudes else 0.0
            ),
        },
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
            tracks.append(analyze_track(
                name, archive.read(name), overrides,
            ))
    return {
        "name": path.name,
        "sha256": archive_sha,
        "known_policy_pack": pack,
        "tracks": tracks,
    }


def report(paths: list[Path]) -> dict:
    archives = [analyze_archive(path) for path in paths]
    tracks = [track for archive in archives for track in archive["tracks"]]
    path_names = (
        "direct_common_pitch", "additive_partial_pitch",
        "fm_modulator_only", "none",
    )
    held_names = (
        "raw_changed_writes_all_channels", "coalesced_events_all_channels",
        "coalesced_events_melodic", "up_events_melodic",
        "down_events_melodic", "under_5_cent_events_melodic",
        "5_to_50_cent_events_melodic", "at_least_50_cent_events_melodic",
    )
    totals = {
        "tracks": len(tracks),
        "melodic_keyons": sum(track["melodic_keyons"] for track in tracks),
        "vibrato_keyons": {
            name: sum(track["vibrato_keyons"].get(name, 0) for track in tracks)
            for name in path_names
        },
        "vibrato_signatures": {
            name: sum(track["vibrato_signatures"].get(name, 0)
                      for track in tracks)
            for name in path_names
        },
        "held_pitch": {
            name: sum(track["held_pitch"][name] for track in tracks)
            for name in held_names
        },
    }
    totals["tracks_with_direct_vibrato"] = sum(
        track["vibrato_keyons"].get("direct_common_pitch", 0) > 0
        for track in tracks
    )
    totals["tracks_with_melodic_held_pitch"] = sum(
        track["held_pitch"]["coalesced_events_melodic"] > 0
        for track in tracks
    )
    totals["held_pitch"]["maximum_absolute_cents_melodic"] = max(
        (track["held_pitch"]["maximum_absolute_cents_melodic"]
         for track in tracks), default=0.0,
    )
    result = {
        "schema": "jukupoly-opl-pitch-pack-report-v1",
        "policy": (
            "target vibrato is eligible only when carrier pitch is direct and "
            "not mixed with an unmodulated additive operator; FM-modulator-only "
            "VIB is timbre-only, and one-sided additive VIB is partial pitch"
        ),
        "source_vibrato": {
            "shape": "Nuked eight-step 0,+half,+full,+half,0,-half,-full,-half",
            "doom_opl_clock_hz": opl_vibrato.DOOM_OPL_CLOCK_HZ,
            "opl_divider": opl_vibrato.DOOM_OPL_DIVIDER,
            "clock_derived_lfo_hz": round(opl_vibrato.lfo_hz(), 9),
            "target_50hz_phase_increment": opl_vibrato.PHASE_INCREMENT,
        },
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
        "JUKUPOLY-OPL-PITCH-REPORT: PASS "
        f"tracks={totals['tracks']} "
        f"direct={totals['vibrato_keyons']['direct_common_pitch']} "
        f"held={totals['held_pitch']['coalesced_events_melodic']} "
        f"sha256={result['report_sha256']}",
        file=sys.stderr if args.output is None else sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
