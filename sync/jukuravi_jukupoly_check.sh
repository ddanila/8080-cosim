#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 spinoffs/jukuravi/firmware/build_jukupoly.py --check
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-suspense.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-suspense-generated.inc \
  --output spinoffs/jukuravi/firmware/suspense.com \
  --check
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-suspense-full.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-suspense-full-generated.inc \
  --output spinoffs/jukuravi/firmware/suspfull.com \
  --check
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-tdk-robots-60s.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-tdk-robots-60s-generated.inc \
  --output spinoffs/jukuravi/firmware/tdk60.com \
  --check
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-tdk-robots.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-tdk-robots-generated.inc \
  --output spinoffs/jukuravi/firmware/tdkrobot.com \
  --check
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukuravi_jukupoly_test" \
  tests/jukuravi_jukupoly_test.c cosim/i8080.c
"$TMP/jukuravi_jukupoly_test" spinoffs/jukuravi/firmware/jukupoly.com
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukuravi_jukupoly_suspense_test" \
  tests/jukuravi_jukupoly_suspense_test.c cosim/i8080.c
"$TMP/jukuravi_jukupoly_suspense_test" \
  spinoffs/jukuravi/firmware/suspense.com
"$TMP/jukuravi_jukupoly_suspense_test" \
  spinoffs/jukuravi/firmware/suspfull.com 6400
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukuravi_jukupoly_mod_test" \
  tests/jukuravi_jukupoly_mod_test.c cosim/i8080.c
"$TMP/jukuravi_jukupoly_mod_test" \
  spinoffs/jukuravi/firmware/tdk60.com 3000
"$TMP/jukuravi_jukupoly_mod_test" \
  spinoffs/jukuravi/firmware/tdkrobot.com 25728
