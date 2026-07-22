#!/usr/bin/env bash
set -euo pipefail

if [[ ${CI_GATE:-} == off ]]; then
  echo "ci_gate: skipped because CI_GATE=off"
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ci_gate: warning: gh not found; skipping master CI check" >&2
  exit 0
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ci_gate: warning: gh is not authenticated; skipping master CI check" >&2
  exit 0
fi

if ! runs_json=$(
  gh run list --branch master \
    --json workflowName,conclusion,status,headSha,databaseId --limit 15
); then
  echo "ci_gate: warning: could not query GitHub Actions; skipping master CI check" >&2
  exit 0
fi

# gh returns newest-first. Skip non-completed and cancelled/skipped entries so
# each workflow is judged by its newest conclusive completed run.
failures=$(python3 -c '
import json
import sys

runs = json.load(sys.stdin)
seen = set()
for run in runs:
    workflow = run.get("workflowName", "unknown workflow")
    if workflow in seen or run.get("status") != "completed":
        continue
    conclusion = run.get("conclusion", "")
    if conclusion in {"", "cancelled", "skipped"}:
        continue
    seen.add(workflow)
    if conclusion == "failure":
        print("\t".join((
            workflow,
            str(run.get("headSha", "unknown")),
            str(run.get("databaseId", "unknown")),
        )))
' <<<"$runs_json")

if [[ -n $failures ]]; then
  echo "ci_gate: latest conclusive master CI is red:" >&2
  while IFS=$'\t' read -r workflow sha run_id; do
    [[ -z $workflow ]] && continue
    echo "  - $workflow at ${sha:0:12}" >&2
    echo "    inspect: gh run view $run_id --log-failed" >&2
  done <<<"$failures"
  echo "ci_gate: push blocked; fix CI or explicitly override once with CI_GATE=off git push" >&2
  exit 1
fi

echo "ci_gate: latest conclusive master CI runs have no failures"
