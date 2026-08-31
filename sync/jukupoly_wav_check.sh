#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 spinoffs/jukupoly/firmware/build_three_voice.py --check
spinoffs/jukupoly/render_jukupoly_wav.sh --sample-rate 48000 \
  spinoffs/jukupoly/firmware/three-voice.com "$TMP/three-voice.wav"
python3 tests/jukupoly_wav_test.py "$TMP/three-voice.wav"
