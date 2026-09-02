#!/usr/bin/env python3
"""Isolate one OPL logical note and compare it with its Juku reduction.

The source side is rendered from the selected register writes by the pinned
Nuked OPL3 core.  The target side is compiled as a standalone JukuPoly score
and rendered by the cycle-level 8080/PIT model.  All reconstruction, fitting,
quantization, and comparison work is deliberately host-only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import wave
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
ORACLE_SOURCE = SPINOFF / "tools" / "jukupoly_opl_oracle.c"
RENDERER_SOURCE = SPINOFF / "tools" / "render_jukupoly_wav.c"
NUKED = SPINOFF / "external" / "Nuked-OPL3"
PINNED_NUKED_COMMIT = "765ec962e473aeb767e4cba74ffdc8f588ffbfe8"
VGM_RATE = 44_100
ANALYSIS_FRAME = VGM_RATE // 50
WAV_RATE = 48_000
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_enhanced  # noqa: E402
import opl_oracle  # noqa: E402
import opl_voices  # noqa: E402


@dataclass(frozen=True)
class Audio:
    rate: int
    channels: int
    samples: tuple[tuple[int, ...], ...]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        command, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def renderer_run_seconds(output: str) -> float:
    for field in output.split():
        if field.startswith("run=") and field.endswith("s"):
            return float(field[4:-1])
    raise ValueError(f"renderer did not report run duration: {output}")


def build_host_tools(directory: Path) -> tuple[Path, Path]:
    compiler = shutil.which("cc")
    if compiler is None:
        raise OSError("required host C compiler is missing: cc")
    actual = run(["git", "-C", str(NUKED), "rev-parse", "HEAD"])
    if actual != PINNED_NUKED_COMMIT:
        raise ValueError(
            f"Nuked OPL3 is {actual}, expected {PINNED_NUKED_COMMIT}"
        )
    oracle = directory / "jukupoly_opl_oracle"
    renderer = directory / "render_jukupoly_wav"
    run([
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        f"-I{NUKED}", "-o", str(oracle), str(ORACLE_SOURCE),
        str(NUKED / "opl3.c"),
    ])
    run([
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-o", str(renderer), str(RENDERER_SOURCE),
        str(ROOT / "cosim" / "i8080.c"), "-lm",
    ])
    return oracle, renderer


def select_logical_note(
        notes: list[opl_voices.LogicalNote], *, identifier: int | None,
        at_seconds: float, midi_note: int | None,
) -> opl_voices.LogicalNote:
    if identifier is not None:
        matches = [note for note in notes if note.identifier == identifier]
    else:
        sample = round(at_seconds * VGM_RATE)
        matches = [note for note in notes if note.start <= sample < note.end]
        if midi_note is not None:
            matches = [note for note in matches
                       if note.initial_pitch is not None and
                       round(note.initial_pitch) == midi_note]
    if len(matches) != 1:
        summary = ", ".join(
            f"{note.identifier}:midi="
            f"{None if note.initial_pitch is None else round(note.initial_pitch)}"
            f"@{note.start / VGM_RATE:.3f}-{note.end / VGM_RATE:.3f}s"
            for note in matches[:12]
        ) or "none"
        raise ValueError(
            f"logical-note selection matched {len(matches)} notes ({summary}); "
            "specify --logical-note or narrow with --midi-note"
        )
    return matches[0]


def frame_rows(frames: int) -> list[dict]:
    rows = []
    while frames:
        count = min(255, frames)
        rows.append({"frames": count})
        frames -= count
    return rows


def isolated_allocation(note: opl_voices.LogicalNote, frames: int) -> dict:
    start = opl_voices.analysis_frame(note.start)
    end = max(start + 1, opl_voices.analysis_frame(note.end))
    end = min(frames, end)
    selected = {
        "logical_note": note.identifier,
        "logical_voice": 0,
        "midi_note": round(note.initial_pitch),
    }
    decisions = [{"frame": start, "selected": [selected]}]
    if end < frames:
        decisions.append({"frame": end, "selected": []})
    return {
        "schema": "jukupoly-opl-three-voice-allocation-v1",
        "source_onsets": 1,
        "protected_onsets": 0,
        "retained_onsets": 1,
        "gained_onsets": 1,
        "missed_protected_onsets": 0,
        "frames": decisions,
    }


def pcm_to_wav(pcm: Path, output: Path, rate: int = VGM_RATE) -> None:
    payload = pcm.read_bytes()
    if len(payload) % 4:
        raise ValueError("oracle PCM is not stereo signed-16 little-endian")
    with wave.open(str(output), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(payload)


def read_wav(path: Path) -> Audio:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        rate = source.getframerate()
        frames = source.getnframes()
        if width != 2 or channels not in (1, 2):
            raise ValueError(f"unsupported WAV shape: {channels}ch/{width * 8}bit")
        values = struct.unpack(f"<{frames * channels}h", source.readframes(frames))
    return Audio(rate, channels, tuple(
        tuple(values[index:index + channels])
        for index in range(0, len(values), channels)
    ))


def frame_rms(audio: Audio, rate_hz: int = 50) -> list[float]:
    width = audio.rate // rate_hz
    if width * rate_hz != audio.rate:
        raise ValueError("audio sample rate is not divisible by analysis rate")
    result = []
    for start in range(0, len(audio.samples) - width + 1, width):
        block = audio.samples[start:start + width]
        power = sum(
            sum(value * value for value in sample) / len(sample)
            for sample in block
        ) / len(block)
        result.append(math.sqrt(power) / 32768.0)
    return result


def smooth_rms(values: list[float], radius: int = 2) -> list[float]:
    return [math.sqrt(sum(item * item for item in
                          values[max(0, at - radius):at + radius + 1]) /
                      len(values[max(0, at - radius):at + radius + 1]))
            for at in range(len(values))]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = fraction * (len(ordered) - 1)
    low = int(position)
    high = min(len(ordered) - 1, low + 1)
    blend = position - low
    return ordered[low] * (1.0 - blend) + ordered[high] * blend


def normalized_db(values: list[float], start: int, end: int) -> list[float]:
    reference = percentile(values[start:end], 0.95)
    if reference <= 0:
        raise ValueError("selected audio interval is silent")
    return [max(-60.0, 20.0 * math.log10(max(value, reference / 1000) /
                                         reference))
            for value in values]


def correlation(first: list[float], second: list[float]) -> float | None:
    if len(first) != len(second) or len(first) < 2:
        return None
    left = statistics.fmean(first)
    right = statistics.fmean(second)
    numerator = sum((a - left) * (b - right)
                    for a, b in zip(first, second))
    denominator = math.sqrt(
        sum((a - left) ** 2 for a in first) *
        sum((b - right) ** 2 for b in second)
    )
    return numerator / denominator if denominator else None


def compare_contours(source: Audio, target: Audio, start: int, end: int) -> dict:
    source_rms = smooth_rms(frame_rms(source))
    target_rms = smooth_rms(frame_rms(target))
    count = min(len(source_rms), len(target_rms))
    start, end = max(0, start), min(count, end)
    source_db = normalized_db(source_rms, start, end)
    target_db = normalized_db(target_rms, start, end)

    def onset(values: list[float]) -> int | None:
        return next((frame for frame in range(start, end)
                     if values[frame] >= -30.0), None)

    source_onset, target_onset = onset(source_db), onset(target_db)
    shift = 0 if source_onset is None or target_onset is None \
        else target_onset - source_onset
    pairs = []
    for frame in range(start, end):
        target_frame = frame + shift
        if 0 <= target_frame < count and max(
                source_db[frame], target_db[target_frame]) >= -40.0:
            pairs.append((source_db[frame], target_db[target_frame]))
    errors = [abs(left - right) for left, right in pairs]
    return {
        "method": (
            "50 Hz RMS energy, 100 ms RMS smoothing, independent 95th-"
            "percentile level normalization, onset alignment, compare only "
            "frames where either contour is above -40 dB"
        ),
        "source_onset_frame": source_onset,
        "target_onset_frame": target_onset,
        "alignment_shift_frames": shift,
        "compared_frames": len(pairs),
        "median_absolute_error_db": (
            percentile(errors, 0.5) if errors else None
        ),
        "p90_absolute_error_db": (
            percentile(errors, 0.9) if errors else None
        ),
        "correlation": correlation(
            [left for left, _right in pairs],
            [right for _left, right in pairs],
        ),
        "warning": (
            "This compares macroscopic loudness shape, not waveform or "
            "timbre; FM and pulse-wave PCM are intentionally incomparable "
            "sample-for-sample."
        ),
    }


def write_contours(path: Path, source: Audio, target: Audio) -> None:
    left = smooth_rms(frame_rms(source))
    right = smooth_rms(frame_rms(target))
    lines = ["frame,seconds,opl_rms,juku_rms"]
    for frame in range(min(len(left), len(right))):
        lines.append(
            f"{frame},{frame / 50:.6f},{left[frame]:.9f},{right[frame]:.9f}"
        )
    path.write_text("\n".join(lines) + "\n")


def mono_samples(audio: Audio) -> list[int]:
    return [round(sum(sample) / len(sample)) for sample in audio.samples]


def resample_linear(values: list[int], source_rate: int,
                    target_rate: int) -> list[int]:
    frames = round(len(values) * target_rate / source_rate)
    result = []
    for at in range(frames):
        position = at * source_rate / target_rate
        low = min(len(values) - 1, int(position))
        high = min(len(values) - 1, low + 1)
        blend = position - low
        result.append(round(values[low] * (1.0 - blend) + values[high] * blend))
    return result


def write_ab(path: Path, source: Audio, target: Audio) -> None:
    left = resample_linear(mono_samples(source), source.rate, WAV_RATE)
    right = resample_linear(mono_samples(target), target.rate, WAV_RATE)
    left_rms = math.sqrt(statistics.fmean(value * value for value in left))
    right_rms = math.sqrt(statistics.fmean(value * value for value in right))
    scale = left_rms / right_rms if right_rms else 1.0
    right = [max(-32768, min(32767, round(value * scale))) for value in right]
    silence = [0] * (WAV_RATE // 2)
    combined = left + silence + right
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(WAV_RATE)
        output.writeframes(struct.pack(f"<{len(combined)}h", *combined))


def pitch_report(segments: list[opl_voices.NoteSegment], fit_report: dict,
                 target_rate: int) -> dict:
    by_identifier = {segment.identifier: segment for segment in segments}
    episodes = fit_report.get("detuned_layer_analysis", {}).get("episodes", [])
    if not episodes:
        return {"mode": "merged logical pitch", "members": []}
    members = []
    for item in episodes[0]["members"]:
        source_segments = item.get("source_segments", [item["segment"]])
        group = [by_identifier[identifier] for identifier in source_segments]
        segment = group[0]
        pitch = segment.pitches[0].midi_pitch
        assert pitch is not None
        source_hz = 440.0 * 2.0 ** ((pitch - 69.0) / 12.0)
        target_hz = item["phase_step"] * target_rate / 65536.0
        members.append({
            "source_segment": segment.identifier,
            "source_segments": source_segments,
            "source_channels": [item.bank * 9 + item.channel
                                for item in group],
            "source_midi_pitch": pitch,
            "source_hz": source_hz,
            "target_phase_step": item["phase_step"],
            "target_hz": target_hz,
            "error_cents": 1200.0 * math.log2(target_hz / source_hz),
        })
    return {
        "mode": "source-derived detuned members selected on host",
        "source_members": len(segments),
        "target_members": len(members),
        "members": members,
        "maximum_absolute_error_cents": max(
            abs(item["error_cents"]) for item in members
        ),
    }


def recalibrate_detuned_phase_steps(
        fit_report: dict, segments: list[opl_voices.NoteSegment],
        note: opl_voices.LogicalNote, mapped_midi: int, target_rate: int,
) -> dict:
    """Retune host-generated fixed steps without repeating envelope search."""
    result = copy.deepcopy(fit_report)
    by_identifier = {segment.identifier: segment for segment in segments}
    octave_offset = mapped_midi - round(note.initial_pitch)
    episodes = result.get("detuned_layer_analysis", {}).get("episodes", [])
    for episode in episodes:
        steps = set()
        for member in episode["members"]:
            source_identifiers = member.get(
                "source_segments", [member["segment"]],
            )
            source_steps = set()
            for identifier in source_identifiers:
                segment = by_identifier[identifier]
                pitch = segment.pitches[0].midi_pitch
                if pitch is None:
                    raise ValueError("detuned member lacks a finite pitch")
                frequency = 440.0 * 2.0 ** (
                    (pitch + octave_offset - 69.0) / 12.0
                )
                source_steps.add(round(frequency * 65536.0 / target_rate))
            if len(source_steps) != 1:
                raise ValueError(
                    "sample-rate calibration split an equal-step member group"
                )
            member["phase_step"] = source_steps.pop()
            steps.add(member["phase_step"])
        if len(steps) != len(episode["members"]):
            raise ValueError(
                "sample-rate calibration merged distinct member groups; "
                "rerun the full fitter with an explicit target rate"
            )
    result["detuned_layer_analysis"]["target_sample_rate_hz"] = target_rate
    # The note measurement references the same logical episode in the live
    # fitter, but JSON/deep-copy callers need an explicit synchronized copy.
    by_note = {episode["logical_note"]: episode for episode in episodes}
    for measurement in result.get("notes", []):
        episode = measurement.get("detuned_layer_episode")
        if episode is not None:
            measurement["detuned_layer_episode"] = by_note[
                episode["logical_note"]
            ]
    return result


def source_effects(probes: list[opl_oracle.OracleChannelProbe],
                   segments: list[opl_voices.NoteSegment]) -> dict:
    channels = {segment.bank * 9 + segment.channel for segment in segments}
    selected = [item.probe for item in probes if item.channel in channels and
                any(segment.bank * 9 + segment.channel == item.channel and
                    segment.start <= item.probe.sample < segment.end
                    for segment in segments)]
    return {
        "physical_channels": sorted(channels),
        "am_on_direct_path": any(
            (probe.carrier_am or (probe.connection and probe.modulator_am))
            for probe in selected
        ),
        "vibrato_on_direct_path": any(
            (probe.carrier_vibrato or
             (probe.connection and probe.modulator_vibrato))
            for probe in selected
        ),
        "pitch_states": len({(probe.f_number, probe.block)
                             for probe in selected}),
        "carrier_envelope_stages": sorted({probe.carrier_stage
                                            for probe in selected}),
        "modulator_envelope_stages": sorted({probe.modulator_stage
                                              for probe in selected}),
    }


def generate(args: argparse.Namespace) -> dict:
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    data, compressed_sha = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    vgm_sha = hashlib.sha256(data).hexdigest()
    try:
        source_label = str(source.relative_to(ROOT))
    except ValueError:
        source_label = str(source)
    full_segments = opl_voices.reconstruct_segments(
        writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    full_notes = opl_voices.group_layers(
        full_segments, opl_voices.candidate_relations(full_segments),
    )
    (output / "source-logical-notes.json").write_text(json.dumps({
        "schema": "jukupoly-opl-logical-note-catalog-v1",
        "source_name": source.name,
        "source_vgm_sha256": vgm_sha,
        "notes": [asdict(note) for note in full_notes],
    }, indent=2) + "\n")
    selected = select_logical_note(
        full_notes, identifier=args.logical_note,
        at_seconds=args.at_seconds, midi_note=args.midi_note,
    )
    member_ids = set(selected.members)
    members = [segment for segment in full_segments
               if segment.identifier in member_ids]
    window_start = max(
        0, selected.start - round(args.pre_roll * VGM_RATE),
    )
    window_start = window_start // ANALYSIS_FRAME * ANALYSIS_FRAME
    window_end = selected.end + round(args.tail * VGM_RATE)
    window_end = ((window_end + ANALYSIS_FRAME - 1) //
                  ANALYSIS_FRAME * ANALYSIS_FRAME)
    total_samples = window_end - window_start
    frames = total_samples // ANALYSIS_FRAME
    spans = [(item.bank, item.channel, item.start, item.end)
             for item in members]
    isolated_writes = opl_oracle.isolate_note_writes(
        writes, spans, window_start, window_end,
    )

    with tempfile.TemporaryDirectory(prefix="jukupoly-voice-diff.") as name:
        temporary = Path(name)
        oracle, renderer = build_host_tools(temporary)
        stream = output / "source-voice.jop"
        raw_pcm = temporary / "source-voice.s16le"
        probes_path = output / "source-voice-probes.csv"
        opl_oracle.write_event_stream(stream, isolated_writes, total_samples)
        oracle_output = run([
            str(oracle), str(stream), str(raw_pcm), str(probes_path), "all",
        ])
        source_wav = output / "01-opl-reference.wav"
        pcm_to_wav(raw_pcm, source_wav)
        probes = opl_oracle.read_channel_probes(probes_path)

        isolated_segments = opl_voices.reconstruct_segments(
            isolated_writes, info.banks, total_samples, info.clock,
            info.frequency_divider,
        )
        isolated_notes = opl_voices.group_layers(
            isolated_segments,
            opl_voices.candidate_relations(isolated_segments),
        )
        if len(isolated_notes) != 1:
            raise ValueError(
                f"isolated register stream reconstructed {len(isolated_notes)} "
                "logical notes instead of one"
            )
        note = isolated_notes[0]
        allocation = isolated_allocation(note, frames)
        base = vgz.compile_score(
            info, writes, source, compressed_sha, vgm_sha, set(), {}, False,
        )
        base = copy.deepcopy(base)
        base["rows"] = frame_rows(frames)
        base["conversion"]["duration_frames"] = frames
        base["conversion"]["duration_seconds"] = frames / 50
        base["conversion"]["total_vgm_samples"] = total_samples
        score_path = output / "juku-voice-score.json"
        com_path = output / "juku-voice.com"
        target_wav = output / "02-juku-cosim.wav"
        calibration_rate = args.target_sample_rate
        calibration = []
        fits, base_fit_report = opl_enhanced.fit_selected_envelopes(
            isolated_segments, isolated_notes, allocation, probes, frames,
            enable_rearticulation=True,
            enable_detuned_layers=True,
            enable_target_shape_fit=True,
            target_sample_rate=calibration_rate,
        )
        for iteration in range(3):
            fit_report = recalibrate_detuned_phase_steps(
                base_fit_report, isolated_segments, note,
                round(note.initial_pitch), calibration_rate,
            )
            score = opl_enhanced.compile_enhanced_score(
                base, isolated_notes, allocation, fits, frames, fit_report,
                target_sample_rate=calibration_rate,
                frame_samples=args.frame_samples,
                segments=isolated_segments,
            )
            score["title"] = (
                f"{base['title']} — isolated logical note "
                f"{selected.identifier}"
            )
            score["arrangement"] = (
                "Host-isolated OPL logical note; three-voice source-member "
                "reduction with host-fitted envelopes and no percussion"
            )
            score["conversion"]["voice_isolation"] = {
                "source_logical_note": selected.identifier,
                "source_window_samples": [window_start, window_end],
                "source_window_seconds": [window_start / VGM_RATE,
                                          window_end / VGM_RATE],
                "members": [asdict(item) for item in members],
            }
            score_path.write_text(json.dumps(score, indent=2) + "\n")
            generated, metadata = build.compile_song(score)
            (output / "juku-voice-generated.inc").write_text(generated)
            image = build.assemble(
                generated, metadata["mod_effects"],
                metadata["enhanced_envelopes"],
                metadata["enhanced_tremolo"], metadata["enhanced_vibrato"],
            )
            com_path.write_bytes(image)
            renderer_output = run([
                str(renderer), "--sample-rate", str(WAV_RATE), "--lead", "0",
                "--tail", "0", "--max-seconds", str(frames / 50 + 5),
                str(com_path), str(target_wav),
            ])
            run_seconds = renderer_run_seconds(renderer_output)
            effective_target_rate = (
                frames * args.frame_samples / run_seconds
            )
            calibration.append({
                "iteration": iteration + 1,
                "phase_table_rate_hz": calibration_rate,
                "measured_average_sample_hz": effective_target_rate,
                "renderer_run_seconds": run_seconds,
            })
            next_rate = round(effective_target_rate)
            if next_rate == calibration_rate:
                break
            calibration_rate = next_rate

    source_audio = read_wav(source_wav)
    target_audio = read_wav(target_wav)
    start_frame = opl_voices.analysis_frame(note.start)
    end_frame = min(frames, opl_voices.analysis_frame(note.end) + 64)
    contour_path = output / "envelope-contours.csv"
    write_contours(contour_path, source_audio, target_audio)
    ab_path = output / "03-opl-then-juku.wav"
    write_ab(ab_path, source_audio, target_audio)
    pitch = pitch_report(isolated_segments, fit_report, effective_target_rate)
    member_fit = fit_report.get("detuned_layer_analysis", {})
    report = {
        "schema": "jukupoly-opl-isolated-voice-comparison-v1",
        "source": {
            "path": source_label,
            "compressed_sha256": compressed_sha,
            "vgm_sha256": vgm_sha,
            "chip": info.chip,
            "chip_clock_hz": info.clock,
            "gd3": info.gd3,
        },
        "selection": {
            "logical_note": selected.identifier,
            "initial_midi_pitch": selected.initial_pitch,
            "start_seconds": selected.start / VGM_RATE,
            "end_seconds": selected.end / VGM_RATE,
            "source_members": len(members),
            "source_channels": sorted(
                item.bank * 9 + item.channel for item in members
            ),
            "window_seconds": [window_start / VGM_RATE,
                               window_end / VGM_RATE],
        },
        "reference": {
            "engine": "Nuked OPL3",
            "commit": PINNED_NUKED_COMMIT,
            "register_writes": len(isolated_writes),
            "oracle_output": oracle_output,
            "wav": source_wav.name,
            "wav_sha256": sha256(source_wav),
            "effects": source_effects(probes, isolated_segments),
        },
        "target": {
            "engine": "cycle-level 8080 plus D57 PIT pulse renderer",
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "com": com_path.name,
            "com_sha256": sha256(com_path),
            "wav": target_wav.name,
            "wav_sha256": sha256(target_wav),
            "renderer_output": renderer_output,
            "initial_phase_table_rate_hz": args.target_sample_rate,
            "final_phase_table_rate_hz": calibration_rate,
            "measured_average_sample_hz": effective_target_rate,
            "measured_music_frame_hz": (
                effective_target_rate / args.frame_samples
            ),
            "host_calibration": calibration,
            "frame_samples": args.frame_samples,
            "runtime_effects": (
                "fixed phase steps, 4-bit ADSR packets, bounded host-chosen "
                "rearticulation; no OPL emulation on the 8080"
            ),
        },
        "comparison": {
            "pitch": pitch,
            "envelope_fit": {
                "logical_note_sample_weighted_mae_levels":
                    fit_report["sample_weighted_mean_absolute_error"],
                "logical_note_maximum_error_levels":
                    fit_report["maximum_error"],
                "member_sample_weighted_mae_levels":
                    member_fit.get("member_sample_weighted_mean_absolute_error"),
                "member_maximum_error_levels":
                    member_fit.get("member_maximum_error"),
                "rearticulation_packets": fit_report["rearticulation"].get(
                    "emitted_packets", 0
                ),
            },
            "rendered_energy_contour": compare_contours(
                source_audio, target_audio, start_frame, end_frame,
            ),
            "effect_disposition": {
                "source_direct_am": source_effects(
                    probes, isolated_segments,
                )["am_on_direct_path"],
                "separate_target_tremolo": False,
                "reason": (
                    "the detuned-member path fits the oracle's post-AM "
                    "50 Hz levels directly into host-generated envelope and "
                    "rearticulation packets; it spends no per-sample target "
                    "cycles on an OPL model"
                ),
                "source_direct_vibrato": source_effects(
                    probes, isolated_segments,
                )["vibrato_on_direct_path"],
            },
            "ab_wav": ab_path.name,
            "contours_csv": contour_path.name,
        },
        "host_target_split": {
            "host": [
                "parse and timestamp every OPL register write",
                "reconstruct and select the logical note and member channels",
                "render the isolated authoritative OPL reference",
                "fit envelopes/rearticulations and choose at most three layers",
                "quantize source pitches to fixed target phase steps",
                "compile the score and calculate comparison evidence",
            ],
            "juku": [
                "parse precomputed 50 Hz row packets",
                "advance bounded 4-bit envelope state",
                "mix at most three fixed-step pulse voices",
            ],
        },
        "gates": {
            "one_logical_note_reconstructed": len(isolated_notes) == 1,
            "no_hardware_rhythm_bits": all(
                write.register != 0xBD or not write.value & 0x3F
                for write in isolated_writes
            ),
            "target_voice_limit_respected": (
                pitch.get("target_members", 1) <= 3
            ),
            "member_mean_error_below_delivery_limit": (
                member_fit.get("member_sample_weighted_mean_absolute_error",
                               99) <= opl_enhanced.MAX_DELIVERY_NOTE_MAE
            ),
            "pitch_error_below_five_cents": (
                pitch.get("maximum_absolute_error_cents", 0) < 5
            ),
        },
    }
    report_path = output / "comparison.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source OPL VGM or VGZ")
    parser.add_argument("output", type=Path, help="output evidence directory")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--logical-note", type=int,
                           help="exact logical-note identifier")
    selection.add_argument("--at-seconds", type=float, default=0.0,
                           help="select the sole note active at this time")
    parser.add_argument("--midi-note", type=int,
                        help="narrow --at-seconds selection by rounded MIDI note")
    parser.add_argument("--pre-roll", type=float, default=0.25,
                        help="seconds before the selected onset (default 0.25)")
    parser.add_argument("--tail", type=float, default=1.5,
                        help="seconds after source key-off (default 1.5)")
    parser.add_argument("--target-sample-rate", type=int, default=7170)
    parser.add_argument("--frame-samples", type=int, default=143)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source is missing: {args.source}")
    if args.logical_note is not None and args.logical_note < 0:
        parser.error("--logical-note must be nonnegative")
    if args.at_seconds < 0 or args.pre_roll < 0 or args.tail < 0:
        parser.error("selection time, pre-roll, and tail must be nonnegative")
    if args.midi_note is not None and not 0 <= args.midi_note <= 127:
        parser.error("--midi-note must be 0..127")
    if not 4000 <= args.target_sample_rate <= 12000:
        parser.error("--target-sample-rate must be 4000..12000")
    if not 129 <= args.frame_samples <= 143:
        parser.error("--frame-samples must be 129..143")
    try:
        report = generate(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    print(
        "JUKUPOLY-VOICE-DIFF: PASS "
        f"note={report['selection']['logical_note']} "
        f"members={report['selection']['source_members']} "
        f"output={args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
