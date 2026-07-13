# Firmware gap ledger

Status: **PROM GAP LEDGER READY / DUMP TRUTH PENDING**

This generated ledger is the single-page burnability view for the
small PROMs that still matter to replica and Tier-3 preservation work.
It separates boot-validated functional fallbacks from dumped factory
truth. A reconstructed fallback may be useful for Tier 1/2 bring-up,
but a programming-disk file or repeated physical dump wins when it
arrives.

## Command

```sh
python3 scripts/report_firmware_gap_ledger.py
```

## PROM Matrix

| Ref | Part | Programmed drawing | Role | Burnable repo fallback | Guard | Next truth source |
| --- | --- | --- | --- | --- | --- | --- |
| D2 | К556РТ4 | `ДГШ5.106.037` | READY/bus-control PROM | `ref/physical-proms/validated/d2_037.raw.bin` (256 bytes, SHA256 `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`) | `docs/d2-reconstruction-constraints.md`; `docs/d2-physical-dump-and-continuity.md` | programming-disk comparison or independent future read |
| D6 | К556РТ4 | `ДГШ5.106.038` | memory decode PROM | `ref/physical-proms/validated/d6_038.raw.bin` (256 bytes, SHA256 `05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`) | `ref/physical-proms/README.md` | independent-reader or programming-disk comparison |
| D8 | К155РЕ3 | `ДГШ5.106.039` | ROM-socket pager PROM | `ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin` (32 bytes, SHA256 `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3`) | `docs/reconstructed-prom-fallbacks.md` | replace/check fallback against programming-disk file or dump |
| D94 | К155РЕ3 | `ДГШ5.106.092` | FDC control/decode PROM | no | `docs/d94-reconstruction-constraints.md` | programming-disk file or repeated dump plus complete D94.15 and D93.2/.4 strobe-branch continuity |
| D15 | M2764/2764 | repository EktaSoft BIOS split | BIOS low 8 KiB | `ref/eprom-images/d15_ekta37_low.bin` (8192 bytes, SHA256 `d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`) | `docs/eprom-programming-images.md` | repeat physical D15 dump for Tier-3 truth |
| D16 | M2764/2764 | repository EktaSoft BIOS split | BIOS high 8 KiB | `ref/eprom-images/d16_ekta37_high.bin` (8192 bytes, SHA256 `35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817`) | `docs/eprom-programming-images.md` | repeat physical D16 dump for Tier-3 truth |

## Evidence Checks

| Check | Result |
| --- | --- |
| D2 validated physical raw image exists and is 256 bytes | PASS |
| D6 validated physical raw image exists and is 256 bytes | PASS |
| D8 fallback exists and is 32 bytes | PASS |
| D15 functional image exists and is 8192 bytes | PASS |
| D16 functional image exists and is 8192 bytes | PASS |
| D15+D16 round-trip exactly to roms/ekta37.bin | PASS |
| D15/D16 split and non-dump provenance are documented | PASS |
| D2 physical table and continuity are guarded | PASS |
| D94 no-burn boundary is constrained | PASS |
| .113/.117 RE3 scans are guarded as not D8/D94 | PASS |
| Fallback report adopts physical RT4 tables but excludes D94 | PASS |
| Repeated RT4 dump validation procedure is available | PASS |
| Repeated RE3 dump validation procedure is available | PASS |

## Practical Burn Rule

- D2 and D6 now have validated physical raw tables. D8 remains a
  reconstructed functional image; D15/D16 use the `ekta37` EPROM split.
- D2 is preservation-strength within current evidence: three captures
  validate identically and include a separate power cycle. D6 also has three
  matching preserved captures including a separate power cycle.
- D15/D16 are deterministic Tier-1/2 functional images, not physical
  device dumps. Program them as low/high 8 KiB respectively and
  retain programmer verification records.
- Never substitute the older D2-as-I/O-decode behavioral table; D9 is
  the chip-select decoder and D2 is the separate `.037` READY/wait PROM.
- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`
  or D94 `.092`; they are lineage evidence, not matching processor
  module programming tables.
- D94 is not reconstructable from current automatic evidence: the
  board identity and address inputs are known, but enable, outputs,
  and contents remain absent.

## Required External Closure

- Locate the Baltijets programming-disk files referenced by doc 007.
- Compare the validated D2/D6 tables against Baltijets programming files
  if recovered; obtain D8/D94 RE3 physical truth separately.
- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;
  preserve raw pin-level and active-low asserted tables separately.
- Validate D8/D94 serial captures with `scripts/validate_re3_dump.py`;
  a sound D94 dump still requires complete enable/output continuity.
- Repeatedly read physical D15/D16 and compare their concatenation
  with `roms/ekta37.bin`; preserve any stable mismatch as a variant.
