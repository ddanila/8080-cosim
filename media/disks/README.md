# Juku disk images

Vendored public Juku raw disk images used by the FDC/EKDOS probes and Tier 2
software bring-up work. They are kept in tree so the emulator and HDL media
path have stable, checksum-identified inputs. Public availability does not by
itself establish a redistribution license; preserve the source and hash
metadata and assess applicable rights before redistributing the images.

## Provenance

| File | Source archive | Size | SHA-1 | SHA-256 | Role |
| --- | --- | ---: | --- | --- | --- |
| `JUKU1.CPM` | `https://arti.ee/juku/tarkvara/JUKU1.7Z` | 819200 | `e4508c3f2ef7e1a5c4c84451d1f207fd8a7e2751` | `859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27` | EKDOS/CP-M boot image; ROMBIOS `TDD` reaches `A>` in cosim |
| `JUKGAME1.CPM` | `https://arti.ee/juku/tarkvara/JUKU2.7Z` | 819200 | `efd6e83669777966d523d323ea61e0352eea88ff` | `659ac330083f20ef41495f54240c528342ba3d431c657f0686a265383e88095d` | Companion game disk image |
| `JUKPROG1.CPM` | `https://arti.ee/juku/tarkvara/JUKU2.7Z` | 819200 | `32708fd095be8ea50bf2ba185c6d5654e0ca3255` | `94670f3333b29e205c1586a0f52882aaa0f8cff2d45c3493676ce3ab263ae269` | Companion program disk image |
| `JUKPROG2.CPM` | `https://arti.ee/juku/tarkvara/JUKU2.7Z` | 819200 | `725233ba5f8943ff2778bf4d70dbf25f71a5854d` | `7e41d32f64a37ea2312ae81e73a6043888b97eb78d04ebacc53be2e4690a1520` | Companion program disk image |
| `JUKPROGX.CPM` | `https://arti.ee/juku/tarkvara/JUKU2.7Z` | 819200 | `7ac496b74bc5f0d6beeae5231b3f379b53ad8284` | `3ce19c094ee2801583c277fa6012d6aae983a696c9932d39f927fa3156b78e58` | Companion program disk image |
| `J3KUTIL4.JUK` | `https://elektroonikamuuseum.ee/failid/juku/tarkvara/J3KUTIL4.JUK` | 819200 | `fb8a5239cdd74eced3b0bb7ab8ec6e8b2092f4c3` | `d7a0b766a00c80ac487e24f48499386249534418ccb42739bae83a9e5a075de3` | Museum utility disk; first external EKDOS prompt proof before stronger `JUKU1.CPM` guard |

## Format

Each image is a raw MAME/Juku geometry image:

- 80 tracks
- 2 sides
- 10 sectors per track
- 512 bytes per sector
- 819200 bytes total

The `.CPM` extension comes from the public Arti archive. `cosim/juk_disk.c`
validates these by size and geometry, not by extension.

## Checks

```sh
(cd media/disks && sha256sum -c SHA256SUMS)
sync/juk_disk_check.sh
sync/ekdos_fdc_probe.py
```

`sync/ekdos_fdc_probe.py` defaults to `media/disks/JUKU1.CPM` and should report
`EKDOS A> PROMPT REACHED`.

The C and HDL FDC models keep these preservation inputs read-only by default.
Their ROMBIOS-derived 512-byte write-sector path is tested against a temporary
copy. To opt into persistence on a caller-created copy, use
`JUKU_DISK_WRITABLE=1` with cosim or `+disk_writable` with the HDL model; never
point a writable run at the tracked originals.
