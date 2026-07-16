# EKDOS source inspection

Status: **PASS**

This generated report inspects the vendored Arti `EKDOS30.ASM` source
for constants that matter to the ROMBIOS/EKDOS/FDC path. It intentionally
does not try to assemble the historical source; some source lines have
archive/OCR-era wrapping damage, so this check only uses stable `EQU`
labels and `TRANS` tables.

## Source

| Field | Value |
| --- | --- |
| File | `ref/ekdos-source/EKDOS30.ASM` |
| SHA256 | `9d0d06147597b4039bbbfdb31b98adc17168da2e354962ec12423b385e0ced3d` |
| Lines | `708` |

## Monitor Interface Constants

| Label | Value | Meaning |
| --- | ---: | --- |
| `ROM` | `0xFF50` | ROMBIOS cold-start loader base |
| `FLOPPY` | `0xFF53` | ROMBIOS floppy handler entry |
| `START` | `0xFF56` | loader for `<A>` sectors to CCP |
| `RWFLOPPY` | `0xFF59` | ROMBIOS read/write floppy entry |
| `RAMDISKSEL` | `0xFF5C` | RAM-drive probe/format entry |
| `RDNO` | `2` | EKDOS RAM-drive number |
| `DKRD` | `0x11` | EKDOS read-sector request code |
| `DKWR` | `0x12` | EKDOS write-sector request code |
| `VIARV` | `10` | retries loaded into `RCOUNT` for disk I/O |

## Floppy Parameter Block

| Field | Value |
| --- | ---: |
| `NDISKS` | `3` |
| `TRACKS` | `160` logical side-tracks = `80` cylinders x 2 sides |
| physical sectors/track inferred from `TRANS` | `10` x 512-byte sectors |
| CP/M logical sectors/track from `TRANS` | `40` x 128-byte sectors |
| logical bytes/side-track | `5120` |
| raw `JUKU1.CPM` size | `819200` bytes |

## Floppy Handler Work Area

| Label | Value | Meaning |
| --- | ---: | --- |
| `TYP` | `0xD600` | monitor floppy work-area base |
| `SEKDSK` | `0xD61A` | selected drive |
| `SEKSEC` | `0xD61D` | selected sector |
| `HSTACT` | `0xD623` | host-sector cache active flag |
| `HSTWRT` | `0xD624` | host-sector cache dirty flag |
| `UNACNT` | `0xD625` | unallocated-write counter |
| `RCOUNT` | `0xD62A` | retry counter |
| `MEMADR` | `0xD62E` | DMA address field |
| `STAK` | `0xD2FC` | EKDOS temporary stack outside RAM-drive aperture |

## Sector Translation

| Table | Entries | Min | Max | Matches 1..40 |
| --- | ---: | ---: | ---: | --- |
| `TRANS` | `40` | `1` | `40` | `True` |
| `TRANS1` | `40` | `1` | `40` | `True` |

## Parser Boundary

The source contains a few visibly wrapped/collided historical lines; those
are left as source text rather than repaired in place. Skipped required-like
lines:

- none

## Failures

- none
