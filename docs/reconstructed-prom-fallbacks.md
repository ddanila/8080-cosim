# Reconstructed PROM fallback images

Status: **BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED**

These files are programming fallbacks, not dumped factory truth. They are
derived from the current boot-validated HDL/cosim behavior and should be
replaced or checked against Baltijets programming-disk files or physical
PROM dumps when those become available.

## Command

```sh
scripts/export_reconstructed_proms.py
sync/prom_fallback_check.sh
```

## Files

| Stem | Size | BIN SHA256 | HEX SHA256 | Role |
| --- | ---: | --- | --- | --- |
| `d6_rt4_memory_decode_reconstructed` | 256 | `b5c69c8fdc03e592d817c1c872c67e07761f218d5223f6257944248018473baf` | `e80a3f9b4b30de7dbe7a7148a73921287be07c84646c52217641d6a387504b2c` | D6 К556РТ4 memory decode; low nibble uses D0=ROM_N, D1=RAM_N, D2=REV, D3=ROE_N. |
| `d8_re3_rom_pager_reconstructed` | 32 | `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3` | `c95273ef8c46ab5db1fcbaabb6971f988e934752f6921ecb06dda6cc38b1a0bc` | D8 К155РЕ3 ROM-socket pager; byte values are active-low output rails. |

## Boundaries

- `d6_rt4_memory_decode_reconstructed.*` covers only the D6 memory decode
  fallback. Row order is `{BA15..BA11, PC2, PC3, PC4}`, preserving all
  eight traced physical inputs. Its reset-mode overlay selects ROM for
  `0x0000..0x3FFF`; current functional evidence constrains PC2, while
  PC3/PC4 are enumerated but truth-invariant until a dump proves otherwise.
  It does not claim to be the dumped factory byte table.
- `d8_re3_rom_pager_reconstructed.*` covers only the D8 ROM-socket pager
  fallback for programmed drawing family `ДГШ5.106.039`.
- No D2 image is exported. Current board metadata identifies D2 as a
  К556РТ4 bus-arbitration/wait PROM (`ДГШ5.106.037`, dump pending) with
  traced physical inputs but unknown truth. Older functional I/O-decode
  stand-ins must not be burned as a physical D2 programming image.
- No D94 image is exported. The current `re3_prom_092` HDL block is an
  electrically released stub connected to the three accepted FDC controls;
  it supplies no truth for the unknown `ДГШ5.106.092` content.
- No video/DRAM timing РЕ3 image is exported. The exact slot/state timing
  remains a dump/programming-disk dependency.
- Use these only for Tier 1/2 functional bring-up if no programming disk
  or dump is available. Tier 3 still requires real dumps.

## Non-exported PROMs

| PROM | Programmed drawing | Reason no fallback is emitted |
| --- | --- | --- |
| D2 К556РТ4 | `ДГШ5.106.037` | Physical inputs are traced, but no source constrains the output truth table. |
| D94 К155РЕ3 | `ДГШ5.106.092` | Content is unknown; HDL leaves the connected FDC-control outputs electrically released. |
| Video/DRAM timing РЕ3 | `ДГШ5.106.009` family | Timing truth is not derivable from current schematic/MAME evidence; needs dump or programming-disk table. |

## HDL Consistency Guard

`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the
current `hdl/devices.v` modules and compares every exported row against the
actual `decode_prom` and `re3_prom` logic. A passing guard means the files in
`ref/reconstructed-proms/` still match the boot-validated HDL fallback logic.

CI also reruns `scripts/export_reconstructed_proms.py` and fails if the
generated files or this report are stale.

## Diff Procedure

When a dump arrives, compare size and SHA256 first, then byte-diff against
the matching `.bin` file. A mismatch is not automatically an error: the
dump wins if its provenance and repeated reads are sound, and the HDL
model should then be updated to match the silicon.
