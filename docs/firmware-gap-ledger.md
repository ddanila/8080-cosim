# Firmware gap ledger

Status: **ADOPTED FIRMWARE SET VERIFIED**

This generated ledger is the single-page burnability view for the
small PROMs that still matter to replica and Tier-3 preservation work.
It records adopted physical small-PROM tables with per-device capture provenance and
the independent archival D15/D16 pair. Each of these six devices has an
exact-hash-guarded burnable repository image accepted as content truth.
Later programming files or socket reads are preservation evidence and must
be retained as variants if they differ; they do not keep this set open.

## Command

Run from the repository root with Python 3 (standard library only).
The writer replaces this report, including when checks fail (exit code 1).

```sh
python3 scripts/report_firmware_gap_ledger.py
```

The generator verifies image sizes/hashes, BIOS split concatenation, and
the reconstructed BASIC page bytes. Behavior, provenance, and acquisition
rows check source/report text markers and tool presence; they do not run
simulations, repeat physical reads, or verify a programmed chip. Use the
owning reports and commands for those checks.

## PROM Matrix

| Ref | Part | Programmed drawing | Role | Burnable repository image | Guard | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| D2 | К556РТ4 | `ДГШ5.106.037` | READY/bus-control PROM | `ref/physical-proms/validated/d2_037.raw.bin` (256 bytes, SHA256 `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`) | `docs/d2-reconstruction-constraints.md`; `docs/d2-physical-dump-and-continuity.md` | adopted from two boards; future programming-disk comparison is optional provenance |
| D6 | К556РТ4 | `ДГШ5.106.038` | memory decode PROM | `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes, SHA256 `c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489`) | `ref/physical-proms/README.md` | adopted cross-machine table; future programming-disk comparison is optional provenance |
| D8 | К155РЕ3 | `ДГШ5.106.039` | ROM-socket pager PROM | `ref/physical-proms/validated/d8_039.raw.bin` (32 bytes, SHA256 `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`) | `ref/physical-proms/README.md` | adopted from three independent read events under six alias names; further independent provenance is optional |
| D94 | К155РЕ3 | `ДГШ5.106.092` | FDC control/decode PROM | `ref/physical-proms/validated/d94_092.raw.bin` (32 bytes, SHA256 `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`) | `docs/d94-reconstruction-constraints.md` | content adopted from three independent read events under six alias names; exact .009 CS7 closes shared enable, while D0 hidden-branch continuity remains open |
| D15 | M2764/2764 | repository EktaSoft BIOS split | BIOS low 8 KiB | `ref/eprom-images/d15_ekta37_low.bin` (8192 bytes, SHA256 `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`) | `docs/eprom-programming-images.md` | third-source archival pair adopted; future socket read is optional variant preservation |
| D16 | M2764/2764 | repository EktaSoft BIOS split | BIOS high 8 KiB | `ref/eprom-images/d16_ekta37_high.bin` (8192 bytes, SHA256 `35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817`) | `docs/eprom-programming-images.md` | third-source archival pair adopted; future socket read is optional variant preservation |

## Evidence Checks

| Check | Result |
| --- | --- |
| D2 validated physical raw image has exact size and SHA256 | PASS |
| D6 validated physical raw image has exact size and SHA256 | PASS |
| D8 validated physical raw image has exact size and SHA256 | PASS |
| D8 source/test markers cover open-collector socket selects | PASS |
| D8 report records exhaustive minimized socket-select equations | PASS |
| D94 validated physical raw image has exact size and SHA256 | PASS |
| D15 functional image has exact size and SHA256 | PASS |
| D16 functional image has exact size and SHA256 | PASS |
| D15+D16 round-trip exactly to roms/ekta37.bin | PASS |
| D15/D16 split and adopted archival provenance are documented | PASS |
| Third-source archival D15/D16 pair is adopted as content truth | PASS |
| Factory .106.106 BASIC bytes match reconstruction; report records photo adjudication | PASS |
| D2 physical table and continuity are guarded | PASS |
| D2 report records READY polarity guard markers | PASS |
| D6 source markers connect the physical table to runnable selection | PASS |
| D6 source/test markers cover open-collector release | PASS |
| D94 physical table is adopted while continuity stays guarded | PASS |
| D94 source markers connect physical-table FDC read/write strobes | PASS |
| Runnable source instantiates all four physical small-PROM tables without a functional PROM stand-in | PASS |
| .113/.117 RE3 scans are guarded as not D8/D94 | PASS |
| Historical fallback report adopts all physical PROM tables | PASS |
| Repeated RT4 dump validation procedure is available | PASS |
| Repeated RE3 dump validation procedure is available | PASS |

## Practical Burn Rule

- D2, D6, D8, and D94 have validated physical raw tables; D8/D94 board-name aliases do not prove cross-board reads;
  D15/D16 use the independently preserved archival `ekta37` pair.
- D15/D16 are the adopted third-source archival contents, not direct
  reads of the photographed sockets. Program them as low/high 8 KiB
  respectively and retain programmer verification records.
- The printed `.106.106` 2 KiB BASIC table is reconstructed separately;
  its sole BAS0/JBASIC disagreement at `021A` is photo-adjudicated as `21`,
  yielding an exact match to the first page of `roms/jbasic11.bin`.
- Never substitute the older D2-as-I/O-decode behavioral table; D9 is
  the chip-select decoder and D2 is the separate `.037` READY/wait PROM.
- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`
  or D94 `.092`; they are lineage evidence, not matching processor
  module programming tables.
- D94 firmware content does not release the FDC hardware. See
  [D94 constraints](d94-reconstruction-constraints.md) for the input/enable
  mapping, runnable-model limits, and unresolved D0 load continuity.

## Optional Preservation Follow-up

- Preserve the Baltijets programming-disk files referenced by doc 007 if found.
- Compare the validated D2/D6 tables against Baltijets programming files
  if recovered; use it as independent corroboration of D8/D94 as well.
- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;
  preserve raw pin-level and active-low asserted tables separately.
- Preserve future D2/D6 corroboration with the reader-3 metadata and
  independent enable-release checks documented in `docs/rt4-dump-acquisition.md`.
- Preserve future D8/D94 serial captures with `scripts/validate_re3_dump.py`;
  the adopted D94 table has exact .009 CS7 enable closure; D0-load continuity remains open.
- If accessible, repeatedly read physical D15/D16 and compare their concatenation
  with `roms/ekta37.bin`; preserve any stable mismatch as a variant.
