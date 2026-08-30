#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 spinoffs/jukuravi/firmware/build_three_voice.py --check
spinoffs/jukuravi/render_jukupoly_wav.sh --sample-rate 48000 \
  spinoffs/jukuravi/firmware/three-voice.com "$TMP/three-voice.wav"
python3 tests/jukuravi_wav_test.py "$TMP/three-voice.wav"
