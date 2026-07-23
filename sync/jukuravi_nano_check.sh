#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CXX=${CXX:-c++}
command -v "$CXX" >/dev/null || { echo "$CXX not found"; exit 2; }

mkdir -p .tools
# Snap-packaged arduino-cli has a private /tmp namespace, so keep this guarded
# build directory inside the checkout where both the shell and CLI can inspect
# the same emitted artifact.
tmp=$(mktemp -d .tools/jukuravi-nano.XXXXXX)
trap 'rm -rf "$tmp"' EXIT
sketch=spinoffs/jukuravi/nano/jukuravi_bridge

"$CXX" -std=c++11 -Wall -Wextra -Werror -pedantic \
  -I"$sketch" -o "$tmp/bridge-test" tests/jukuravi_nano_bridge_test.cpp
"$tmp/bridge-test"

if command -v arduino-cli >/dev/null 2>&1 && \
   arduino-cli core list | grep -q '^arduino:avr '; then
  if ! arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 \
      --warnings all --build-path "$tmp/avr" "$sketch" \
      >"$tmp/arduino.log" 2>&1; then
    cat "$tmp/arduino.log"
    exit 1
  fi
  hex=$(find "$tmp/avr" -maxdepth 1 -type f -name '*.ino.hex' -print -quit)
  test -n "$hex" && test -s "$hex"
  echo "JUKURAVI-NANO-AVR: PASS (arduino:avr Nano compile; $(wc -c < "$hex")-byte Intel HEX)"
else
  echo "JUKURAVI-NANO-AVR: SKIP (arduino-cli with arduino:avr core not installed)"
fi
