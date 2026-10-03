# Development workflow

The canonical development branch for this repository is `master`.

- Work directly on `master` and push coherent progress to the user's fork at
  `origin/master`. Feature branches and pull requests are outside this
  repository's normal workflow.
- Keep generated evidence reports and their authoritative source changes in the
  same commit so a remote checkout remains reproducible.
- Run the checks appropriate to the touched area before each push. At minimum,
  use `git diff --check`; connectivity changes also require `sync/check.sh`, and
  documentation/report changes require
  `python3 scripts/check_documentation_consistency.py`.

The repository may retain `main` only as historical remote state. New progress
belongs on `master`.

## HDL CI coverage contract

The HDL Actions workflow uses `ci/hdl-ci.json` to map changed paths to the HDL/LVS lanes. The selector is deliberately fail-open: shared machine
model paths, CI-control paths, an unknown path, or an unavailable diff run every
lane. A change confined to a declared subsystem runs only its owning lanes.

The selector schedules the bounded hosted lanes described in
[CI budgets](../ci/README.md); a full hosted run does not execute every local
test:

- `ci/check_hdl_ci.py` verifies that all workflow entrypoints remain in the
  manifest, exist in the checkout, and select their owning lane.
- `ci/test_select_hdl_jobs.py` covers isolated, multi-area, unknown, control,
  documentation, and forced-full decisions.
- scheduled and tag runs force all hosted lanes; an unchanged nightly SHA is
  skipped only if a previous scheduled run for that exact SHA succeeded.
- `workflow_dispatch` defaults to `full`; `changed` evaluates the latest commit
  (`HEAD^..HEAD`) and is available for selector diagnostics.
- the final `results` job fails if a selected lane did not succeed or an
  unselected lane unexpectedly ran.

Run the CI guardrails locally after changing the workflow, manifest, or selector:

```sh
python3 ci/check_hdl_ci.py
python3 -m unittest -v ci.test_select_hdl_jobs
```

New HDL tests must be added to the owning job and its `entrypoints` list. New
path families must receive an explicit dependency rule. Leaving a path
unclassified is safe but intentionally expensive because it selects the full
suite.

## Reports and evidence

Use `scripts/regen_all.sh --check` for its selected fast generated reports and
`--deep --check` for its additional behavioral checks. These sets do not cover
every report; run the owning command for changed evidence. See
[regeneration scope](../sync/README.md#fast-behavioral-checks) for optional sets
and index-relative freshness checking. Report writers own their
Markdown output; edit the writer and regenerate instead of appending a work log.
Photo hashes must validate the materialized bytes or the authenticated LFS
object identity, as required by the guard. Hosted photo inputs and cache scope
are declared in `.github/workflows/reports.yml`.

`scripts/ci_gate.sh` checks the latest conclusive CI results on `master`.
Preserve protocol, source and release assertions when repairing a failure.
Timing expectations live in `sync/ekdos_timing_expected.json`; update them only
for a justified implementation change and review the regenerated evidence.
