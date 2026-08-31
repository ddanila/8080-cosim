#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
third_party/zmac/src/zmac --nmnv --zmac -8 -P2=1 \
  -Ispinoffs/jukupoly/firmware \
  -o "$TMP/JUKEBOX.cim" \
  spinoffs/jukupoly/firmware/jukupoly-player-0100.asm
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-canyon-demo.json \
  --generated "$TMP/canyon.inc" \
  --output "$TMP/canyon.com" \
  --song-output "$TMP/D1T01.JPS"
python3 tests/jukupoly_library_test.py
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_library_test" \
  tests/jukupoly_library_test.c cosim/i8080.c
for track in $(seq 1 44); do
  "$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/D1T01.JPS" "$track"
done
"$TMP/jukupoly_library_test" "$TMP/JUKEBOX.cim" "$TMP/D1T01.JPS" abort
