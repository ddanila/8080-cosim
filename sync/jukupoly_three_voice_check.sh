#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 spinoffs/jukupoly/firmware/build_three_voice.py --check
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_three_voice_test" \
  tests/jukupoly_three_voice_test.c cosim/i8080.c
"$TMP/jukupoly_three_voice_test" \
  spinoffs/jukupoly/firmware/three-voice.com
