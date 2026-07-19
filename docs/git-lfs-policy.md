# Git LFS policy

Original reference photographs under `ref/photos/**/*.jpg` are preserved with
Git LFS. They are evidence inputs: keep the original bytes immutable, add new
files for new captures, and do not recompress or replace an existing path.

The repository intentionally does not materialize every LFS object in routine
CI. GitHub charges each Actions download to the repository owner's LFS
bandwidth, even when the object is unchanged or a later step fails. The reports
workflow therefore:

1. checks out LFS pointer files;
2. restores `.git/lfs/objects` from the Actions cache, keyed by the required
   pointer contents; and
3. runs `git lfs pull --include=...` for only the photographs read by its
   validators and report generators.

On a cache hit, `git lfs pull` verifies and materializes the cached objects
without downloading them again. On a cache miss, only absent required objects
are downloaded. The cache is an optimization, never the authoritative copy.

## Maintaining the CI allowlist

When a CI script begins reading another photograph's bytes, add that path (or
the narrowest stable directory pattern) to both places in
`.github/workflows/reports.yml`:

- the `hashFiles(...)` arguments used for the cache key; and
- the `git lfs pull --include=...` list.

Keep the two lists identical. A validator that only reads a text manifest,
registration record, or LFS pointer does not require the corresponding image
to be added. Prefer an exact file path when a report reads only one or two
images from a larger evidence set.

After changing the allowlist, test from a pointer-only checkout and run every
consumer of the newly included photographs. `git lfs ls-files --size` can be
used to audit the resulting object count and download size.

## Local use

A normal clone may materialize all current LFS files. To avoid that for a new
checkout:

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/ddanila/8080-cosim.git
cd 8080-cosim
git lfs pull --include="ref/photos/juku-pcb-2/*.jpg"
```

To obtain every original photograph later, run:

```sh
git lfs pull
```

Local `git lfs prune` only removes safe local cache copies; it does not reduce
GitHub's stored objects or billing. Do not rewrite published history merely to
optimize LFS usage. Storage growth should instead be controlled by keeping
originals immutable and avoiding accidental duplicate imports.

## GitHub settings and monitoring

- Keep **Include Git LFS objects in archives** disabled unless source ZIP and
  tarball users explicitly require the photographs. Archive downloads count
  toward LFS bandwidth when inclusion is enabled.
- Review LFS storage and bandwidth in GitHub **Settings → Billing & Licensing**.
- Treat unusual bandwidth growth as a CI/download-frequency problem first;
  inspect workflows for blanket `lfs: true`, unrestricted `git lfs pull`, or
  repeated clean-runner downloads before considering data removal.
