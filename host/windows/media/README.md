# Bundled CP/M development A: media

`CPM3.IMG` is the 409,600-byte `development-a` profile from the pinned
`cpm-plus-juku` revision in `manifest.json`. It extends the full tools profile
with ED, SID, PATCH, HEXCOM and HELLO source/HEX examples: 33 files, 190 KiB free.

`cpm3-report.json` records per-file identities and provenance. The manifest
binds both the image and report hashes. `LICENSE.TXT` accompanies binary
redistribution. Refresh all three identities when rebuilding the image.

The CI build packages these pinned bytes, so publishing a Windows artifact
needs neither a sibling checkout nor live downloads of CP/M source archives.
The reproducible upstream build command is `make out/cpm-plus-juku-dev.img`.
B: music/application media is deliberately not included in the host bundle.
