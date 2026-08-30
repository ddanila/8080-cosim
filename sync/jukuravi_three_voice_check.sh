#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 spinoffs/jukuravi/firmware/build_three_voice.py --check
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukuravi_three_voice_test" \
  tests/jukuravi_three_voice_test.c cosim/i8080.c
"$TMP/jukuravi_three_voice_test" \
  spinoffs/jukuravi/firmware/three-voice.com
