#!/usr/bin/env bash
set -euo pipefail

APP=org.kicad.KiCad
if flatpak info --user "$APP" >/dev/null 2>&1; then
  exec flatpak run --user --filesystem=/tmp --command=kicad-cli "$APP" "$@"
fi
if flatpak info --system "$APP" >/dev/null 2>&1; then
  exec flatpak run --system --filesystem=/tmp --command=kicad-cli "$APP" "$@"
fi
echo "KiCad Flatpak is not installed: $APP" >&2
exit 1
