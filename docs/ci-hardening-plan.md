# CI hardening plan

Status date: **2026-07-20**. Handwritten execution plan, not a generated
report. Owner: repo maintainer; any session (human or agent) may execute an
item, but items are independent commits and CI must be green between them.

## Progress

- [x] 2. Shared LFS-aware photo-hash helper.
- [x] 1. One-command report regeneration.
- [x] 4. Timing expectations as data.
- [x] 3. CI-aware pre-push gate.
- [x] 5. Workflow concurrency groups.
- [ ] 6. Narrow `reports.yml` path gates.

## Motivation

On 2026-07-20 all three workflows were red for ~12 hours. Root causes, each
mapping to one improvement below:

1. Generated evidence docs went stale after model changes and nobody had a
   one-command way to resweep them (`d94-reconstruction-constraints.md`,
   `serial-handoff.md`, the EKDOS reference trio) — improvement 1.
2. A new photo-evidence guard (`kicad/check_d93_irq_conditioner.py`) hashed
   raw JPEG bytes and failed on CI where `ref/photos/**/*.jpg` are
   unmaterialized Git LFS pointers; the pointer-tolerant boilerplate existed
   only as per-script copies that the new script missed — improvement 2.
3. The autonomous routing loop kept pushing onto a red master for ~12 hours;
   nothing forced a look at CI state — improvement 3.
4. The EKDOS timing expectations are hardcoded dicts inside
   `sync/ekdos_timing_reference.py`, so every intentional model-driven timing
   shift needs a code edit and the failure cannot distinguish "regression"
   from "expected shift" — improvement 4.

## Common workflow (applies to every item)

1. `git pull --rebase` immediately before starting and again before each push
   (the routing agent is active on another machine).
2. One commit per improvement, pushed separately; watch the triggered
   workflows go green before starting the next item.
3. Anything touching `docs/` or `PLAN.md`: run
   `python3 scripts/check_documentation_consistency.py` locally before
   committing.

## 1. `scripts/regen_all.sh` — one-command report regeneration

Stale generated docs are the top cause of red CI; the generator list exists
only implicitly inside two workflow files.

Design:

- New `scripts/regen_all.sh` (bash, `set -euo pipefail`), two tiers:
  - Default (fast, under a minute): every pure-Python generator from
    `.github/workflows/reports.yml`, in the workflow's step order. Order
    matters: `scripts/report_owner_measurement_shortlist.py` runs after its
    upstream reports; the video-slot group is d2 -> d94 -> d41 -> video_slot.
    Source the list verbatim from `reports.yml`; do not reinvent it.
  - `--deep`: adds the cosim/HDL-based doc writers from `hdl.yml`
    (`sync/ekdos_fdc_probe.py`, `sync/ekdos_jbasic_command_probe.py`,
    `sync/ekdos_timing_reference.py`, `sync/ekdos_checkpoint_reference.py`,
    `sync/ekdos_ioseq_reference.py`, `sync/juku_top_checkpoint_load_check.py`,
    `sync/juku_top_checkpoint_resume_probe.py`,
    `scripts/report_juku_top_fdc_alignment.py`,
    `scripts/report_d6_runtime_path.py`, plus the doc-writing shell guards
    `sync/fdc_check.sh` and `sync/d96_check.sh`). Requires gcc + iverilog;
    takes minutes.
  - `--check`: after regenerating, `git diff --exit-code -- docs/ ref/` so
    CI-style callers get a non-zero exit on drift. Without it, print the
    drift list and exit 0.
- Header comment: "This list mirrors .github/workflows/reports.yml and
  hdl.yml; update all three together."

Steps:

1. Write the script; extract the generator sequence verbatim from
   `reports.yml` steps and the `hdl.yml` behavioral steps.
