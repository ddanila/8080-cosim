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
  `python3 scripts/check_markdown.py` and
  `python3 scripts/check_documentation_consistency.py`.

The repository may retain `main` only as historical remote state. New progress
belongs on `master`.

## HDL CI coverage contract

The HDL Actions workflow uses `ci/hdl-ci.json` to map changed paths to the HDL/LVS lanes. The selector is deliberately fail-open: shared machine
model paths, CI-control paths, an unknown path, or an unavailable diff run every
lane once the workflow is triggered. The workflow’s own path filters run first;
a path outside those filters does not invoke the selector on a push. A change confined to a declared subsystem runs only its owning lanes.

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
path families must be included in the workflow trigger filters and receive an
explicit dependency rule. Within an invoked workflow, leaving a path
unclassified selects the full suite; it does not compensate for an omitted
workflow trigger.

## Reports and evidence

Use `scripts/regen_all.sh --check` for its selected fast generated reports and
`--deep --check` for its additional behavioral checks. These sets do not cover
every report; run the owning command for changed evidence. See
[regeneration scope](../sync/README.md#regenerating-reports) for optional sets
and index-relative freshness checking. Report writers own their
Markdown output; edit the writer and regenerate instead of appending a work log.
Photo hashes must validate the materialized bytes or the authenticated LFS
object identity, as required by the guard. Hosted photo inputs and cache scope
are declared in `.github/workflows/reports.yml`.

## Local CI gate

`scripts/ci_gate.sh` samples the latest 15 `master` workflow runs. For each
workflow, it selects the newest completed result excluding empty, cancelled
and skipped conclusions, and blocks only `failure`. Other conclusions,
including `timed_out`, do not block. Missing or unauthenticated `gh` and query
errors warn and skip; `CI_GATE=off` explicitly bypasses this gate.

The script does not pass `--repo`: it uses GitHub CLI's selected repository,
which can differ from the push destination in a fork. Select this repository
explicitly when invoking it:

```sh
GH_REPO=ddanila/8080-cosim scripts/ci_gate.sh
```

The same environment variable applies when the installed pre-push hook invokes
the gate. The gate neither waits for running jobs nor proves that every
workflow passed on the current commit. Inspect all triggered runs for the
pushed SHA before claiming CI success.

Preserve protocol, source and release assertions when repairing a failure.
Timing expectations live in `sync/ekdos_timing_expected.json`; update them only
for a justified implementation change and review the regenerated evidence.
