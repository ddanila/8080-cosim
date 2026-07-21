#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 kicad/report_replica_bringup_verification.py
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
