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
