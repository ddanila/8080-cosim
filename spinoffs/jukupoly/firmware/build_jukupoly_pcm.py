#!/usr/bin/env python3
"""Convert a PCM WAV into a packed 4-bit standalone Juku CP/M player."""

from __future__ import annotations

import argparse
import array
import hashlib
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build_zmac import executable  # noqa: E402


SOURCE = HERE / "jukupoly-pcm-0100.asm"
INCLUDE_NAME = "jukupoly-pcm-generated.inc"
PAIR_CYCLES = 422
DEFAULT_CPU_HZ = 1_700_000.0
PIT_HZ = 2_000_000.0
MAX_COM_BYTES = 0x8000 - 0x0100


class PcmError(ValueError):
    pass


def read_pcm_wav(path: Path) -> tuple[list[float], int]:
    """Read integer PCM WAV and downmix its channels to floating-point mono."""
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            width = source.getsampwidth()
            rate = source.getframerate()
            frames = source.getnframes()
            compression = source.getcomptype()
            raw = source.readframes(frames)
    except (OSError, EOFError, wave.Error) as exc:
        raise PcmError(f"cannot read PCM WAV {path}: {exc}") from exc
    if compression != "NONE" or channels < 1 or width not in (1, 2, 3, 4):
        raise PcmError("input must be an uncompressed 8/16/24/32-bit PCM WAV")
    if rate <= 0 or frames <= 0:
        raise PcmError("input WAV must contain at least one audio frame")

    values: list[float] = []
    offset = 0
    scale = float(1 << (width * 8 - 1))
    for _ in range(frames):
        mixed = 0.0
        for _ in range(channels):
            item = raw[offset:offset + width]
            offset += width
            sample = item[0] - 128 if width == 1 else int.from_bytes(
                item, "little", signed=True,
            )
            mixed += sample / scale
        values.append(mixed / channels)
    return values, rate


def resample(samples: list[float], source_rate: int,
             target_rate: float) -> list[float]:
    """Band-limit and resample with a compact 32-tap windowed-sinc kernel."""
    count = max(2, round(len(samples) * target_rate / source_rate))
    ratio = source_rate / target_rate
    cutoff = 0.47 * min(1.0, target_rate / source_rate)
    radius = 16
    result: list[float] = []
    for output_index in range(count):
        position = output_index * ratio
        centre = math.floor(position)
        total = 0.0
        weight_total = 0.0
        for source_index in range(centre - radius + 1, centre + radius + 1):
            if not 0 <= source_index < len(samples):
                continue
            distance = position - source_index
            phase = 2.0 * cutoff * distance
            sinc = (1.0 if phase == 0.0 else
                    math.sin(math.pi * phase) / (math.pi * phase))
            window_position = distance / radius
            if abs(window_position) >= 1.0:
                continue
            window = 0.5 + 0.5 * math.cos(math.pi * window_position)
            weight = 2.0 * cutoff * sinc * window
            total += samples[source_index] * weight
            weight_total += weight
        result.append(total / weight_total if weight_total else 0.0)
    if len(result) & 1:
        result.append(0.0)
    return result


def quantize(samples: list[float], peak_level: float,
             maximum_code: int) -> tuple[bytes, list[int]]:
    source_peak = max(abs(value) for value in samples)
    gain = peak_level / source_peak if source_peak else 1.0
    midpoint = (maximum_code + 1) / 2.0
    radius = (maximum_code - 1) / 2.0
    nibbles = [
        max(1, min(maximum_code, round(midpoint + radius * value * gain)))
        for value in samples
    ]
    packed = bytes(
        nibbles[index] << 4 | nibbles[index + 1]
        for index in range(0, len(nibbles), 2)
    )
    return packed, nibbles


