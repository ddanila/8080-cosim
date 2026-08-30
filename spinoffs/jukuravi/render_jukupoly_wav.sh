#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/render_jukupoly_wav" \
  spinoffs/jukuravi/tools/render_jukupoly_wav.c cosim/i8080.c -lm
"$TMP/render_jukupoly_wav" "$@"
