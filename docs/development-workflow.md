# Development workflow

The canonical development branch for this repository is `master`.

- Work directly on `master` unless a temporary branch is unavoidable.
- Commit and push coherent intermediate progress promptly; do not accumulate a
  large unpublished reconstruction backlog.
- Push completed commits directly to `origin/master`. Pull requests are not
  part of the normal workflow for this repository.
- If work is created on a temporary branch, cherry-pick or fast-forward every
  adopted commit onto `master`, verify it there, and delete the temporary local
  and remote branch after adoption.
- Keep generated evidence reports and their authoritative source changes in the
  same commit so a remote checkout remains reproducible.
- Run the checks appropriate to the touched area before each push. At minimum,
  use `git diff --check`; connectivity changes also require `sync/check.sh`, and
  documentation/report changes require
  `python3 scripts/check_documentation_consistency.py`.

The repository may retain `main` only as historical remote state. New progress
belongs on `master`.

## HDL CI coverage contract

The HDL Actions workflow uses `ci/hdl-ci.json` to map changed paths to the nine
expensive HDL/LVS lanes. The selector is deliberately fail-open: shared machine
model paths, CI-control paths, an unknown path, or an unavailable diff run every
lane. A change confined to a declared subsystem runs only its owning lanes.

The optimization changes scheduling, not the full test inventory:

- `ci/check_hdl_ci.py` verifies that all 66 workflow entrypoints remain in the
  manifest, exist in the checkout, and select their owning lane.
- `ci/test_select_hdl_jobs.py` covers isolated, multi-area, unknown, control,
  documentation, and forced-full decisions.
- scheduled and tag runs force the complete suite; an unchanged nightly SHA is
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
