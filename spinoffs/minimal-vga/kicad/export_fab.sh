#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb}"
OUT="${2:-fab/minimal-vga}"
KCLI="$("scripts/find-kicad-cli.sh")"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"

if [ ! -f "$BOARD" ]; then
  echo "No routed PCB yet: $BOARD" >&2
  echo "Create the Rev A .kicad_pcb before exporting fab files." >&2
  exit 2
fi

KCLI_VERSION=$("$KCLI" --version)
PCBNEW_VERSION=$("$KICAD_PYTHON" - <<'PY'
import pcbnew
print(pcbnew.GetBuildVersion())
PY
)
KCLI_MAJOR=${KCLI_VERSION%%.*}
PCBNEW_MAJOR=${PCBNEW_VERSION%%.*}
if [ "$KCLI_MAJOR" != "$PCBNEW_MAJOR" ]; then
  echo "KiCad CLI/Python mismatch: CLI $KCLI_VERSION, pcbnew $PCBNEW_VERSION." >&2
  echo "Use a Python pcbnew build matching the KiCad CLI that owns this board." >&2
  exit 2
fi
if ! "$KICAD_PYTHON" - "$BOARD" <<'PY'
import pcbnew
import sys

board = pcbnew.LoadBoard(sys.argv[1])
if board is None:
    raise SystemExit(1)
print(
    f"KiCad toolchain coherent: pcbnew {pcbnew.GetBuildVersion()}, "
    f"{len(list(board.Footprints()))} footprints"
)
PY
then
  echo "Matching pcbnew could not load $BOARD; fabrication export is blocked." >&2
  exit 2
fi

mkdir -p "$OUT"

python3 spinoffs/minimal-vga/kicad/report_rev_a_source_model.py \
  spinoffs/minimal-vga/kicad/rev-a-physical.board.json \
  "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_schematic_intent.py \
  spinoffs/minimal-vga/kicad/rev-a-physical.board.json \
  "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_router_readiness.py \
  "$OUT" >/dev/null
BEHAVIORAL_REPORT="$OUT/behavioral-readiness.md"
BEHAVIORAL_OK=0
if [ "${MINIMAL_VGA_REUSE_BEHAVIORAL_REPORT:-0}" = "1" ]; then
  if [ ! -s "$BEHAVIORAL_REPORT" ] \
      || ! grep -q 'Status: \*\*BEHAVIORAL REGRESSIONS PASS\*\*' "$BEHAVIORAL_REPORT" \
      || ! grep -q -- '- Exit code: 0' "$BEHAVIORAL_REPORT" \
      || ! grep -q -- '- Expected markers missing: 0' "$BEHAVIORAL_REPORT"; then
    echo "Requested behavioral-report reuse, but the existing report is not a complete pass." >&2
    exit 6
  fi
  NEWER_BEHAVIORAL_INPUT=$(find \
    spinoffs/minimal-vga/sim spinoffs/minimal-vga/hdl spinoffs/minimal-vga/sync \
    hdl sync cosim roms \
    spinoffs/minimal-vga/kicad/rev-a-physical.board.json \
    spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch \
    spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb \
    spinoffs/minimal-vga/kicad/check_rev_a_*.sh \
    -type f -newer "$BEHAVIORAL_REPORT" -print -quit)
  if [ -n "$NEWER_BEHAVIORAL_INPUT" ]; then
    echo "Requested behavioral-report reuse, but an input is newer: $NEWER_BEHAVIORAL_INPUT" >&2
    exit 6
  fi
  echo "Reusing current passing behavioral report: $BEHAVIORAL_REPORT"
  BEHAVIORAL_OK=1
elif python3 spinoffs/minimal-vga/kicad/report_rev_a_behavioral_readiness.py "$OUT" >/dev/null; then
  BEHAVIORAL_OK=1
fi
if [ "$BEHAVIORAL_OK" != "1" ]; then
  if [ "${MINIMAL_VGA_ALLOW_BEHAVIORAL_EXPORT:-0}" != "1" ]; then
    echo "VJUGA behavioral aggregate failed; fab export blocked." >&2
    echo "Report: $OUT/behavioral-readiness.md" >&2
    echo "Set MINIMAL_VGA_ALLOW_BEHAVIORAL_EXPORT=1 only for a design-held debug export." >&2
    exit 5
  fi
  echo "WARNING: continuing a design-held debug export after behavioral failure." >&2
