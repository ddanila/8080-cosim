# EKDOS media acquisition gate

Status: **VENDORED JUKU1 PROMPT PROVEN**

The factory target from Baltijets doc 003 is disk `JUKU-1`
(`ДГШ5.106.105`) in drive A, followed by `ROMBIOS 3.43` command sequence
`<T>, <D>, <D>` and the EKDOS `A>` prompt.

## Current artifacts

| Artifact | Role | Provenance |
| --- | --- | --- |
| `media/disks/JUKU1.CPM` | default EKDOS boot image | public Arti `JUKU1.7Z`; SHA256 `859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27` |
| `media/disks/J3KUTIL4.JUK` | independent museum utility-disk cross-check | Elektroonikamuuseum; SHA256 `d7a0b766a00c80ac487e24f48499386249534418ccb42739bae83a9e5a075de3` |
| `ref/ekdos-source/EKDOS30.ASM` | monitor/FDC call and geometry reference | public Arti source; SHA256 `9d0d06147597b4039bbbfdb31b98adc17168da2e354962ec12423b385e0ced3d` |
| `media/system/` | CP/M/EKDOS system binaries | museum `JUKUSYS.ZIP`; not small-PROM programming data |

The raw image geometry is 80 tracks, 10 sectors per track, 512 bytes per sector,
and one or two sides (409,600 or 819,200 bytes). The `.CPM` extension is an
archive convention; the loader validates size and geometry.

## Proven boundary

- `sync/ekdos_fdc_probe.py` boots the default `JUKU1.CPM` through the C oracle
  and reaches the visible `A>` prompt.
- `docs/juku-top-fdc-verilator-probe.md` and
  `sync/juku_top_fdc_prompt_check.sh` guard the uninterrupted structural-HDL
  path to the same prompt.
- `docs/juku-top-jbasic-verilator-probe.md` extends that path through disk
  `JBASIC.COM` to visible `READY`.
- `docs/vendored-disk-catalog.md` and `docs/basic-disk-extraction.md` own the
  current disk directory and BASIC extraction evidence.

This closes functional public-media acquisition for Tier 2. It does not prove
that `JUKU1.CPM` is byte-identical to a surviving factory
`ДГШ5.106.105` disk, and none of these files supplies D8/D94 programming truth.
Validated physical D2/D6 tables were acquired independently from the disk media.
A fresh physical factory-disk dump remains useful preservation evidence but is
not a fabrication blocker.

## Verification

```sh
(cd ref/ekdos-source && sha256sum -c SHA256SUMS)
(cd media/disks && sha256sum -c SHA256SUMS)
(cd media/system && sha256sum -c SHA256SUMS)
python3 scripts/report_ekdos_source_inspection.py
python3 scripts/report_vendored_disk_catalog.py
python3 scripts/extract_basic_disk_files.py
sync/juk_disk_check.sh
sync/ekdos_fdc_probe.py
sync/juku_top_fdc_prompt_check.sh
```

For a new raw image, record source, filename, geometry, and SHA256 in
`media/disks/README.md`, then run with
`EKDOS_PROBE_DISK=/path/to/image sync/ekdos_fdc_probe.py` before considering it
adopted.
