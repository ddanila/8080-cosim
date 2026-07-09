# EKDOS media acquisition gate

Status: **VENDORED JUKU1 PROMPT PROVEN**

The factory boot target from Baltijets doc 003 is disk `JUKU-1`
(`ДГШ5.106.105`) in drive A, then `ROMBIOS 3.43` command sequence
`<T>, <D>, <D>` to the EKDOS `A>` prompt.

The required EKDOS/CP-M media is now vendored under `media/disks/`. The cosim
FDC path is split into two repeatable checks:

1. `sync/juk_disk_check.sh` validates the raw disk loader and WD1793
   read-sector behavior with synthetic media.
2. `sync/ekdos_fdc_probe.py` runs the ROMBIOS boot sequence through the vendored
   `media/disks/JUKU1.CPM` image by default and requires the EKDOS `A>` prompt
   bitmap in VRAM.

The public/community request text for this image and the PROM dumps is tracked
in `docs/community-prom-media-request.md`.

The related public CP/M/EKDOS system binaries from the museum `JUKUSYS.ZIP`
archive are vendored under `media/system/` with checksum manifests. They are
reference system binaries, not a substitute for the still-missing small-PROM
programming files.

The public EKDOS source references from Arti's software mirror are vendored
under `ref/ekdos-source/`. `EKDOS30.ASM` is useful when checking ROMBIOS/FDC
call conventions and disk geometry; it is source evidence, not a boot image.
`docs/ekdos-source-inspection.md` is generated from that source and guards the
stable monitor/FDC constants used by the current probes.

The vendored Arti and museum disk images are also cataloged by
`scripts/report_vendored_disk_catalog.py`. The generated
`docs/vendored-disk-catalog.md` report records visible CP/M directory entries
and identifies disk-side BASIC candidates. `J3KUTIL4.JUK` is cataloged alongside
the CP/M images; `JUKU1.CPM` contains `JBASIC.COM`, while `JUKPROG2.CPM`
contains `JBASIC.COM`, `B80.COM`, `BRUN.COM`, `BASCOM.COM`, `BASCOM.DOK`, and
`BASLIB.REL`.
`scripts/extract_basic_disk_files.py` then vendors the strongest BASIC launch
inputs under `ref/extracted-software/` and records the extraction boundary in
`docs/basic-disk-extraction.md`.

## Required Image

| Field | Requirement |
|---|---|
| Label | `JUKU-1` / `ДГШ5.106.105` EKDOS boot disk |
| Format | MAME/Juku raw disk image (`.CPM` archive extension, `.juk` geometry) |
| Size | 409600 bytes (single-sided) or 819200 bytes (double-sided) |
| Geometry | 80 tracks, 10 sectors/track, 512 bytes/sector |
| Vendored path | `media/disks/JUKU1.CPM` |
| Override env | `EKDOS_PROBE_DISK=/path/to/image` or `EKDOS_PROBE_DISK=none` |

## Candidate Sources

- MAME software-list media (`hash/juku.xml`) for Juku EKDOS 2.x / CP-M disks.
- The juku3000 ecosystem and any mirrored `.juk`/raw media references.
- A fresh physical dump of the factory `JUKU-1` disk, if a surviving disk is
  available.

Record any later replacement source, filename, SHA-256, and software-list label
in `media/disks/README.md`.

## Museum Utility Disk Validation

The museum/juku3000 EKDOS 2.30 utility disk is now vendored and proves the
cosim side reaches a live EKDOS prompt:

| Field | Value |
|---|---|
| Source URL | `https://elektroonikamuuseum.ee/failid/juku/tarkvara/J3KUTIL4.JUK` |
| Vendored path | `media/disks/J3KUTIL4.JUK` |
| Size | 819200 bytes |
| SHA-1 | `fb8a5239cdd74eced3b0bb7ab8ec6e8b2092f4c3` |
| SHA-256 | `d7a0b766a00c80ac487e24f48499386249534418ccb42739bae83a9e5a075de3` |
| Probe status | `EKDOS A> PROMPT REACHED` |
| Screen evidence | `52K EKDOS 2.30` and left-margin `A>` prompt |

This was the first cosim proof for a disk-backed EKDOS image. The stronger
vendored `JUKU1.CPM` proof below is now the default media gate; the current
HDL prompt path is guarded in `docs/fdc-readiness.md`.

A follow-up run with Arti's public `JUKU1.7Z` found a stronger factory-media
candidate. The archive extracts to a single 819200-byte raw image `JUKU1.CPM`;
the existing loader accepts it by geometry, and ROMBIOS reaches the same EKDOS
`A>` prompt after `<T>, <D>, <D>`. This image is now vendored.

| Field | Value |
|---|---|
| Source URL | `https://arti.ee/juku/tarkvara/JUKU1.7Z` |
| Archive contents | `JUKU1.CPM` |
| Vendored path | `media/disks/JUKU1.CPM` |
| Image size | 819200 bytes |
| SHA-256 | `859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27` |
| SHA-1 | `e4508c3f2ef7e1a5c4c84451d1f207fd8a7e2751` |
| Probe status | `EKDOS A> PROMPT REACHED` |
| Screen evidence | `A>` prompt bitmap found at `x=0`, `y=70` |
| FDC evidence | 27 command/status writes, 80 status reads, 10752 data reads |

This closes the public-source cosim proof for a `JUKU1` boot image. Remaining
work is to carry disk-backed FDC behavior into `juku_top` and, for museum-grade
provenance, compare against a fresh physical `ДГШ5.106.105` disk dump if one
surfaces.

## Source Reference

| Field | Value |
|---|---|
| Source URL | `https://arti.ee/juku/tarkvara/EKDOS30.ASM` |
| Vendored path | `ref/ekdos-source/EKDOS30.ASM` |
| Size | 14336 bytes |
| SHA-256 | `9d0d06147597b4039bbbfdb31b98adc17168da2e354962ec12423b385e0ced3d` |
| Role | 52K EKDOS 2.30 CP/M BIOS source; documents monitor entry points, disk parameters, and floppy handler interface |

The same source directory also keeps Arti's `axb.asm` CP/M BIOS skeleton as a
nearby reference file, with hashes in `ref/ekdos-source/SHA256SUMS`.
The generated inspection confirms the source-level ROMBIOS floppy entries
`FLOPPY=0xFF53`, `RWFLOPPY=0xFF59`, 160 side-tracks, and a 40-entry CP/M
translation table matching 10 physical 512-byte sectors per side-track.

## Verification Command

```sh
(cd ref/ekdos-source && sha256sum -c SHA256SUMS)
python3 scripts/report_ekdos_source_inspection.py
python3 scripts/report_vendored_disk_catalog.py
python3 scripts/extract_basic_disk_files.py
sync/juk_disk_check.sh
sync/ekdos_fdc_probe.py
```

The probe report is written to `docs/ekdos-fdc-probe.md`. It should say
`Disk image loaded by cosim: yes`, read at least one 512-byte sector through
WD1793 port `0x1F`, and report `EKDOS A> PROMPT REACHED`.
