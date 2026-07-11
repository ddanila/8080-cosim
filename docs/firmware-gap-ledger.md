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
| D2 | К556РТ4 | `ДГШ5.106.037` | bus-arbitration/wait PROM | no | `docs/d2-reconstruction-constraints.md` | programming-disk file or repeated physical dump |
| D6 | К556РТ4 | `ДГШ5.106.038` | memory decode PROM | `ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.bin` (256 bytes, SHA256 `b5c69c8fdc03e592d817c1c872c67e07761f218d5223f6257944248018473baf`) | `docs/reconstructed-prom-fallbacks.md` | replace/check fallback against programming-disk file or dump |
| D8 | К155РЕ3 | `ДГШ5.106.039` | ROM-socket pager PROM | `ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin` (32 bytes, SHA256 `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3`) | `docs/reconstructed-prom-fallbacks.md` | replace/check fallback against programming-disk file or dump |
| D94 | К155РЕ3 | `ДГШ5.106.092` | FDC control/decode PROM | no | `docs/d94-reconstruction-constraints.md` | programming-disk file or repeated dump plus complete D94.15 and D93.2/.4 strobe-branch continuity |

## Evidence Checks

| Check | Result |
| --- | --- |
| D6 fallback exists and is 256 bytes | PASS |
| D8 fallback exists and is 32 bytes | PASS |
| D2 no-burn boundary is constrained | PASS |
| D94 no-burn boundary is constrained | PASS |
| .113/.117 RE3 scans are guarded as not D8/D94 | PASS |
| Fallback report excludes D2 and D94 exports | PASS |
| Repeated RT4 dump validation procedure is available | PASS |

## Practical Burn Rule

- For functional bring-up without factory truth, only the D6 and D8
  reconstructed images are currently burnable from the repo.
- Do not burn any older D2-as-I/O-decode behavioral table as physical
  D2; D9 is the current chip-select decoder and D2 remains a separate
  `.037` bus/wait PROM with fully traced inputs but unknown contents.
- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`
  or D94 `.092`; they are lineage evidence, not matching processor
  module programming tables.
- D94 is not reconstructable from current automatic evidence: the
  board identity and address inputs are known, but enable, outputs,
  and contents remain absent.

## Required External Closure

- Locate the Baltijets programming-disk files referenced by doc 007.
- Or repeatedly dump the socketed D2/D6 RT4 and D8/D94 RE3 parts from
  hardware, then compare D6/D8 against `ref/reconstructed-proms/` and
  replace the HDL/fallbacks only if the dump provenance is stronger.
- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;
  preserve raw pin-level and active-low asserted tables separately.