fi

if [ "${MINIMAL_VGA_ALLOW_ERC_EXPORT:-0}" != "1" ]; then
  if ! KICAD_CLI="$KCLI" python3 spinoffs/minimal-vga/kicad/report_rev_a_erc_readiness.py \
      spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch \
      "$OUT" >/dev/null; then
    echo "KiCad ERC failed for spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch; fab export blocked." >&2
    echo "Report: $OUT/erc-readiness.md" >&2
    echo "Set MINIMAL_VGA_ALLOW_ERC_EXPORT=1 only for debug exports." >&2
    exit 4
  fi
fi

if [ "${MINIMAL_VGA_ALLOW_DRC_EXPORT:-0}" != "1" ]; then
  if ! "$KCLI" pcb drc --severity-error --exit-code-violations \
      --output "$OUT/drc-report.txt" "$BOARD" >/dev/null; then
    echo "KiCad DRC failed for $BOARD; fab export blocked." >&2
    echo "Report: $OUT/drc-report.txt" >&2
    echo "Set MINIMAL_VGA_ALLOW_DRC_EXPORT=1 only for debug exports." >&2
    exit 3
  fi
fi

KICAD_CLI="$KCLI" python3 spinoffs/minimal-vga/kicad/report_rev_a_fab_readiness.py \
  "$BOARD" \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_routing_geometry.py \
  "$BOARD" \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_routing_disposition.py \
  "$BOARD" \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_mounting_holes.py \
  "$BOARD" \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_diagnostic_leds.py \
  "$BOARD" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_power_budget.py \
  "$BOARD" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  spinoffs/minimal-vga/docs/rev-a-power-budget.md \
  "$OUT" >/dev/null

mkdir -p "$OUT/gerbers" "$OUT/drill"
mkdir -p "$OUT/assembly" "$OUT/review"
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py \
  "$BOARD" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  "$OUT/assembly"
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_socket_fit.py \
  "$BOARD" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_socket_insertion_policy.py \
  "$BOARD" \
  "$OUT" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_mechanical_fit.py \
  "$BOARD" \
  "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_manual_rows.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_cpn_consistency.py "$OUT" >/dev/null
"$KCLI" pcb export gerbers \
  --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  -o "$OUT/gerbers/" "$BOARD"
"$KCLI" pcb export drill --format excellon --drill-origin absolute -o "$OUT/drill/" "$BOARD"
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_drill_readiness.py \
  "$BOARD" \
  "$OUT/drill/rev-a-physical.drl" \
  "$OUT" >/dev/null
"$KCLI" sch export pdf \
  --black-and-white \
  --output "$OUT/review/rev-a-physical-schematic.pdf" \
  spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch
"$KCLI" pcb export pdf \
  --layers F.Fab,F.SilkS,F.CrtYd,Edge.Cuts \
  --common-layers Edge.Cuts \
  --black-and-white \
  --mode-single \
  --output "$OUT/review/rev-a-assembly-front.pdf" \
  "$BOARD"
"$KCLI" pcb export pdf \
  --layers B.Fab,B.SilkS,B.CrtYd,Edge.Cuts \
  --common-layers Edge.Cuts \
  --black-and-white \
  --mirror \
  --mode-single \
  --output "$OUT/review/rev-a-assembly-back.pdf" \
  "$BOARD"
"$KCLI" pcb export pos \
  --side both \
  --format csv \
  --units mm \
  --output "$OUT/assembly/rev-a-position.csv" \
  "$BOARD"
cp spinoffs/minimal-vga/kicad/rev-a.bom.csv "$OUT/rev-a.engineering-bom.csv"
cp spinoffs/minimal-vga/kicad/rev-a-jlcpcb-cpn-checklist.csv "$OUT/assembly/"
cp spinoffs/minimal-vga/kicad/rev-a-assembly-orientation-notes.md "$OUT/assembly/"
cp spinoffs/minimal-vga/kicad/fab-notes.md "$OUT/"
python3 spinoffs/minimal-vga/kicad/package_rev_a_upload.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_orientation_notes.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_fab_package_integrity.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_external_gerber_review.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_manual_install_disposition.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_vendor_order_checklist.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_order_upload_runbook.py "$OUT" >/dev/null
python3 spinoffs/minimal-vga/kicad/report_rev_a_order_readiness.py "$OUT" >/dev/null
echo "Exported fab package to $OUT"
