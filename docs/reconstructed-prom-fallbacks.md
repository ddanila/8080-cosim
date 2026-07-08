# Reconstructed PROM fallback images

Status: **BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED**

These files are programming fallbacks, not dumped factory truth. They are
derived from the current boot-validated HDL/cosim behavior and should be
replaced or checked against Baltijets programming-disk files or physical
PROM dumps when those become available.

## Command

```sh
scripts/export_reconstructed_proms.py
```

## Files

| Stem | Size | BIN SHA256 | HEX SHA256 | Role |
| --- | ---: | --- | --- | --- |
| `d6_rt4_memory_decode_reconstructed` | 256 | `10063c67c86b4c5f82dfcc63f692e38fa4a567d34d7226e29ca7198255fb96f0` | `f89f8aa348e1c2c4e94ee59c2e80ab23ebf16d488b3a10b8232b21f581a32d96` | D6 К556РТ4 memory decode; low nibble uses D0=ROM_N, D1=RAM_N, D2=REV, D3=ROE_N. |
| `d8_re3_rom_pager_reconstructed` | 32 | `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3` | `c95273ef8c46ab5db1fcbaabb6971f988e934752f6921ecb06dda6cc38b1a0bc` | D8 К155РЕ3 ROM-socket pager; byte values are active-low output rails. |

## Boundaries

- `d6_rt4_memory_decode_reconstructed.*` covers only the D6 memory decode
  fallback. It does not claim to be the dumped `ДГШ5.106.037/.038` byte
  table and does not cover D2 I/O decode.
- `d8_re3_rom_pager_reconstructed.*` covers only the D8 ROM-socket pager
  fallback for programmed drawing family `ДГШ5.106.039`.
- D94 (`ДГШ5.106.092`) and the РЕ3/АГ3 video timing PROM truth remain
  undumped and are not exported here.
- Use these only for Tier 1/2 functional bring-up if no programming disk
  or dump is available. Tier 3 still requires real dumps.

## Diff Procedure

When a dump arrives, compare size and SHA256 first, then byte-diff against
the matching `.bin` file. A mismatch is not automatically an error: the
dump wins if its provenance and repeated reads are sound, and the HDL
model should then be updated to match the silicon.
