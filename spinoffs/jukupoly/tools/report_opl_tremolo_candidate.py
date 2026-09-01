#!/usr/bin/env python3
"""Reproduce one selected logical-note joint envelope+tremolo candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402
import opl_enhanced  # noqa: E402
import opl_oracle  # noqa: E402
import opl_tremolo  # noqa: E402
import opl_voices  # noqa: E402


def generate(source: Path, score_path: Path, probes_path: Path,
             logical_note: int) -> dict:
    data, _compressed = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    score = json.loads(score_path.read_text())
    frames = score["conversion"]["duration_frames"]
    total_samples = min(info.total_samples, frames * opl_voices.ANALYSIS_FRAME)
    info.total_samples = total_samples
    writes = [write for write in writes if write.sample < total_samples]
    segments = opl_voices.reconstruct_segments(
        writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    notes = opl_voices.group_layers(
        segments, opl_voices.candidate_relations(segments),
    )
    by_identifier = {note.identifier: note for note in notes}
    if logical_note not in by_identifier:
        raise ValueError(f"logical note does not exist: {logical_note}")
    measurements = {
        item["logical_note"]: item
        for item in score["conversion"]["enhanced_envelope_fit"]["notes"]
    }
    if logical_note not in measurements:
        raise ValueError(f"logical note was not selected: {logical_note}")
    measurement = measurements[logical_note]
    note = by_identifier[logical_note]
    probes = opl_enhanced._probe_table(
        opl_oracle.read_channel_probes(probes_path)
    )
    start = measurement["selected_frame"]
    end = start + measurement["reference_frames"]
    reference = tuple(
        opl_enhanced._logical_level(note, frame, probes)
        for frame in range(start, end)
    )
    relative_key_off = measurement["source_end_frame"] - start
    key_off = (
        relative_key_off if "release" in measurement["directions"] and
        0 <= relative_key_off < len(reference) else None
    )
    changed_frames = 0
    attenuation_levels = 0
    maximum_delta = 0
    for frame in range(start, end):
        changed = False
        frame_delta = 0
        for bank, channel in note.channels:
            probe = probes[(frame, bank * 9 + channel)]
            if not (probe.carrier_am or
                    probe.connection == 1 and probe.modulator_am):
                continue
            without_am, with_am = opl_tremolo.quantized_oracle_am_effect(
                probe.modulator_output_attenuation,
                probe.carrier_output_attenuation,
                probe.connection, probe.modulator_am, probe.carrier_am,
                probe.tremolo_value,
            )
            delta = without_am - with_am
            changed = changed or delta != 0
            frame_delta += delta
        changed_frames += int(changed)
        attenuation_levels += frame_delta
        maximum_delta = max(maximum_delta, frame_delta)

    fit = opl_tremolo.fit_joint_envelope_tremolo(
        reference, start_frame=start, key_off_frame=key_off,
        sustain_while_keyed=note.sustained_envelope,
        counter_at_onset=(start + 1) & 0xFF,
    )
    gates = {
        "source_am_survives_4bit": changed_frames > 0,
        "joint_fit_selects_tremolo": fit.depth_levels > 0,
        "joint_fit_improves_squared_error": (
            fit.squared_error_improvement > 0
        ),
        "significant_directions_preserved": (
            opl_tremolo.opl_envelope.envelope_directions(
                reference, fit.envelope.predicted_levels, key_off,
            )["mismatches"] == 0
        ),
    }
    if not all(gates.values()):
        raise ValueError("candidate gates failed: " + ", ".join(
            key for key, value in gates.items() if not value
        ))
    return {
        "schema": "jukupoly-opl-tremolo-candidate-report-v1",
        "source": {
            "name": source.name,
            "vgm_sha256": hashlib.sha256(data).hexdigest(),
            "score_sha256": hashlib.sha256(score_path.read_bytes()).hexdigest(),
            "probe_sha256": hashlib.sha256(probes_path.read_bytes()).hexdigest(),
        },
        "logical_note": logical_note,
        "selected_frame": start,
        "selected_seconds": start / 50,
        "reference_frames": len(reference),
        "channels": note.channels,
        "source_quantized_am": {
            "changed_frames": changed_frames,
            "attenuation_levels": attenuation_levels,
            "maximum_delta_levels": maximum_delta,
        },
        "baseline_envelope": {
            "packet": fit.baseline_envelope.packet(),
            "squared_error": fit.baseline_envelope.squared_error,
            "mean_absolute_error": (
                fit.baseline_envelope.absolute_error / len(reference)
            ),
            "maximum_error": fit.baseline_envelope.maximum_error,
        },
        "joint_fit": {
            "depth_levels": fit.depth_levels,
            "packet": fit.envelope.packet(),
            "squared_error": fit.envelope.squared_error,
            "squared_error_improvement": fit.squared_error_improvement,
            "improvement_per_frame": (
                fit.squared_error_improvement / len(reference)
            ),
            "mean_absolute_error": fit.envelope.absolute_error / len(reference),
            "maximum_error": fit.envelope.maximum_error,
        },
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("score", type=Path)
    parser.add_argument("probes", type=Path)
    parser.add_argument("logical_note", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = generate(
            args.source, args.score, args.probes, args.logical_note,
        )
    except (OSError, ValueError, vgz.VgmError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)
    print(
        "JUKUPOLY-OPL-TREMOLO-CANDIDATE: PASS "
        f"note={result['logical_note']} "
        f"depth={result['joint_fit']['depth_levels']} "
        f"improvement={result['joint_fit']['squared_error_improvement']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
