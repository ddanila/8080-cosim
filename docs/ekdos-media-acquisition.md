# EKDOS media acquisition gate

Status: **COSIM EKDOS PROMPT PROVEN WITH EXTERNAL MEDIA**

The factory boot target from Baltijets doc 003 is disk `JUKU-1`
(`ДГШ5.106.105`) in drive A, then `ROMBIOS 3.43` command sequence
`<T>, <D>, <D>` to the EKDOS `A>` prompt.

This repository must not vendor copyrighted EKDOS/CP-M disk images. The
cosim FDC path is therefore split into two repeatable checks:

1. `sync/juk_disk_check.sh` validates the raw `.juk` loader and WD1793
   read-sector behavior with synthetic media.
2. `EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py` runs the
   ROMBIOS boot sequence through an externally supplied image and, for
   disk-backed runs, requires the EKDOS `A>` prompt bitmap in VRAM.

The public/community request text for this image and the PROM dumps is tracked
in `docs/community-prom-media-request.md`.

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

## Transient Validation

A transient, non-vendored run with the museum/juku3000 EKDOS 2.30 utility disk
proved the cosim side reaches a live EKDOS prompt:

| Field | Value |
|---|---|
| Source URL | `https://elektroonikamuuseum.ee/failid/juku/tarkvara/J3KUTIL4.JUK` |
| Local policy | downloaded to `/tmp` only; not committed |
| Size | 819200 bytes |
| SHA-1 | `fb8a5239cdd74eced3b0bb7ab8ec6e8b2092f4c3` |
| Probe status | `EKDOS A> PROMPT REACHED` |
| Screen evidence | `52K EKDOS 2.30` and left-margin `A>` prompt |

This closes the cosim proof for an externally supplied EKDOS image. The exact
factory `JUKU-1` / `ДГШ5.106.105` image is still preferred for final factory
acceptance evidence, and the FDC behavior still needs to be ported into
`juku_top`.

## Verification Command

```sh
sync/juk_disk_check.sh
EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py
```

The probe report is written to `docs/ekdos-fdc-probe.md`. A valid image should
make the report say `Disk image loaded by cosim: yes` and read at least one
512-byte sector through WD1793 port `0x1F`. For disk-backed runs it must now
also report `EKDOS A> PROMPT REACHED`.
