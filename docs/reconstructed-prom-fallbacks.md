# Reconstructed PROM fallback images

Status: **D8 FUNCTIONAL FALLBACK EXPORTED / PHYSICAL RT4 TABLES ADOPTED**

The D8 file is a programming fallback, not dumped factory truth. D2 and D6
now use validated owner captures under `ref/physical-proms/`; they are no
longer emitted here as reconstructions. The D8 fallback should be
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
| `d8_re3_rom_pager_reconstructed` | 32 | `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3` | `c95273ef8c46ab5db1fcbaabb6971f988e934752f6921ecb06dda6cc38b1a0bc` | D8 К155РЕ3 ROM-socket pager; byte values are active-low output rails. |

## Boundaries

- D2 `.037` has three validated captures including a separate power cycle;
  authoritative raw SHA256 is
  `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`.
- D6 `.038` has three validated captures including a separate power cycle;
  authoritative raw SHA256 is
  `05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`.
  This physical table supersedes the old reconstructed D6 image.
- `d8_re3_rom_pager_reconstructed.*` covers only the D8 ROM-socket pager
  fallback for programmed drawing family `ДГШ5.106.039`.
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
| D94 К155РЕ3 | `ДГШ5.106.092` | Content is unknown; HDL leaves the connected FDC-control outputs electrically released. |
| Video/DRAM timing РЕ3 | `ДГШ5.106.009` family | Timing truth is not derivable from current schematic/MAME evidence; needs dump or programming-disk table. |

## HDL Consistency Guard

`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the
current `hdl/devices.v` modules and compares every exported row against the
actual physical-table-backed `wait_prom_037`/`decode_prom` and reconstructed
`re3_prom` logic. A passing guard means the selected physical/reconstructed
files still match HDL.

CI also reruns `scripts/export_reconstructed_proms.py` and fails if the
generated files or this report are stale.

## Diff Procedure

When a dump arrives, compare size and SHA256 first, then byte-diff against
the matching `.bin` file. A mismatch is not automatically an error: the
dump wins if its provenance and repeated reads are sound, and the HDL
model should then be updated to match the silicon.
