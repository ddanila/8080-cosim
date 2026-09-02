#!/usr/bin/env python3
"""Audit the Imp intro envelope against isolated pinned-Nuked PCM.

This is intentionally independent of the post-EG attenuation trace used by
the converter's fitter.  The OPL PCM supplies relative envelope shape while
the already documented attenuation policy supplies only the absolute 4-bit
peak.  A candidate therefore cannot pass merely by agreeing with the model
which selected it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_SOURCE = (
    ROOT / "out" / "jukupoly-m7-pack-scan" / "sources" /
    "doom1-03 The Imp's Song.vgz"
)
DEFAULT_OUTPUT = SPINOFF / "OPL-IMP-TARGET-SHAPE-M7.json"
EXPECTED_COMPRESSED_SHA256 = (
    "1d3670f1bd3ccccf6ecd510926101ba6c24fc466c38d37277edfe57c538839cc"
)
EXPECTED_VGM_SHA256 = (
    "601c83652b950d8f2978baef35b8fb7db1aba8d5d2e30decd2535dccf56adb16"
)
OLD_REART = FIRMWARE / "jukupoly-imp-30s-rearticulation-m7.json"
NEW_REART = (
    FIRMWARE / "jukupoly-imp-30s-rearticulation-target-shape-m7.json"
)
OLD_DETUNED = FIRMWARE / "jukupoly-imp-30s-detuned-m7.json"
NEW_DETUNED = FIRMWARE / "jukupoly-imp-30s-detuned-target-shape-m7.json"
sys.path.insert(0, str(FIRMWARE))

import opl_envelope  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_oracle  # noqa: E402
import opl_voices  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_score(path: Path) -> dict:
    score = json.loads(path.read_text())
    source = score["source"]
    if (source["compressed_sha256"] != EXPECTED_COMPRESSED_SHA256 or
            source["vgm_sha256"] != EXPECTED_VGM_SHA256):
        raise ValueError(f"score identifies a different source: {path}")
    return score


def render_isolated(
        writes: list, channels: tuple[int, ...], total_samples: int,
        oracle: Path, directory: Path, label: str,
) -> tuple[list[tuple[int, int]], list[opl_oracle.OracleChannelProbe], dict]:
    selected = [
        write for write in writes if write.sample < total_samples and any(
            opl_oracle.channel_write(write, 0, channel)
            for channel in channels
        )
    ]
    stream = directory / f"{label}.jop"
    pcm_path = directory / f"{label}.s16le"
    probes_path = directory / f"{label}.csv"
    count = opl_oracle.write_event_stream(
        stream, selected, total_samples,
    )
    completed = subprocess.run(
        [str(oracle), str(stream), str(pcm_path), str(probes_path), "all"],
        check=True, text=True, stdout=subprocess.PIPE,
    )
    return (
        opl_oracle.read_pcm(pcm_path),
        opl_oracle.read_channel_probes(probes_path),
        {
            "channels": list(channels),
            "samples": total_samples,
            "writes": count,
            "pcm_sha256": sha256(pcm_path),
            "oracle_result": completed.stdout.strip(),
        },
    )


def probe_table(
        probes: list[opl_oracle.OracleChannelProbe],
) -> dict[tuple[int, int], opl_oracle.OracleProbe]:
    return {
        (item.probe.sample // opl_voices.ANALYSIS_FRAME, item.channel):
        item.probe
        for item in probes
        if item.probe.sample % opl_voices.ANALYSIS_FRAME == 0
    }


def absolute_peak(
        probes: list[opl_oracle.OracleChannelProbe],
        channels: tuple[int, ...], frames: int,
) -> int:
    table = probe_table(probes)
    levels = []
    for frame in range(frames):
        amplitude = 0.0
        for channel in channels:
            probe = table[(frame, channel)]
            amplitude += opl_envelope.opl_channel_amplitude(
                probe.modulator_output_attenuation,
                probe.carrier_output_attenuation,
                probe.connection,
            )
        levels.append(round(15 * min(1.0, amplitude)))
    return max(levels)


def first_packet(score: dict, logical_note: int) -> tuple[dict, int]:
    fit = score["conversion"]["enhanced_envelope_fit"]
    note = next(
        item for item in fit["notes"]
        if item["logical_note"] == logical_note
    )
    boundary = min(
        (item["frame_offset"] for item in note["articulation_packets"]),
        default=note["reference_frames"],
    )
    return note["packet"], boundary


def member_packet(score: dict, phase_step: int) -> tuple[dict, int, tuple[int, ...]]:
    fit = score["conversion"]["enhanced_envelope_fit"]
    episode = next(
        item for item in fit["detuned_layer_analysis"]["episodes"]
        if item["start_frame"] == 0
    )
    member = next(
        item for item in episode["members"]
        if item["phase_step"] == phase_step
    )
    boundary = min(
        (item["frame_offset"] for item in member["articulation_packets"]),
        default=member["reference_frames"],
    )
    return (
        member["packet"], boundary,
        tuple(member.get("source_segments", [member["segment"]])),
    )


def compare(
        pcm: list[tuple[int, int]], frames: int, peak: int,
        old_packet: dict, new_packet: dict,
) -> dict:
    reference = opl_envelope.quantize_isolated_pcm(
        pcm, start_sample=0, frames=frames, peak_level=peak,
        samples_per_frame=opl_voices.ANALYSIS_FRAME,
    )

    def measurement(packet: dict) -> dict:
        predicted = opl_envelope.simulate_envelope(
            frames, key_off_frame=None, counter_at_onset=1, **packet,
        )
        errors = tuple(
            expected - actual
            for expected, actual in zip(predicted, reference)
        )
        return {
            "packet": packet,
            "absolute_error": sum(abs(value) for value in errors),
            "mean_absolute_error": (
                sum(abs(value) for value in errors) / frames
            ),
            "squared_error": sum(value * value for value in errors),
            "maximum_error": max(abs(value) for value in errors),
        }

    old = measurement(old_packet)
    new = measurement(new_packet)
    return {
        "frames": frames,
        "seconds": frames / 50,
        "absolute_peak_level": peak,
        "reference_levels": list(reference),
        "source_semantic_target": old,
        "target_shape_candidate": new,
        "improvement": {
            "absolute_error": (
                old["absolute_error"] - new["absolute_error"]
            ),
            "mean_absolute_error_fraction": (
                (old["mean_absolute_error"] - new["mean_absolute_error"]) /
                old["mean_absolute_error"]
            ),
            "squared_error": old["squared_error"] - new["squared_error"],
        },
        "gates": {
            "mean_absolute_error_reduced": (
                new["mean_absolute_error"] < old["mean_absolute_error"]
            ),
            "squared_error_reduced": (
                new["squared_error"] < old["squared_error"]
            ),
            "maximum_error_not_increased": (
                new["maximum_error"] <= old["maximum_error"]
            ),
            "candidate_uses_existing_automatic_release": (
                old_packet["sustain_while_keyed"] is True and
                new_packet["sustain_while_keyed"] is False
            ),
        },
    }


def generate(source: Path, oracle: Path) -> dict:
    if not source.is_file() or sha256(source) != EXPECTED_COMPRESSED_SHA256:
        raise ValueError(f"missing or hash-mismatched Imp source: {source}")
    if not oracle.is_file():
        raise ValueError(f"OPL oracle is missing: {oracle}")
    data, compressed_hash = vgz.decode_source(source)
    if (compressed_hash != EXPECTED_COMPRESSED_SHA256 or
            hashlib.sha256(data).hexdigest() != EXPECTED_VGM_SHA256):
        raise ValueError("decoded Imp source hash mismatch")
    info, writes = vgz.parse_vgm(data)
    segments = opl_voices.reconstruct_segments(
        writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    opening = {segment.identifier: segment for segment in segments[:4]}
    if any(
            identifier not in opening or opening[identifier].bank != 0 or
            opening[identifier].channel != identifier or
            opening[identifier].start != 0
            for identifier in range(4)):
        raise ValueError("unexpected Imp opening segment layout")

    old_reart = load_score(OLD_REART)
    new_reart = load_score(NEW_REART)
    old_detuned = load_score(OLD_DETUNED)
    new_detuned = load_score(NEW_DETUNED)
    old_merged, old_merged_frames = first_packet(old_reart, 0)
    new_merged, new_merged_frames = first_packet(new_reart, 0)
    if old_merged_frames != new_merged_frames:
        raise ValueError("merged candidate articulation boundary changed")
    old_episode = old_detuned["conversion"]["enhanced_envelope_fit"][
        "detuned_layer_analysis"
    ]["episodes"][0]
    # Audit the two energy-dominant target voices.  Equal target phase steps
    # may now represent a host-combined group of source OPL channels.
    dominant = sorted(
        old_episode["members"],
        key=lambda item: (-item["reference_energy"], item["phase_step"]),
    )[:2]
    member_inputs = []
    for old_member in dominant:
        phase_step = old_member["phase_step"]
        old_packet, old_frames, old_segments = member_packet(
            old_detuned, phase_step,
        )
        new_packet, new_frames, new_segments = member_packet(
            new_detuned, phase_step,
        )
        if old_frames != new_frames:
            raise ValueError("detuned member articulation boundary changed")
        if old_segments != new_segments:
            raise ValueError("detuned member source grouping changed")
        member_inputs.append((
            phase_step, old_segments, old_packet, new_packet, old_frames,
        ))

    maximum_frames = max(
        old_merged_frames, *(item[4] for item in member_inputs),
    )
    total_samples = maximum_frames * opl_voices.ANALYSIS_FRAME
    streams = {}
    comparisons = {}
    with tempfile.TemporaryDirectory(
            prefix="jukupoly-imp-target-shape.") as name:
        directory = Path(name)
        pcm, probes, evidence = render_isolated(
            writes, (0, 1, 2, 3), total_samples, oracle, directory,
            "merged-0-3",
        )
        streams["merged_channels_0_3"] = evidence
        peak = absolute_peak(probes, (0, 1, 2, 3), old_merged_frames)
        comparisons["merged_logical_lead"] = compare(
            pcm, old_merged_frames, peak, old_merged, new_merged,
        )
        for phase_step, segment_group, old_packet, new_packet, frames in member_inputs:
            channels = tuple(opening[segment].channel
                             for segment in segment_group)
            pcm, probes, evidence = render_isolated(
                writes, channels, total_samples, oracle, directory,
                f"step-{phase_step}-channels-" + "-".join(
                    str(channel) for channel in channels
                ),
            )
            label = f"detuned_step_{phase_step}"
            streams[label] = {
                **evidence, "source_segments": list(segment_group),
                "phase_step": phase_step,
            }
            peak = absolute_peak(probes, channels, frames)
            comparisons[label] = compare(
                pcm, frames, peak, old_packet, new_packet,
            )

    gates = {
        "all_pcm_comparisons_pass": all(
            all(item["gates"].values()) for item in comparisons.values()
        ),
        "candidate_scores_enable_target_shape": all(
            score["conversion"]["enhanced_envelope_fit"][
                "target_shape_fit"
            ]["enabled"]
            for score in (new_reart, new_detuned)
        ),
        "source_scores_do_not_enable_target_shape": all(
            not score["conversion"]["enhanced_envelope_fit"].get(
                "target_shape_fit", {"enabled": False}
            )["enabled"]
            for score in (old_reart, old_detuned)
        ),
    }
    return {
        "schema": "jukupoly-imp-target-shape-pcm-audit-v1",
        "scope": (
            "first independently articulated Imp intro lobe; exact isolated "
            "Nuked-OPL PCM/RMS cross-check of converter attenuation fits, "
            "including equal-phase source-member groups"
        ),
        "source": {
            "name": source.name,
            "compressed_sha256": EXPECTED_COMPRESSED_SHA256,
            "vgm_sha256": EXPECTED_VGM_SHA256,
            "chip": info.chip,
            "chip_clock_hz": info.clock,
        },
        "oracle": {"path_name": oracle.name, "sha256": sha256(oracle)},
        "scores": {
            "source_semantic_rearticulation": {
                "path": OLD_REART.name, "sha256": sha256(OLD_REART),
            },
            "target_shape_rearticulation": {
                "path": NEW_REART.name, "sha256": sha256(NEW_REART),
            },
            "source_semantic_detuned": {
                "path": OLD_DETUNED.name, "sha256": sha256(OLD_DETUNED),
            },
            "target_shape_detuned": {
                "path": NEW_DETUNED.name, "sha256": sha256(NEW_DETUNED),
            },
        },
        "isolated_streams": streams,
        "comparisons": comparisons,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--opl-oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.source.resolve(), args.opl_oracle.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    if not all(result["gates"].values()):
        failed = sorted(
            key for key, value in result["gates"].items() if not value
        )
        raise SystemExit(f"failed audit gates: {', '.join(failed)}")
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = args.output.resolve()
    if args.check:
        if output.read_text() != rendered:
            raise SystemExit(f"{output} is missing or stale")
        action = "checked"
    else:
        output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-IMP-TARGET-SHAPE: {action} {output} "
        + " ".join(
            f"{name}={item['source_semantic_target']['mean_absolute_error']:.3f}"
            f"->{item['target_shape_candidate']['mean_absolute_error']:.3f}"
            for name, item in result["comparisons"].items()
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
