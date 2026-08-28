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

if [ -d "$PWD/.tools/bin" ]; then
  PATH="$PWD/.tools/bin:$PATH"
  export PATH
fi

: "${KICAD_CLI:=$(sh scripts/find-kicad-cli.sh 2>/dev/null || true)}"
: "${KICAD_PYTHON:=$(sh scripts/find-kicad-python.sh 2>/dev/null || true)}"
[ -n "${KICAD_CLI:-}" ] || [ ! -x "$PWD/.tools/bin/kicad-cli" ] || KICAD_CLI="$PWD/.tools/bin/kicad-cli"
[ -n "${KICAD_PYTHON:-}" ] || [ ! -x "$PWD/.tools/bin/kicad-python" ] || KICAD_PYTHON="$PWD/.tools/bin/kicad-python"

# Prefer a CLI whose major version matches pcbnew. A newer system pcbnew can save a
# board that the repository's older fallback CLI cannot open; silently mixing those
# tools made the first four-layer Video DRC report an empty/invalid JSON file.
if [ -n "${KICAD_PYTHON:-}" ] && [ -n "${KICAD_CLI:-}" ]; then
  _pcbnew_major="$($KICAD_PYTHON -c 'import pcbnew; print(pcbnew.Version().split(".")[0])' 2>/dev/null || true)"
  _cli_major="$($KICAD_CLI --version 2>/dev/null | sed 's/\..*//' || true)"
  if [ -n "$_pcbnew_major" ] && [ "$_pcbnew_major" != "$_cli_major" ]; then
    for _cli_candidate in /usr/bin/kicad-cli /usr/local/bin/kicad-cli; do
      [ -x "$_cli_candidate" ] || continue
      _candidate_major="$($_cli_candidate --version 2>/dev/null | sed 's/\..*//' || true)"
      if [ "$_candidate_major" = "$_pcbnew_major" ]; then
        KICAD_CLI="$_cli_candidate"
        break
      fi
    done
  fi
fi

if [ -z "${KICAD_FOOTPRINTS:-}" ]; then
  # Derive from the resolved kicad-cli app bundle (glob-free, so this stays safe
  # even when sourced under zsh, which errors on unmatched globs).
  _bundle_fp=""
  case "$KICAD_CLI" in
    */KiCad.app/Contents/MacOS/kicad-cli)
      _bundle_fp="${KICAD_CLI%/MacOS/kicad-cli}/SharedSupport/footprints" ;;
  esac
  _system_fp=""
  case "$KICAD_CLI" in /usr/bin/*|/usr/local/bin/*) _system_fp=/usr/share/kicad/footprints ;; esac
  for _d in \
    "$_bundle_fp" \
    "$_system_fp" \
    "$PWD/.tools/apt-root/usr/share/kicad/footprints" \
    /usr/share/kicad/footprints \
    "$HOME/Applications/KiCad.app/Contents/SharedSupport/footprints" \
    /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints
  do
    if [ -n "$_d" ] && [ -d "$_d" ]; then KICAD_FOOTPRINTS="$_d"; break; fi
  done
fi

: "${FREECADCMD:=$(command -v freecadcmd 2>/dev/null || true)}"
[ -n "${FREECADCMD:-}" ] || [ ! -x "$PWD/.tools/bin/freecadcmd" ] || FREECADCMD="$PWD/.tools/bin/freecadcmd"
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
