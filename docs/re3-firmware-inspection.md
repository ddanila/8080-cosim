# К155РЕ3 firmware inspection

Status: **PASS**

This generated report preserves the tracked owner-scan РЕ3 programming
tables under `ref/firmware/` and keeps their role bounded. The files are
real factory programming-table excerpts, but current board evidence says
they are **not** the processor-module D8 `.039` or D94 `.092` contents.

## Command

```sh
scripts/report_re3_firmware_inspection.py
sync/reference_artifact_check.sh
```

## Shape Checks

| Check | Result |
| --- | --- |
| `.113` byte count is 32 | PASS |
| `.117` byte count is 32 | PASS |
| `.113` matches the scanned sparse 14h-17h one-cold walk | PASS |
| `.117` matches the scanned 08h-17h four-row one-cold dwell | PASS |
| Both tables use only `FF`, `07`, `0B`, `0D`, `0E` | PASS |
| The two scanned tables are distinct | PASS |
| Neither scanned table matches physical D8 or D94 | PASS |
| Physical D8 supersedes and differs from the historical reconstruction | PASS |

## Tables

| Programmed drawing | Primary use | Row summary | SHA256 |
| --- | --- | --- | --- |
| `ДГШ5.106.113` | `ДГШ5.106.103` family | `00-13:FF, 14:07, 15:0B, 16:0D, 17:0E, 18-1F:FF` | `05b582e19bed47c70374859de41c7fb4ce648a6f0b895059f9cf963c5496cb13` |
| `ДГШ5.106.117` | `ДГШ5.106.103` family | `00-07:FF, 08-0B:07, 0C-0F:0B, 10-13:0D, 14-17:0E, 18-1F:FF` | `3c431fdc0005a865aba209a026a3e75cbc1af9bdf1d5d8fc9953954238205f18` |

## Artifact Hashes

| File | Size | SHA256 |
| --- | ---: | --- |
| `BAS0.HEX` | 6273 | `fc8514a64e9524738936e65dffd48f90d17762576a743a1fb84f1dbe65b9a34e` |
| `BAS1.HEX` | 6273 | `cd42a74a5df7a34693ba2a99ef06c9e80ab7fa317669fffa55652317fd4ada16` |
| `BAS2.HEX` | 6273 | `4ee0617d9df24eb7f551b1e40e5e5ef5c75288f5aaa202dce5872da7423a0444` |
| `BAS3.HEX` | 6273 | `530985f784e6b9fe3517d4cb55abc9f5aed7fd65cb84d0b30898caaf58e9a909` |
| `JUKUROM0.HEX` | 8192 | `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596` |
| `JUKUROM1.HEX` | 8192 | `35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817` |
| `Juku_К155РЕ3_firmware.pdf` | 2779146 | `acf0136d7ef5ddded0a67b9617d5f6e75a3222788668451dbcf85fdd82c50ed0` |
| `README.md` | 2205 | `c894020252087a626ff76be2c52e3caed53ec54e19a88448549dce26d5bf04fa` |
| `re3_dgsh5.106.113.hex` | 96 | `05b582e19bed47c70374859de41c7fb4ce648a6f0b895059f9cf963c5496cb13` |
| `re3_dgsh5.106.117.hex` | 96 | `3c431fdc0005a865aba209a026a3e75cbc1af9bdf1d5d8fc9953954238205f18` |

## Interpretation Boundary

- `.113` and `.117` are tracked because they came from the owner-scan
  `Juku_К155РЕ3_firmware.pdf` and are useful PROM-lineage evidence.
- They are not exported as D8/D94 burnable fallbacks: the processor-module
  parts list names D8 as `ДГШ5.106.039`, and the `.009` FDC revision adds
  D94 as `ДГШ5.106.092`; neither scanned table represents those parts.
- The tables' `FF` idle plus one-cold `07/0B/0D/0E` shape is consistent
  with a timing/phase-select PROM family, not with the two-chip BIOS D8
  socket pager required by the traced processor module.
- Repeated physical D8 `.039` and D94 `.092` reads are preserved under
  `ref/physical-proms/validated/`; the former D8 reconstruction is
  retained only to make the 19-row mismatch auditable.
- Programming-disk copies remain valuable independent corroboration for
  D2/D6/D8/D94 and are still needed for any unidentified timing РЕ3.
