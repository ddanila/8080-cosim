# Bundled CP/M development A: media

`CPM3.IMG` is the 409,600-byte `development-a` profile from the pinned
`cpm-plus-juku` revision in `manifest.json`. It extends the full tools profile
with ED, SID, PATCH, HEXCOM and HELLO source/HEX examples: 33 files, 190 KiB free.

`cpm3-report.json` records per-file identities and provenance. The manifest
binds both the image and report hashes. `LICENSE.TXT` accompanies binary
redistribution. When rebuilding, replace the image and report together, then
update the manifest's source revision, image size/hash, and report hash.

The floppy transfer packager, `tools/package-jukuwin-floppy.py`, verifies these
identities and bundles `CPM3.IMG` with its license. The portable host folder
created by `tools/package-jukuhost-windows.py` contains no disk image. The
Windows CI release uses the floppy bundle, so publishing it needs neither a
sibling checkout nor live downloads of CP/M source archives.

To rebuild the media, run `make out/cpm-plus-juku-dev.img` in the pinned
`cpm-plus-juku` checkout. Copy `out/cpm-plus-juku-dev.img` to `CPM3.IMG` and
`out/cpm-plus-juku-dev.report.json` to `cpm3-report.json` in this directory,
then update the manifest as described above. The Windows build does not
refresh these files. B: music/application media is not included in the
floppy bundle.