2. Add a syntax check for the script to the list in `ci.yml`.
3. Document: one paragraph in `sync/README.md` ("after changing
   `kicad/juku.board.json`, timing-relevant HDL, or any `report_*.py`, run
   `scripts/regen_all.sh` — `--deep` if HDL/cosim behavior changed — and
   commit the drift"); add the same one-liner near this plan's reference in
   `PLAN.md` so the autonomous agent sees it.

Verify: run twice on a clean tree — the first run must produce zero drift
(proves list and order correct against green CI); the second proves
idempotence. `--check` must exit 0. Run the doc-consistency check because of
the `PLAN.md` edit.

## 2. Shared LFS-aware photo-hash helper

The pointer-tolerant hashing exists as four or more divergent copies; the
2026-07-20 generic-job break was a new script missing the boilerplate.

Design:

- New module `kicad/photo_evidence.py`:
  - `photo_sha256(path) -> tuple[str, bool]` — `(digest, is_lfs_pointer)`;
    when the file is an unmaterialized LFS pointer, return the pointer's
    `oid sha256` (which equals the content hash) and `True`.
  - `jpeg_dimensions(path) -> list[int]` — SOF parse; callers must skip it
    when only a pointer is present.
  - Docstring explains the CI/LFS contract.
- All known consumers live in `kicad/` and run as `python3 kicad/foo.py`, so
  a plain sibling import works; if a consumer outside `kicad/` turns up, use
  a two-line `sys.path` shim rather than relocating the module.

Steps:

1. `grep -rn "git-lfs.github.com/spec" kicad/ scripts/ sync/` to find all
   copies (known: `check_fdc_unused_pins.py`, `check_fdc_recovery_counter.py`,
   `check_fdc_read_clock_toggle.py`, `check_d93_irq_conditioner.py`).
2. Create the module (lift the logic from `check_d93_irq_conditioner.py`,
   which already handles both the hash and the dimensions-skip).
3. Replace each inline copy with the import; keep each script's error-message
   wording unchanged (grep each message string before touching it — some are
   asserted elsewhere).
4. Add the module to the `py_compile` list in `ci.yml`.

Verify: run all affected checks with real photos (all PASS); then simulate CI
by swapping the referenced photos for `git cat-file blob HEAD:<path>` output,
re-run all affected checks (still PASS), restore, and confirm
`git status` is clean for `ref/photos/`.

## 3. CI-aware pre-push gate

The routing loop pushed onto a red master for ~12 hours; the gate caps the
damage at one commit instead of hours.

Design:

- New `scripts/ci_gate.sh`:
  - If `gh` is missing or unauthenticated (`gh auth status`), print a
    one-line warning and exit 0 — never brick a machine without gh.
  - Otherwise fetch the latest completed run per workflow on master
    (`gh run list --branch master --json workflowName,conclusion,status,headSha --limit 15`)
    and reduce to the newest completed run per workflow.
  - Any `failure` -> print which workflow/commit is red plus a
    `gh run view` hint, exit 1.
  - Escape hatch: `CI_GATE=off` skips entirely; the failure message documents
    the override so a blocked agent or human knows it exists.
- Wire it into the existing `.githooks/pre-push`, before the deep-cosim step
  (fail fast: no point running a multi-minute check before being blocked).

Steps:

1. Read `.githooks/pre-push` and confirm how hooks are activated
   (`git config core.hooksPath`) so the gate runs on both machines.
2. Write `scripts/ci_gate.sh`; add the hook call; add a syntax check for it
   to `ci.yml`.
3. Note near this plan's reference in `PLAN.md`: pushes are gated on green
   master CI; fix or explicitly override with `CI_GATE=off`, never stack on
   red.

Verify: run the script on green master (exit 0); feed the reducer canned JSON
with a failure (exit 1, correct message); test the gh-absent path with a
stripped `PATH`; then a real push confirming the hook fires and passes.

Accepted caveat: the gate only helps the next push after CI turns red — a
just-pushed breakage still lands. That is fine; it bounds the damage.

## 4. Timing expectations as data with a deliberate update path

Keeps the forcing function (CI still fails hard on any timing shift), changes
the medium from a code edit to a reviewable data diff.

Design:

- New committed `sync/ekdos_timing_expected.json` holding what is now
  `EXPECTED_FIRSTS` and `EXPECTED_IRQS` (string keys such as `"IN 0x1F"`).
- `sync/ekdos_timing_reference.py` changes:
  - Load expectations from the JSON; drop the hardcoded dicts.
  - Plain run: compare and fail exactly as today on mismatch, but append to
    the message: "if the model change is intentional, run
    sync/ekdos_timing_reference.py --update and commit the diff".
  - `--update`: write measured values back to the JSON, regenerate the doc,
    exit 0.
- `hdl.yml`: add the JSON to the `git diff --exit-code` list in the
  "Check boot report freshness" step so an uncommitted `--update` fails CI.

Steps:

1. `grep -rn "8956831\|9039953" .` first — confirm the values live only in
   the script and the generated doc.
2. Extract the dicts to JSON; implement load and `--update`; keep the doc
   output byte-identical in the no-drift case.
3. Update `hdl.yml` as above.

Verify: plain run on current master passes with a byte-identical doc; corrupt
one JSON value -> plain run fails with the new hint; `--update` restores it
and leaves an empty diff.

## Execution order

2 -> 1 -> 4 -> 3. Item 2 is smallest and item 1's verification benefits from
stable checks; item 4 touches `hdl.yml` (watch the slow HDL workflow once);
item 3 last because it changes push behavior for the other machine and needs
the hook-activation investigation.

# CI cost reduction

Added **2026-07-20**. Separate motivation from items 1-4: those keep CI green,
these cut GitHub Actions minutes. The autonomous routing loop pushes ~80-120
commits/day in bursts, and the workflows have no cost controls, so a large
fraction of billed minutes is spent on runs that are either instantly obsolete
or triggered on paths the workflow does not read. Both items preserve full
regression coverage — they only stop redundant work.

Items 5 and 6 are independent; either order. Both are single-workflow-file
edits with no behavioral change to what actually runs, so CI-green-between is
trivial to confirm.

## 5. Concurrency groups with `cancel-in-progress`

No workflow has a `concurrency` block, so a burst of loop pushes starts a run
per commit and every run finishes even when a newer commit has already
superseded it. Measured 2026-07-20: 552 commits in the prior 7 days.

Design:

- Add to `ci.yml`, `hdl.yml`, and `reports.yml`, at top level (after `on:`):

  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```

- Keyed per workflow and per ref, so a burst on `master` only cancels stale
  `master` runs of the same workflow.

Steps:

1. Add the block to each of the three workflow files.

Verify: push two commits within a few seconds; confirm the first workflow run
shows `cancelled` and only the newest completes.

Accepted caveat: with `cancel-in-progress`, intermediate commits inside a burst
are not each individually verified — only the tip of each burst runs to
completion. This is the right trade for a latest-wins autonomous loop; if a
future need for per-commit bisectable green arises, scope the cancel to
non-default branches only.

Interaction with item 3 (CI-aware pre-push gate): superseded runs become
`cancelled`, not `failure`, so the gate does not misread them as red. When
item 3 is built, its "newest completed run per workflow" reducer must treat a
`cancelled` newest run as *no signal* (advance to the newest conclusive run)
rather than as green — it already keys blocking on `failure`, so this is a
"skip cancelled" refinement, not a behavior change.

## 6. Narrow the `reports.yml` over-broad path gates

`reports.yml` is the heaviest workflow (Git LFS pull + ~40 report
regenerations). Its `push`/`pull_request` `paths` include `scripts/**` and
`ref/**`, but the routing loop churns two files under those globs that no
`reports.yml` step reads:

- `scripts/check_documentation_consistency.py` (a `ci.yml` check, never run
  here), matched by `scripts/**`.
- `ref/routing/*.json`, matched by `ref/**`.

Result measured 2026-07-20: 425 of 552 commits (77%) triggered the full
`reports.yml` suite for nothing.

Design:

- Add negation patterns after the positive globs, in **both** the `push.paths`
  and `pull_request.paths` lists:

  ```yaml
  - 'scripts/**'
  - '!scripts/check_documentation_consistency.py'
  - 'ref/**'
  - '!ref/routing/**'
  ```

- Negations must follow the positive pattern they refine; a change touching
  only excluded paths then does not trigger the workflow.

Steps:

1. `grep -rn "ref/routing\|check_documentation_consistency" .github/workflows/reports.yml`
   to confirm no step reads either path (expected: no matches).
2. Edit both `paths` lists identically.

Verify: a routing-style commit (only `ref/routing/*.json` +
`scripts/check_documentation_consistency.py`) does **not** trigger
`reports.yml`; a real report-input change (e.g. a `report_*.py` or
`ref/firmware/**`) still does.

## Not pursued: `push` vs `pull_request` double-run

A standard optimization is to scope `push:` to `master` so PR branches run only
via the `pull_request` event instead of twice. This repo creates no branches or
PRs — everything lands directly on `master` — so the `pull_request:` triggers
never fire and no double-run exists to eliminate. The triggers are inert; drop
them only as future cosmetic cleanup, not for cost.
