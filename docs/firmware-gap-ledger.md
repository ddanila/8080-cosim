# Firmware gap ledger

Status: **BURNABLE SET VERIFIED / TIER-3 CORROBORATION PENDING**

This generated ledger is the single-page burnability view for the
small PROMs that still matter to replica and Tier-3 preservation work.
It separates boot-validated functional EPROM images from dumped factory
PROM truth. Every populated device has an exact-hash-guarded burnable
repository image for Tier 1/2. Programming-disk files, independent PROM
reads, and original D15/D16 reads remain Tier-3 corroboration and win
if a stable difference appears.

## Command

```sh
python3 scripts/report_firmware_gap_ledger.py
```

## PROM Matrix

| Ref | Part | Programmed drawing | Role | Burnable repository image | Guard | Next truth source |
| --- | --- | --- | --- | --- | --- | --- |
| D2 | К556РТ4 | `ДГШ5.106.037` | READY/bus-control PROM | `ref/physical-proms/validated/d2_037.raw.bin` (256 bytes, SHA256 `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`) | `docs/d2-reconstruction-constraints.md`; `docs/d2-physical-dump-and-continuity.md` | programming-disk comparison or independent future read |
| D6 | К556РТ4 | `ДГШ5.106.038` | memory decode PROM | `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes, SHA256 `c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489`) | `ref/physical-proms/README.md` | revision-3 reader capture is adopted; programming-disk comparison or independent read is Tier-3 corroboration |
| D8 | К155РЕ3 | `ДГШ5.106.039` | ROM-socket pager PROM | `ref/physical-proms/validated/d8_039.raw.bin` (32 bytes, SHA256 `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`) | `ref/physical-proms/README.md` | programming-disk comparison or independent future read |
| D94 | К155РЕ3 | `ДГШ5.106.092` | FDC control/decode PROM | `ref/physical-proms/validated/d94_092.raw.bin` (32 bytes, SHA256 `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`) | `docs/d94-reconstruction-constraints.md` | programming-disk comparison plus the equation-targeted D0 hidden-branch probe, D5-D7 destinations (D4 is photo-closed to D93.1), D104.10 receiver-output continuity, pull-up resistor identities, and the guarded D29.4/IORD recheck |
| D15 | M2764/2764 | repository EktaSoft BIOS split | BIOS low 8 KiB | `ref/eprom-images/d15_ekta37_low.bin` (8192 bytes, SHA256 `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`) | `docs/eprom-programming-images.md` | repeat physical D15 dump for Tier-3 truth |
| D16 | M2764/2764 | repository EktaSoft BIOS split | BIOS high 8 KiB | `ref/eprom-images/d16_ekta37_high.bin` (8192 bytes, SHA256 `35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817`) | `docs/eprom-programming-images.md` | repeat physical D16 dump for Tier-3 truth |

## Evidence Checks

| Check | Result |
| --- | --- |
| D2 validated physical raw image has exact size and SHA256 | PASS |
| D6 validated physical raw image has exact size and SHA256 | PASS |
| D8 validated physical raw image has exact size and SHA256 | PASS |
| D8 physical table executes as open-collector socket selects | PASS |
| D8 physical table has exhaustive minimized socket-select equations | PASS |
| D94 validated physical raw image has exact size and SHA256 | PASS |
| D15 functional image has exact size and SHA256 | PASS |
| D16 functional image has exact size and SHA256 | PASS |
| D15+D16 round-trip exactly to roms/ekta37.bin | PASS |
| D15/D16 split and non-dump provenance are documented | PASS |
| Factory .106.106 BASIC page is reconstructed and photo-adjudicated | PASS |
| D2 physical table and continuity are guarded | PASS |
| D2 open-collector raw polarity executes through the D30 READY latch | PASS |
| D6 corrected physical table drives runnable selection directly | PASS |
| D6 physical table preserves open-collector release | PASS |
| D94 physical table is adopted while continuity stays guarded | PASS |
| D94 physical table drives runnable FDC read/write strobes under guarded upstream fits | PASS |
| .113/.117 RE3 scans are guarded as not D8/D94 | PASS |
| Historical fallback report adopts all physical PROM tables | PASS |
| Repeated RT4 dump validation procedure is available | PASS |
| Repeated RE3 dump validation procedure is available | PASS |

## Practical Burn Rule

- D2, D6, D8, and D94 have validated physical raw tables; D15/D16
  still use the deterministic `ekta37` EPROM split.
- Reader-3 reproduced D2 byte-for-byte across three captures including a
  power cycle. Three equally stable D6 reads then proved the old artifact
  had all four output channels reversed; socket continuity and the full
  boot guard adopt the corrected direct table.
- D15/D16 are deterministic Tier-1/2 functional images, not physical
  device dumps. Program them as low/high 8 KiB respectively and
  retain programmer verification records.
- The printed `.106.106` 2 KiB BASIC table is reconstructed separately;
  its sole BAS0/JBASIC disagreement at `021A` is photo-adjudicated as `21`,
  yielding an exact match to the first page of `roms/jbasic11.bin`.
- Never substitute the older D2-as-I/O-decode behavioral table; D9 is
  the chip-select decoder and D2 is the separate `.037` READY/wait PROM.
- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`
  or D94 `.092`; they are lineage evidence, not matching processor
  module programming tables.
- D94 content and all A0-A4 input destinations are owner-closed. Its
  physical table now drives the runnable FDC `/RE` and `/WE` inputs;
  decoded enable, A3=`IOWR`, and pulled-high A4 remain explicit sim-only
  upstream fits rather than claimed copper closure. The enable source,
  D5-D7 far destinations, D104.10, pull-up identities, guarded
  D29.4/IORD recheck, and apparently pull-up-only D0 resistor identity
  remain unresolved
  connectivity boundaries and still block an FDC hardware release.

## Required External Closure

- Locate the Baltijets programming-disk files referenced by doc 007.
- Compare the validated D2/D6 tables against Baltijets programming files
  if recovered; use it as independent corroboration of D8/D94 as well.
- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;
  preserve raw pin-level and active-low asserted tables separately.
- Preserve future D2/D6 corroboration with the reader-3 metadata and
  independent enable-release checks documented in `docs/rt4-dump-acquisition.md`.
- Preserve future D8/D94 serial captures with `scripts/validate_re3_dump.py`;
  the adopted D94 table still requires complete input/enable/output continuity.
- Repeatedly read physical D15/D16 and compare their concatenation
  with `roms/ekta37.bin`; preserve any stable mismatch as a variant.
