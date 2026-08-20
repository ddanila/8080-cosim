#!/usr/bin/env bash
# Strict native checks for the platform-neutral Juku host core.
set -euo pipefail
cd "$(dirname "$0")/.."
CC=${CC:-cc}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

COMMON=(
  -std=c99 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow
  -Ihost/include
  host/src/jukuhost_core.c host/src/jukuhost_bootstrap.c
  host/src/jukuhost_media.c host/src/jukuhost_service.c
  host/tests/core_test.c
)

"$CC" "${COMMON[@]}" -fsigned-char -o "$TMP/core-signed"
"$TMP/core-signed"
"$CC" "${COMMON[@]}" -funsigned-char -o "$TMP/core-unsigned"
"$TMP/core-unsigned"

if command -v clang >/dev/null 2>&1; then
  clang "${COMMON[@]}" -fsigned-char -o "$TMP/core-clang"
  "$TMP/core-clang"
fi

"$CC" "${COMMON[@]}" -fsigned-char -fsanitize=address,undefined \
  -fno-omit-frame-pointer -o "$TMP/core-sanitize"
"$TMP/core-sanitize"
