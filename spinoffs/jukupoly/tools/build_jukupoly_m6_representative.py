#!/usr/bin/env python3
"""Rebuild the guarded four-track M6 conversion/profile checkpoint."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
IMPORTER = FIRMWARE / "import_jukupoly_vgz.py"
REPORTER = SPINOFF / "tools" / "report_jukupoly_m6_representative.py"
RENDER_REPORTER = SPINOFF / "tools" / "report_jukupoly_m6_renders.py"
LIBRARY_BUILDER = FIRMWARE / "build_doom_library.py"
LIBRARY_REPORTER = SPINOFF / "tools" / "report_jukupoly_m6_mixed_library.py"
DEFAULT_WORK = ROOT / "out" / "jukupoly-m6-representative"
DEFAULT_REPORT = SPINOFF / "OPL-M6-REPRESENTATIVE-PROFILE.json"
DEFAULT_RENDER_REPORT = SPINOFF / "OPL-M6-REPRESENTATIVE-RENDERS.json"
DEFAULT_LIBRARY = ROOT / "out" / "jukupoly-doom-library-m6-mixed"
DEFAULT_LIBRARY_REPORT = SPINOFF / "OPL-M6-MIXED-LIBRARY.json"
DELIVERY_MANIFEST = SPINOFF / "M6-REPRESENTATIVE-DELIVERY.json"
DOOMGATE_SCORE = FIRMWARE / "jukupoly-doomgate-full-vibrato-m5.json"
OPENING_SCORE = FIRMWARE / "jukupoly-opening-full-tremolo-m4.json"
ARCHIVE_HASHES = {
    "doom1": "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a",
    "doom2": "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365",
}
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


@dataclass(frozen=True)
class Conversion:
    pack: str
    source_name: str
    score_name: str
    frame_samples: int
    sample_rate: int
    tremolo: bool = False
    vibrato: bool = False
    prioritize_articulations: bool = False
    seconds: int | None = None


CONVERSIONS = (
    Conversion(
        "doom1", "03 The Imp's Song.vgz", "doom1-03-imp.json",
        143, 7100,
    ),
    Conversion(
        "doom1", "03 The Imp's Song.vgz", "doom1-03-imp-30s.json",
        143, 7170, seconds=30,
    ),
    Conversion(
        "doom1", "04 Dark Halls.vgz", "doom1-04-dark-halls.json",
        137, 6850, tremolo=True, prioritize_articulations=True,
    ),
    Conversion(
        "doom1", "04 Dark Halls.vgz", "doom1-04-dark-halls-30s.json",
        138, 6950, tremolo=True, prioritize_articulations=True, seconds=30,
    ),
    Conversion(
        "doom1", "06 Suspense.vgz", "doom1-06-suspense.json",
        137, 6850, tremolo=True,
    ),
    Conversion(
        "doom1", "06 Suspense.vgz", "doom1-06-suspense-30s.json",
        139, 6980, tremolo=True, seconds=30,
    ),
    Conversion(
        "doom2", "10 The Dave D. Taylor Blues.vgz",
        "doom2-10-dave-taylor.json", 129, 6450,
        tremolo=True, vibrato=True,
    ),
    Conversion(
        "doom2", "10 The Dave D. Taylor Blues.vgz",
        "doom2-10-dave-taylor-30s.json", 135, 6750,
        tremolo=True, vibrato=True, seconds=30,
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(archive: Path, names: set[str], destination: Path) -> None:
    with zipfile.ZipFile(archive) as source:
        available = set(source.namelist())
        missing = sorted(names - available)
        if missing:
            raise ValueError(
                f"{archive.name} lacks expected tracks: {', '.join(missing)}"
            )
        for name in sorted(names):
            (destination / name).write_bytes(source.read(name))


def convert(item: Conversion, sources: Path, scores: Path,
            oracle: Path) -> str:
    command = [
        sys.executable, str(IMPORTER), str(sources / item.source_name),
        str(scores / item.score_name), "--enhanced-envelopes",
        "--enhanced-frame-samples", str(item.frame_samples),
        "--enhanced-sample-rate", str(item.sample_rate),
        "--opl-oracle", str(oracle),
    ]
    if item.tremolo:
        command.append("--enhanced-tremolo")
    if item.vibrato:
        command.append("--enhanced-vibrato")
    if item.prioritize_articulations:
        command.append("--prioritize-articulations")
    if item.seconds is not None:
        command.extend(("--seconds", str(item.seconds)))
    result = subprocess.run(
        command, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def materialize_committed_deliveries(work: Path) -> list[Path]:
    specifications = (
        (
            DOOMGATE_SCORE, "doom1-02-doomgate.jps", 18_133,
            "01765553e4330f71cdbf5507367e8ee95cf5dee7d2d5fb5b5e52a86e3ab72079",
        ),
        (
            OPENING_SCORE, "doom2-18-opening.jps", 10_504,
            "7272b329cd09fae907418d83ad35a5ad14ecf36be26c6e8a5bd6c3c37b47fbf8",
        ),
    )
    destinations = []
    for score_path, filename, expected_bytes, expected_hash in specifications:
        score = json.loads(score_path.read_text())
        generated, metadata = build.compile_song(score)
        payload = build.assemble_song_file(generated, metadata)
        if (len(payload), hashlib.sha256(payload).hexdigest()) != (
                expected_bytes, expected_hash):
            raise ValueError(
                f"committed delivery payload is stale: {score_path.name}"
            )
        destination = work / "songs" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        destinations.append(destination)
    return destinations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doom", type=Path, required=True)
    parser.add_argument("--doom2", type=Path, required=True)
    parser.add_argument("--opl-oracle", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--render-report-output", type=Path, default=DEFAULT_RENDER_REPORT,
    )
    parser.add_argument("--library-output", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument(
        "--library-report-output", type=Path, default=DEFAULT_LIBRARY_REPORT,
    )
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    archives = {"doom1": args.doom.resolve(), "doom2": args.doom2.resolve()}
    for pack, path in archives.items():
        if not path.is_file():
            parser.error(f"archive is missing: {path}")
        actual = sha256(path)
        if actual != ARCHIVE_HASHES[pack]:
            parser.error(
                f"{path.name} SHA-256 is {actual}, expected "
                f"{ARCHIVE_HASHES[pack]}"
            )
    oracle = args.opl_oracle.resolve()
    if not oracle.is_file():
        parser.error(f"OPL oracle is missing: {oracle}")
    if not 1 <= args.jobs <= 12:
        parser.error("--jobs must be 1..12")

    work = args.work.resolve()
    sources = work / "sources"
    scores = work / "scores"
    sources.mkdir(parents=True, exist_ok=True)
    scores.mkdir(parents=True, exist_ok=True)
    try:
        for pack, archive in archives.items():
            extract(
                archive,
                {item.source_name for item in CONVERSIONS if item.pack == pack},
                sources,
            )
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.jobs) as executor:
            futures = {
                executor.submit(convert, item, sources, scores, oracle): item
                for item in CONVERSIONS
            }
            for future in concurrent.futures.as_completed(futures):
                print(future.result())
        subprocess.run([
            sys.executable, str(REPORTER), "--work", str(work),
            "--output", str(args.report_output.resolve()),
        ], cwd=ROOT, check=True)
        materialize_committed_deliveries(work)
        subprocess.run([
            sys.executable, str(RENDER_REPORTER), "--work", str(work),
            "--opl-oracle", str(oracle),
            "--output", str(args.render_report_output.resolve()),
        ], cwd=ROOT, check=True)
        library_output = args.library_output.resolve()
        subprocess.run([
            sys.executable, str(LIBRARY_BUILDER),
            "--doom", str(archives["doom1"]),
            "--doom2", str(archives["doom2"]),
            "--replacement-manifest", str(DELIVERY_MANIFEST),
            "--replacement-dir", str(work / "songs"),
            "--output-dir", str(library_output),
        ], cwd=ROOT, check=True)
        subprocess.run([
            sys.executable, str(LIBRARY_REPORTER),
            "--library", str(library_output),
            "--output", str(args.library_report_output.resolve()),
        ], cwd=ROOT, check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    print(
        f"JUKUPOLY-M6-BUILD: PASS work={work} "
        f"report={args.report_output.resolve()} "
        f"renders={args.render_report_output.resolve()} "
        f"library={args.library_report_output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
