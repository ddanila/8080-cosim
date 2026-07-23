#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

try_python() {
  local candidate="$1"
  if [ -z "$candidate" ]; then
    return 1
  fi
  if ! command -v "$candidate" >/dev/null 2>&1 && [ ! -x "$candidate" ]; then
    return 1
  fi
  if "$candidate" - <<'PY' >/dev/null 2>&1
import pcbnew
PY
  then
    command -v "$candidate" 2>/dev/null || printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

if [ -n "${KICAD_PYTHON:-}" ]; then
  if try_python "$KICAD_PYTHON"; then
    exit 0
  fi
  echo "KICAD_PYTHON cannot import pcbnew: $KICAD_PYTHON" >&2
  exit 2
fi

for candidate in \
  "$SCRIPT_DIR/kicad-flatpak-python.sh" \
  /usr/bin/python3 \
  python3 \
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.*/bin/python3 \
  /opt/homebrew/Caskroom/kicad/*/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.*/bin/python3 \
  /usr/local/Caskroom/kicad/*/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.*/bin/python3
do
  for expanded in $candidate; do
    if try_python "$expanded"; then
      exit 0
    fi
  done
done

echo "No Python interpreter with KiCad pcbnew module found." >&2
echo "Set KICAD_PYTHON to KiCad's Python interpreter." >&2
exit 2
