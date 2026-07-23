#!/usr/bin/env bash
set -euo pipefail

APP=org.kicad.KiCad
# The Flatpak library extension is mounted inside the sandbox at this path.
# pcbnew.FootprintLoad() does not consult KiCad's GUI library tables, so the
# generator scripts need the concrete footprint root in their environment.
FLATPAK_FOOTPRINTS="${KICAD_FLATPAK_FOOTPRINTS:-/app/extensions/Library/footprints}"
if flatpak info --user "$APP" >/dev/null 2>&1; then
  exec flatpak run --user --filesystem=/tmp --command=python3 \
    --env=KICAD_FOOTPRINTS="$FLATPAK_FOOTPRINTS" "$APP" "$@"
fi
if flatpak info --system "$APP" >/dev/null 2>&1; then
  exec flatpak run --system --filesystem=/tmp --command=python3 \
    --env=KICAD_FOOTPRINTS="$FLATPAK_FOOTPRINTS" "$APP" "$@"
fi
echo "KiCad Flatpak is not installed: $APP" >&2
exit 1
