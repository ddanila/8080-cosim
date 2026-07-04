#!/usr/bin/env sh
set -eu

if [ "${KICAD_CLI:-}" ]; then
  if [ -x "$KICAD_CLI" ] || command -v "$KICAD_CLI" >/dev/null 2>&1; then
    printf '%s\n' "$KICAD_CLI"
    exit 0
  fi
  printf 'KICAD_CLI is set but not executable/found: %s\n' "$KICAD_CLI" >&2
  exit 2
fi

if command -v kicad-cli >/dev/null 2>&1; then
  command -v kicad-cli
  exit 0
fi

for candidate in \
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  /Applications/KiCad/kicad-cli \
  /Applications/KiCad/*.app/Contents/MacOS/kicad-cli \
  /opt/homebrew/Caskroom/kicad/*/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  /usr/local/Caskroom/kicad/*/KiCad/KiCad.app/Contents/MacOS/kicad-cli
do
  for path in $candidate; do
    if [ -x "$path" ]; then
      printf '%s\n' "$path"
      exit 0
    fi
  done
done

printf 'Unable to find kicad-cli. Set KICAD_CLI=/path/to/kicad-cli.\n' >&2
exit 1
