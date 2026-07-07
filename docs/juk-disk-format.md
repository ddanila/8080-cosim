# Juku Raw Disk Image Format

This repository uses the raw MAME Juku disk image layout as the cosim disk
backend target. MAME software-list images often use `.juk`; the vendored Arti
images use `.CPM`, but the byte layout is the same and is validated by size.

Source: MAME `src/lib/formats/juku_dsk.cpp` (`FLOPPY_JUKU_FORMAT`),
`https://github.com/mamedev/mame/blob/master/src/lib/formats/juku_dsk.cpp`,
cross-checked 2026-07-06.

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

## Guard

Run:

```sh
sync/juk_disk_check.sh
```

The guard creates synthetic single- and double-sided images, validates CHS
sector reads, and checks out-of-range addressing failures. It does not ship or
validate any copyrighted EKDOS image.

## Next Use

`cosim/juku_fdc.c` consumes this loader for the disk-backed WD1793 model. Use
`sync/ekdos_fdc_probe.py` for the ROMBIOS boot-path probe; it defaults to the
vendored `media/disks/JUKU1.CPM`. Use `JUKU_DISK=/path/to/image` when invoking
`cosim/trace` directly.
