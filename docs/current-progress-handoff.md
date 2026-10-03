# Current progress and publication handoff

Recorded: 2026-10-03.

The user's working policy is to consolidate and publish progress on the
repository's main branch, currently named `master`, in
`/home/ddanila/fun/8080-cosim`. The destination is the user's fork,
`https://github.com/ddanila/8080-cosim`. Further work should happen in that
checkout; no new feature branch or pull request is requested.

## Progress to preserve

- The exact `.009` drawing and board-photo reviews, corrected logical model,
  source and routed PCB snapshots, and measurement backlog are present in the
  main working files. Physical connectivity and fabrication remain on hold.
- The release evidence packet, manifest, reproducible archive builder, PROM and
  EPROM identity checks, raw DRC/ERC evidence inventory, and archive checksum
  sidecar are present. The packet and archive freshness checks pass.
- Eight Windows-host files that existed in newer form only in the temporary
  clone were restored to the main checkout after verifying each destination
  still matched its main-branch baseline: the Windows CI workflow, client
  documentation, application source, import list, cross-build script, runtime
  check, resource generator, and floppy packager.
- Additional main-checkout A8B and R35 photo-review observations and the photo
  endpoint guard were preserved. Differing existing report snapshots were
  preserved in the main checkout instead of overwriting them wholesale.

The 161 earlier progress commits through `d9870fed` have been imported from
`/tmp/juku-progress-20260929` into this checkout's `master` history. Both the
previous local baseline and the fetched remote `master` were verified as
ancestors before advancing the branch while preserving working files.
The remaining photo-review notes, guard improvements, report snapshots, and
this handoff are consolidated in the publication commit on `master`.

## Review artifacts

- [Evidence packet](replica-release-evidence-package.md)
- [Evidence manifest](replica-release-evidence-manifest.json)
- Archive: `fab/evidence/juku-replica-release-evidence.zip`
- Transfer checksum: `fab/evidence/juku-replica-release-evidence.zip.sha256`

The archive is a design-hold review snapshot. It is not a Gerber upload or
fabrication approval. Although generated `fab/` files are normally ignored,
this publication explicitly tracks the archive, checksum sidecar, raw DRC/ERC
inputs, and fabrication review reports needed to check the evidence packet.
Accidental generator output from `--help/` is retained locally under ignored
`fab/diagnostics/accidental-help-output/`; it is not project source.

## Validation and remaining limitations

On 2026-10-03, the photo endpoint/package guard passed with 81 anchors,
25 grid pins, and zero mismatches. The release evidence packet freshness
check and archive content/checksum check both passed. These checks establish
that the review package matches the recorded working files; they do not
resolve the design holds or refresh every historical report snapshot.

The previous Git-directory write restriction and GitHub DNS failure were
resolved in this session. Publication uses a normal fast-forward push to
`origin/master` in the user's fork, followed by remote commit verification.
No feature branch or pull request is part of this handoff.

## CI repair after publication

The published snapshot exposed outdated guard and report assumptions. The
repair accepts KiCad's numbered and name-only pad-net formats, brings HDL
D38.5 and D34.4 onto the source-proved LATCH_SIG and TIMING_TAG2 conductors,
and checks D41 package supplies explicitly. Photo guards retain the unmetered
D96.11/D28.11 candidate as a source conflict requiring continuity. Report
writers now preserve the additional D30, D36, D59 and IE10 photo observations.

LVS, all boot regression levels including self clocking, video readout, report
and PROM validation steps, and documentation consistency passed locally.
Package reporting now writes an incomplete-package hold for absent Gerbers
instead of crashing; tests also require unexpected tool errors to propagate.
The evidence packet and portable archive were regenerated for this repair.
Remote CI must be verified on the publication commit before CI is declared green.
