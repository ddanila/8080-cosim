# BASIC disk extraction

Status: **BASIC DISK FILES EXTRACTED**

This generated report extracts BASIC-relevant CP/M files from the
vendored Arti Juku disk images. The directory-backed extractor uses the
visible directory window at `0x5000`, 4 KiB allocation blocks, a
four-side-track system area, and the `TRANS` sector order from
`ref/ekdos-source/EKDOS30.ASM`.

## Generated artifacts

| Path | Source | SHA256 |
| --- | --- | --- |
| ref/extracted-software/JUKPROG2_JBASIC.COM | `JUKPROG2.CPM` directory `JBASIC.COM` | 73cc53939c501c382e610e4e81dbf19cc5154d83545757b5155ccf70a2351d9c |
| ref/extracted-software/JUKU1_JBASIC_raw_candidate.COM | `JUKU1.CPM` raw candidate at `0x67000` | 85522b5b662b8c353c2aad8167bea0b5fc4a94ec71cc87ea91a7a2c551255c4d |

## Extraction checks

| Disk | Source | Name | Bytes | Blocks | First bytes | Strings | SHA256 |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| JUKPROG2.CPM | directory | `JBASIC.COM` | 8320 | 0x15 0x16 0x17 | `c3 40 13 c3 32 11 c3 c0` | - | 73cc53939c501c382e610e4e81dbf19cc5154d83545757b5155ccf70a2351d9c |
| JUKU1.CPM | directory | `JBASIC.COM` | 8320 | 0x31 0x32 0x33 | `e5 e5 e5 e5 e5 e5 e5 e5` | - | 4ff96f220dec96b4312f76e2e09ca0f83eec3129c6c27c5396ddc600ba0cf79d |
| JUKU1.CPM | raw 0x67000 | `JBASIC.COM candidate` | 8320 | - | `c3 05 01 86 1c 31 ff b3` | `BASIC`@0x05AD, `READY`@0x0576, `ERROR`@0x0569 | 85522b5b662b8c353c2aad8167bea0b5fc4a94ec71cc87ea91a7a2c551255c4d |

## Disposition

- `JUKPROG2_JBASIC.COM` is the best current directory-backed disk BASIC
  executable candidate. It has a CP/M-style jump header and is suitable
  for the next EKDOS command-launch probe.
- The `JUKU1.CPM` directory entry for `JBASIC.COM` remains important
  catalog evidence, but this extractor maps it to erased bytes. The raw
  candidate at `0x67000` has a CP/M jump header plus `BASIC`, `READY`,
  and `ERROR` strings, so it is preserved separately and explicitly
  marked as a candidate.
- This report does not claim a BASIC prompt yet; it creates stable
  inputs for the prompt oracle work.
