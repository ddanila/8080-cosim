#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "${KICAD_CLI:-}" ]; then
  if [ -x "$KICAD_CLI" ] || command -v "$KICAD_CLI" >/dev/null 2>&1; then
    printf '%s\n' "$KICAD_CLI"
    exit 0
  fi
  printf 'KICAD_CLI is set but not executable/found: %s\n' "$KICAD_CLI" >&2
  exit 2
fi

FLATPAK_CLI="$SCRIPT_DIR/kicad-flatpak-cli.sh"
if [ -x "$FLATPAK_CLI" ] && "$FLATPAK_CLI" --version >/dev/null 2>&1; then
  printf '%s\n' "$FLATPAK_CLI"
  exit 0
fi

if command -v kicad-cli-nightly >/dev/null 2>&1; then
  command -v kicad-cli-nightly
  exit 0
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
