#!/usr/bin/env bash
# TF.1 / D1.28 — cpu-card Z80 placement sweep. The cpu card's A8 net is a
# DETERMINISTIC 2-layer fan-out constraint (12/12 stochastic route attempts fail
# identically at the current placement), so re-rolling the router is the wrong tool.
# Instead we grid-search the Z80 (U1) x-position x rotation headlessly: for each
# candidate we regenerate the PCB, gate on placement-class DRC (reject cheaply, no
# routing), then route with a short attempt budget and check TOTAL DRC. The first
# candidate that reaches 0 violations / 0 unconnected wins; its coordinates are then
# folded back into gen_revb_pcb.py permanently (not left in the environment).
#
# Skips (not fails) when the CAD/route toolchain is absent, like the other rev B
# steps. Ranges are overridable for a widened search:
#   SWEEP_XS="25 27 .. 45"  SWEEP_ROTS="90 270"  FR_ATTEMPTS=3  sweep_cpu_place.sh
set -uo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
R="spinoffs/minimal-vga"
. "$R/kicad/revb/env.sh"

CARD=cpu
REF="${SWEEP_REF:-U1}"
XS="${SWEEP_XS:-25 27 29 31 33 35 37 39 41 43 45}"
ROTS="${SWEEP_ROTS:-90 270}"
export FR_ATTEMPTS="${FR_ATTEMPTS:-3}"   # a routable placement routes in 1-2 tries

revb_have KICAD_PYTHON || { echo "  SKIP  sweep: no KICAD_PYTHON"; exit 0; }
[ -f "${FREEROUTING_JAR:-.tools/freerouting/freerouting.jar}" ] || {
  echo "  SKIP  sweep: no freerouting.jar (set FREEROUTING_JAR)"; exit 0; }

echo "== cpu placement sweep: ref=$REF  x={$XS}  rot={$ROTS}  attempts=$FR_ATTEMPTS =="
tried=0
for rot in $ROTS; do
  for x in $XS; do
    tried=$((tried + 1))
    export REVB_SWEEP_REF="$REF" REVB_SWEEP_X="$x" REVB_SWEEP_ROT="$rot"
    "$KICAD_PYTHON" "$R/kicad/revb/gen_revb_pcb.py" "$CARD" >/dev/null 2>&1

    if ! python3 "$R/kicad/revb/check_revb_drc.py" "$CARD" --placement >/dev/null 2>&1; then
      echo "  x=$x rot=$rot : placement DRC FAIL (skip route)"
      continue
    fi
    if ! sh "$R/kicad/revb/route_revb_pcb.sh" "$CARD" >/dev/null 2>&1; then
      echo "  x=$x rot=$rot : placement OK, route did not converge"
      continue
    fi
    if python3 "$R/kicad/revb/check_revb_drc.py" "$CARD" --total >/dev/null 2>&1; then
      echo ""
      echo "  *** WINNER: $REF x=$x rot=$rot  ->  cpu routes 0/0 ***"
      echo "  fold into gen_revb_pcb.py:  \"$REF\": ($x, <keep Y>, $rot)"
      echo "  (candidate #$tried)"
      unset REVB_SWEEP_REF REVB_SWEEP_X REVB_SWEEP_ROT
      exit 0
    fi
    echo "  x=$x rot=$rot : routed but total DRC still dirty"
  done
done

unset REVB_SWEEP_REF REVB_SWEEP_X REVB_SWEEP_ROT
echo ""
echo "  no candidate in the swept grid reached 0/0."
echo "  widen: SWEEP_XS / SWEEP_ROTS, or fall back to one generator-authored A8 track."
exit 1
