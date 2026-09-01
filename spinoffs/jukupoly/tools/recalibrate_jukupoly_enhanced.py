#!/usr/bin/env python3
"""Apply a guarded measured-timing calibration to a symbolic-note JPS2 score."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FIRMWARE = Path(__file__).resolve().parents[1] / "firmware"
sys.path.insert(0, str(FIRMWARE))

import opl_enhanced  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sample-rate", type=int, required=True)
    parser.add_argument("--frame-samples", type=int, required=True)
    args = parser.parse_args()
    try:
        score = json.loads(args.source.read_text())
        result = opl_enhanced.recalibrate_note_score(
            score, sample_rate=args.sample_rate,
            frame_samples=args.frame_samples,
        )
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(
        f"JUKUPOLY-RECALIBRATE: wrote {args.output} "
        f"samples={args.frame_samples} rate={args.sample_rate}Hz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
