# EKDOS media acquisition gate

Status: **WAITING FOR EXTERNAL IMAGE**

The factory boot target from Baltijets doc 003 is disk `JUKU-1`
(`ДГШ5.106.105`) in drive A, then `ROMBIOS 3.43` command sequence
`<T>, <D>, <D>` to the EKDOS `A>` prompt.

This repository must not vendor copyrighted EKDOS/CP-M disk images. The
cosim FDC path is therefore split into two repeatable checks:

1. `sync/juk_disk_check.sh` validates the raw `.juk` loader and WD1793
   read-sector behavior with synthetic media.
2. `EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py` runs the
   ROMBIOS boot sequence through an externally supplied image.

## Required Image

| Field | Requirement |
|---|---|
| Label | `JUKU-1` / `ДГШ5.106.105` EKDOS boot disk |
| Format | MAME/Juku raw `.juk` image |
| Size | 409600 bytes (single-sided) or 819200 bytes (double-sided) |
| Geometry | 80 tracks, 10 sectors/track, 512 bytes/sector |
| Local env | `EKDOS_PROBE_DISK=/path/to/image.juk` |
| Repo policy | Do not commit the image |

## Candidate Sources

- MAME software-list media (`hash/juku.xml`) for Juku EKDOS 2.x / CP-M disks.
- The juku3000 ecosystem and any mirrored `.juk` media references.
- A fresh physical dump of the factory `JUKU-1` disk, if a surviving disk is
  available.

Record the source, filename, SHA-256, and software-list label in a local note or
order log when an image is obtained. Keep the image outside the git tree, or in
an ignored local artifact directory.

## Verification Command

```sh
sync/juk_disk_check.sh
EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py
```

The probe report is written to `docs/ekdos-fdc-probe.md`. A valid image should
make the report say `Disk image loaded by cosim: yes` and read at least one
512-byte sector through WD1793 port `0x1F`. The remaining milestone is stronger:
screen/VRAM evidence that the run reaches the factory `A>` prompt.
