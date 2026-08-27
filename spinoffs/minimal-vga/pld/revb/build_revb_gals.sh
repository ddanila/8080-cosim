#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
PLD="$ROOT/spinoffs/minimal-vga/pld/revb"
GALETTE="${GALETTE:-$ROOT/.tools/galette/bin/galette}"
UPDATE=0
[ "${1:-}" = "--update" ] && UPDATE=1
[ -x "$GALETTE" ] || {
  echo "Galette is missing; run $PLD/bootstrap_galette.sh" >&2
  exit 2
}
[ "$("$GALETTE" --version)" = "Galette 0.3.0" ] || {
  echo "expected Galette 0.3.0 at $GALETTE" >&2
  exit 2
}

vj_build_tmp="$(mktemp -d)"
trap 'rm -rf "$vj_build_tmp"' EXIT
for base in memory-u3 io-u2 video-hdec-u5 video-vdec-u6 video-ctrl-u7; do
  cp "$PLD/$base.pld" "$vj_build_tmp/"
  (cd "$vj_build_tmp" && "$GALETTE" "$base.pld")
done

for base in memory-u3 io-u2 video-hdec-u5 video-vdec-u6 video-ctrl-u7; do
  for ext in jed pin fus chp; do
    generated="$vj_build_tmp/$base.$ext"
    tracked="$PLD/$base.$ext"
    if [ "$UPDATE" = 1 ]; then
      install -m 0644 "$generated" "$tracked"
    else
      cmp "$generated" "$tracked" || {
        echo "$base.$ext is not reproducible; review then run $0 --update" >&2
        exit 1
      }
    fi
  done
done

python3 "$PLD/check_revb_gals.py"
echo "REVB-GAL-BUILD: PASS (Galette 0.3.0; five reproducible JEDECs)"
