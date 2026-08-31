#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
third_party/zmac/src/zmac --nmnv --zmac -8 -P2=1 -P4=1 \
  -Ispinoffs/jukupoly/firmware \
  -o "$TMP/JUKEBOX.cim" \
  spinoffs/jukupoly/firmware/jukupoly-player-0100.asm
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-library-v1-test.json \
  --generated "$TMP/v1.inc" \
  --output "$TMP/v1.com" \
  --song-output "$TMP/D1T01.JPS"
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-envelope-v2-test.json \
  --generated "$TMP/envelope.inc" \
  --output "$TMP/envelope.com" \
  --song-output "$TMP/ENVELOPE.JPS"
python3 tests/jukupoly_library_test.py
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_library_test" \
  tests/jukupoly_library_test.c cosim/i8080.c
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_envelope_test" \
  tests/jukupoly_envelope_test.c cosim/i8080.c
for track in $(seq 1 44); do
  "$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/D1T01.JPS" "$track"
done
"$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/D1T01.JPS" abort
"$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/ENVELOPE.JPS"
for corruption in flags levels truncated descriptor pcm; do
  "$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/ENVELOPE.JPS" \
    "invalid-$corruption"
done
"$TMP/jukupoly_envelope_test" "$TMP/envelope.com"
