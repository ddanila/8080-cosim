# Juku Raw Disk Image Format

This repository uses the raw MAME Juku disk image layout as the cosim disk
backend target. MAME software-list images often use `.juk`; the vendored Arti
images use `.CPM`, but the byte layout is the same and is validated by size.

Source: MAME `src/lib/formats/juku_dsk.cpp` (`FLOPPY_JUKU_FORMAT`) at commit
`40d8c5c343efc497524832d59a6d0e2b8e59376b`,
`https://github.com/mamedev/mame/blob/40d8c5c343efc497524832d59a6d0e2b8e59376b/src/lib/formats/juku_dsk.cpp`,
cross-checked 2026-07-17.

## Geometry

| Field | Value |
|---|---:|
| Tracks | 80 |
| Sectors per track | 10 |
| Sector size | 512 bytes |
| Sector IDs | 1-10 |
| Encoding | MFM |
| Single-sided size | 409600 bytes |
| Double-sided size | 819200 bytes |

The raw byte order used by `cosim/juk_disk.c` is:

```text
offset = (((track * heads) + head) * 10 + (sector - 1)) * 512
```

`heads` is inferred from file size: 1 for 409600-byte images, 2 for
819200-byte images. Other sizes are rejected.

## Reconstructed MFM revolution

The sector-only file does not contain gaps, address marks, CRC bytes, missing
clock transitions, or rotational phase. For the WD1793 Read Track command, the
C and HDL shims deterministically rebuild the decoded bytes described by MAME:
2,000 ns cells give 100,000 cells or 6,250 decoded bytes per 200 ms revolution;
the descriptor uses gaps 1/2/3 of 32/22/35 bytes. Each of the ten sectors has
12 zero sync bytes, three decoded `0xA1` missing-clock sync bytes, an `0xFE`
ID field and CRC, gap 2, another sync run, an `0xFB` data field and CRC, and
gap 3. The remaining 128 bytes are the end gap.

MAME marks the Juku gap values as unverified. Consequently the rebuilt stream
is a reproducible logical representation of the raw image and its recorded
geometry, not evidence for the original factory-written gap contents or flux
timing.

For Write Track, the WD1793 consumes formatter control bytes rather than the
decoded stream returned by Read Track. The vendored
`ref/wd1772-vg93/fd179x-01-datasheet.pdf` Type-III and IBM System 34 tables
define the transformation: `F5` writes missing-clock `A1`, `F6`
writes missing-clock `C2`, and `F7` writes two generated CRC bytes. Replacing
each pair of recorded CRC bytes with one `F7` makes the canonical ten-sector
input 6,230 CPU writes long while still occupying all 6,250 decoded byte times.
The flat backend commits each completed normal-data sector as it is parsed, so
a Force Interrupt leaves earlier sectors changed and later ones untouched.

The raw file cannot encode arbitrary ID order/geometry, data-address-mark type,
damaged headers, or noncanonical gap/flux content. The loader therefore keeps
an explicit normal/deleted bit for each sector. WD1793 Write Sector `a0` and
representable Write Track `FB`/`F8` fields update it; Read Sector and
reconstructed Read Track consume it. By default, closing and reopening the raw
image resets every mark to normal because no such bits exist on disk.

For workflows that need deleted marks to survive a process restart, both
backends accept an explicit companion file: set `JUKU_DISK_DELETED_MARKS` for
`cosim/trace`, or pass `+disk_deleted_marks=<path>` to the HDL model. The file
is exactly 1,600 bytes, one binary `0` or `1` for every fixed
`((track * 2 + side) * 10 + sector - 1)` slot. A writable mount creates and
updates it; a read-only mount can consume an existing file. This sidecar is a
simulation representation and is never embedded in or inferred from a raw
`.juk`/`.CPM` payload. Other unrepresentable complete revolutions set
behavioral WRITE FAULT instead of being falsely serialized as an unchanged
valid raw image.

## Guard

Run:

```sh
sync/juk_disk_check.sh
```

The guard creates synthetic single- and double-sided images, validates CHS
sector reads, checks default session reset and explicit-sidecar reopen
persistence, and checks out-of-range addressing failures. `sync/fdc_check.sh`
also writes the sidecar in one HDL process and reloads it read-only in another.
It does not ship or validate any copyrighted EKDOS image.

## Next Use

`cosim/juku_fdc.c` consumes this loader for the disk-backed WD1793 model. Use
`sync/ekdos_fdc_probe.py` for the ROMBIOS boot-path probe; it defaults to the
vendored `media/disks/JUKU1.CPM`. Use `JUKU_DISK=/path/to/image` when invoking
`cosim/trace` directly, and set `JUKU_DISK_DELETED_MARKS=/path/to/marks` only
when cross-run mark persistence is wanted.
