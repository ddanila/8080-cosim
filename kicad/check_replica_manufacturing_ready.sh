#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f fab/gerbers/upload/juku-replica-gerbers-drill.zip ]; then
  echo "replica manufacturing readiness: DESIGN HOLD (local fabrication ZIP absent; tracked verification is historical; regenerate after remaining design changes)" >&2
  exit 3
fi
if [ ! -f fab/gerbers/source-board.sha256 ] ||
   [ "$(cat fab/gerbers/source-board.sha256)" != "$(sha256sum kicad/juku_routed.kicad_pcb | awk '{print $1}')" ]; then
  echo "replica manufacturing readiness: DESIGN HOLD (fabrication files are not stamped for the current routed PCB)" >&2
  exit 3
fi

python3 kicad/report_replica_bringup_verification.py
"$(scripts/find-kicad-python.sh)" kicad/check_d56_owner_timing_routes.py
"$(scripts/find-kicad-python.sh)" kicad/check_d40_1mhz_route.py
python3 kicad/report_main_board_erc_parity.py || {
  status=$?
  if [ "$status" -ne 3 ]; then
    exit "$status"
  fi
  true
}
python3 kicad/report_replica_manufacturing_readiness.py fab/gerbers

(cd fab/gerbers && sha256sum -c SHA256SUMS)
(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)

if grep -q 'Status: \*\*RELEASED FOR UPLOAD\*\*' docs/replica-manufacturing-readiness.md; then
  echo "replica manufacturing readiness: RELEASED FOR UPLOAD"
  exit 0
fi

echo "replica manufacturing readiness: DESIGN HOLD (package checksums pass; do not upload)" >&2
exit 3