def generated_include(packed: bytes) -> str:
    lines = ["jukupoly_pcm_data:"]
    for offset in range(0, len(packed), 16):
        values = ",".join(
            f"0{value:02x}h" for value in packed[offset:offset + 16]
        )
        lines.append(f"        db      {values}")
    lines.extend(["jukupoly_pcm_end:", ""])
    return "\n".join(lines)


def assemble(include: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="jukupoly-pcm.") as name:
        directory = Path(name)
        source = directory / SOURCE.name
        output = directory / "jukupcm.cim"
        source.write_bytes(SOURCE.read_bytes())
        (directory / INCLUDE_NAME).write_text(include)
        subprocess.run([
            str(executable()), "--nmnv", "--zmac", "-8",
            f"-I{directory}", "-o", str(output), str(source),
        ], check=True)
        image = output.read_bytes()
    if len(image) > MAX_COM_BYTES:
        raise PcmError(
            f"COM image is {len(image)} bytes; conservative Juku limit is "
            f"{MAX_COM_BYTES} bytes"
        )
    return image


def write_preview(path: Path, nibbles: list[int], rate: int,
                  maximum_code: int) -> None:
    midpoint = (maximum_code + 1) / 2.0
    radius = (maximum_code - 1) / 2.0
    samples = array.array("h", (
        round((value - midpoint) * 32767 / radius) for value in nibbles
    ))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.tobytes())


def build(input_path: Path, cpu_hz: float,
          peak_level: float) -> tuple[bytes, list[int], dict[str, float | int | str]]:
    if not math.isfinite(cpu_hz) or cpu_hz <= 0:
        raise PcmError("CPU rate must be positive and finite")
    if not 0.1 <= peak_level <= 1.0:
        raise PcmError("peak level must be between 0.1 and 1.0")
    target_rate = cpu_hz * 2.0 / PAIR_CYCLES
    maximum_code = min(15, math.floor(PIT_HZ / target_rate / 16.0))
    if maximum_code < 3:
        raise PcmError("sample rate leaves fewer than three safe pulse levels")
    source, source_rate = read_pcm_wav(input_path)
    converted = resample(source, source_rate, target_rate)
    packed, nibbles = quantize(converted, peak_level, maximum_code)
    image = assemble(generated_include(packed))
    metadata: dict[str, float | int | str] = {
        "source_rate_hz": source_rate,
        "target_rate_hz": target_rate,
        "samples": len(nibbles),
        "packed_bytes": len(packed),
        "maximum_code": maximum_code,
        "duration_seconds": len(nibbles) / target_rate,
        "com_bytes": len(image),
        "com_sha256": hashlib.sha256(image).hexdigest(),
    }
    return image, nibbles, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="uncompressed integer PCM WAV")
    parser.add_argument("output", type=Path, help="output CP/M COM image")
    parser.add_argument("--cpu-hz", type=float, default=DEFAULT_CPU_HZ,
                        help="effective Juku CPU rate (default: 1700000)")
    parser.add_argument("--peak", type=float, default=0.96,
                        help="normalised input peak, 0.1..1.0 (default: 0.96)")
    parser.add_argument("--preview", type=Path,
                        help="also write the decoded 4-bit PCM preview WAV")
    args = parser.parse_args()
    try:
        image, nibbles, metadata = build(args.input, args.cpu_hz, args.peak)
    except PcmError as exc:
        raise SystemExit(f"JUKUPOLY-PCM: FAIL {exc}") from exc
    args.output.write_bytes(image)
    if args.preview:
        write_preview(args.preview, nibbles,
                      round(float(metadata["target_rate_hz"])),
                      int(metadata["maximum_code"]))
    print(
        "JUKUPOLY-PCM: PASS "
        f"rate={float(metadata['target_rate_hz']):.3f}Hz "
        f"duration={float(metadata['duration_seconds']):.3f}s "
        f"levels=1..{metadata['maximum_code']} "
        f"samples={metadata['samples']} packed={metadata['packed_bytes']} "
        f"com={metadata['com_bytes']} sha256={metadata['com_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
