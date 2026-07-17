#!/usr/bin/env sh
# rev B CAD tool resolver (TC.1). SOURCE this from the repo root (callers cd there
# first, like sync/check.sh). Sets KICAD_CLI, KICAD_PYTHON, KICAD_FOOTPRINTS,
# FREECADCMD via the repo locator scripts + known install paths. Missing tools are
# left empty, not fatal: callers gate a step with `revb_have <VAR>` and print a
# SKIP, so CI (and desks without the tools) stay green — the rev A/CI convention.
#
# Usage:
#   . spinoffs/minimal-vga/kicad/revb/env.sh   # then revb_have / revb_tool_summary
#   sh spinoffs/minimal-vga/kicad/revb/env.sh --print   # just report what resolved

: "${KICAD_CLI:=$(sh scripts/find-kicad-cli.sh 2>/dev/null || true)}"
: "${KICAD_PYTHON:=$(sh scripts/find-kicad-python.sh 2>/dev/null || true)}"

if [ -z "${KICAD_FOOTPRINTS:-}" ]; then
  # Derive from the resolved kicad-cli app bundle (glob-free, so this stays safe
  # even when sourced under zsh, which errors on unmatched globs).
  _bundle_fp=""
  case "$KICAD_CLI" in
    */KiCad.app/Contents/MacOS/kicad-cli)
      _bundle_fp="${KICAD_CLI%/MacOS/kicad-cli}/SharedSupport/footprints" ;;
  esac
  for _d in \
    "$_bundle_fp" \
    /usr/share/kicad/footprints \
    "$HOME/Applications/KiCad.app/Contents/SharedSupport/footprints" \
    /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints
  do
    if [ -n "$_d" ] && [ -d "$_d" ]; then KICAD_FOOTPRINTS="$_d"; break; fi
  done
fi

: "${FREECADCMD:=$(command -v freecadcmd 2>/dev/null || true)}"
if [ -z "${FREECADCMD:-}" ]; then
  for _f in \
    "$HOME/bin/freecadcmd" \
    "$HOME/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd" \
    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
  do
    if [ -x "$_f" ]; then FREECADCMD="$_f"; break; fi
  done
fi

export KICAD_CLI KICAD_PYTHON KICAD_FOOTPRINTS FREECADCMD

# revb_have KICAD_CLI  -> exit 0 if that tool resolved, else 1 (for skip gating)
revb_have() {
  eval _v="\${$1:-}"
  [ -n "$_v" ]
}

revb_tool_summary() {
  echo "KICAD_CLI=${KICAD_CLI:-<none>}"
  echo "KICAD_PYTHON=${KICAD_PYTHON:-<none>}"
  echo "KICAD_FOOTPRINTS=${KICAD_FOOTPRINTS:-<none>}"
  echo "FREECADCMD=${FREECADCMD:-<none>}"
}

if [ "${1:-}" = "--print" ]; then
  revb_tool_summary
fi
