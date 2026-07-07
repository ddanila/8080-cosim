#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 kicad/report_replica_bringup_verification.py
python3 kicad/report_replica_manufacturing_readiness.py fab/gerbers

if ! grep -q 'Status: \*\*READY TO UPLOAD\*\*' docs/replica-manufacturing-readiness.md; then
  echo "replica manufacturing readiness: NOT READY" >&2
  exit 3
fi

(cd fab/gerbers && sha256sum -c SHA256SUMS)
(cd fab/gerbers/upload && sha256sum -c SHA256SUMS.txt)

echo "replica manufacturing readiness: READY TO UPLOAD"
