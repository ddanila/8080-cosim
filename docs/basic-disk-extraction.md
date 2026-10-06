# BASIC disk extraction

Status: **ARTIFACTS GENERATED; ALLOCATION MAPPING UNRESOLVED**

This generated report extracts BASIC-relevant CP/M files from the
vendored Arti Juku disk images. The directory-backed extractor uses the
visible directory window at `0x5000`, 4 KiB allocation blocks, a
four-side-track system area, and a hard-coded transcription of `TRANS` from
`ref/ekdos-source/EKDOS30.ASM`. Raw candidates are fixed-offset slices;
their allocation mapping is not resolved by this extractor. The script does
not read or verify the assembly source’s current translation table.
Entries are grouped by filename without separating CP/M users and sorted
only by the one-byte EX field. S2, missing/duplicate extents and allocation
consistency are not validated, so directory-backed output is provisional.

## Command

Run from the repository root with Python 3 (standard library only) and
`sha256sum`. Verify retained identities before the writer replaces the
extracted files, checksum manifest, README and this report.

```sh
(cd media/disks && sha256sum -c SHA256SUMS)
(cd ref/extracted-software && sha256sum -c SHA256SUMS)
python3 scripts/extract_basic_disk_files.py
```

## Generated artifacts

| Path | Source |
| --- | --- |
| ref/extracted-software/JUKPROG2_JBASIC.COM | `JUKPROG2.CPM` directory `JBASIC.COM` |
| ref/extracted-software/JUKPROG2_JBASIC_live_candidate.COM | `JUKPROG2.CPM` raw live-load candidate at `0x2DE00` |
| ref/extracted-software/JUKU1_JBASIC_raw_candidate.COM | `JUKU1.CPM` raw candidate at `0x67000` |

## Extraction observations

| Disk | Source | Name | Bytes | Blocks | First bytes | Strings | SHA256 |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| JUKPROG2.CPM | directory | `JBASIC.COM` | 8320 | 0x15 0x16 0x17 | `c3 40 13 c3 32 11 c3 c0` | - | 73cc53939c501c382e610e4e81dbf19cc5154d83545757b5155ccf70a2351d9c |
| JUKU1.CPM | directory | `JBASIC.COM` | 8320 | 0x31 0x32 0x33 | `e5 e5 e5 e5 e5 e5 e5 e5` | - | 4ff96f220dec96b4312f76e2e09ca0f83eec3129c6c27c5396ddc600ba0cf79d |
| JUKPROG2.CPM | raw 0x2DE00 | `JBASIC.COM live-load candidate` | 8320 | - | `c3 05 01 86 1c 31 ff b3` | `BASIC`@0x05AD, `READY`@0x0576, `ERROR`@0x0569 | b1ae68b464c245a888c8e6bbf07037960f5a92d4e968c956c6205a1de6cfc545 |
| JUKU1.CPM | raw 0x67000 | `JBASIC.COM candidate` | 8320 | - | `c3 05 01 86 1c 31 ff b3` | `BASIC`@0x05AD, `READY`@0x0576, `ERROR`@0x0569 | 85522b5b662b8c353c2aad8167bea0b5fc4a94ec71cc87ea91a7a2c551255c4d |

## Scope

- `JUKPROG2_JBASIC.COM` is the directory-backed extraction. It differs
  from the separately preserved raw live-load candidate; the directory/raw
  allocation mapping remains unresolved.
- The [launch probe](ekdos-jbasic-command-probe.md) checks the raw
  JUKPROG2 candidate's entry prefix (at least six bytes), BASIC-related
  RAM strings and the visible `READY` oracle. It does not require an
  exact whole-file comparison against loaded RAM.
- The 8,320-byte JUKU1 directory extraction begins with 4,096 `E5` bytes;
  its remaining 4,224 bytes contain other data. It is not wholly erased.
  Its raw candidate has a jump header and BASIC-related strings; those
  signatures alone do not establish that it is a working executable.
- Artifact hashes identify the emitted bytes, not a validated CP/M
  allocation mapping or physical-disk qualification.
- Successful generation means the source files were readable, both
  directories contained a `JBASIC.COM` entry, and the outputs were written.
  The writer does not assert expected hashes, payload lengths, entry bytes,
  or string signatures; the observations above need separate validation.
