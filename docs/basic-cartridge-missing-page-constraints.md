# BASIC cartridge missing-page constraints

Status: **MISSING PAGE CONSTRAINED / ARTIFACT REQUIRED**

This generated report turns the Monitor 3.3 cartridge BASIC missing-page
boundary into static reconstruction constraints. It does not export a
patched cartridge image; the real page still needs a larger artifact,
programming source, or hardware-confirmed dump.

## Command

```sh
python3 scripts/report_basic_cartridge_missing_page_constraints.py
```

## Inputs

| Item | Value |
| --- | --- |
| Cartridge | `roms/jbasic11.bin` |
| Cartridge bytes | 8192 |
| Cartridge SHA256 | `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60` |
| Known relocated runtime span | `0x0100..0x1FFF` |
| Missing source span | `0x2100..0x21FF` |
| Missing runtime span | `0x2000..0x20FF` |

## Relocation Loop Survival Bytes

The relocation loop overwrites itself while running. For the loop tail to
survive until the final iteration, the missing page must reproduce these
runtime bytes at the corresponding source offsets:

| Missing source | Runtime destination | Required bytes | Meaning |
| --- | --- | --- | --- |
| `0x2109..0x2115` | `0x2009..0x2015` | `7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01` | `MOV A,M; STAX D; INX H; INX D; DCX B; MOV A,B; ORA C; JNZ 0x2009; JMP 0x0100` loop tail and exit |

## Known-Body References Into Missing Page

A linear 8080 sweep over the known relocated body (`0x0100..0x1FFF`)
finds direct 16-bit operands that point into the missing runtime page.
This is a conservative static constraint, not proof that every operand
is executed as code.

| Metric | Value |
| --- | ---: |
| Total direct references | 60 |
| Unique referenced missing-page bytes | 15 |
| Unreferenced missing-page bytes by direct operand scan | 241 |
| Referenced missing-page address span | `0x2000..0x2018` |
| Control-transfer references | 1 |

| Target | References | Kinds | Sample source PCs |
| ---: | ---: | --- | --- |
| `0x2000` | 1 | data/immediate | `0x1E06:LXI B` |
| `0x2007` | 3 | data/immediate | `0x013F:STA`, `0x0151:LDA`, `0x0164:LDA` |
| `0x2008` | 2 | data/immediate | `0x0149:STA`, `0x016D:LDA` |
| `0x2009` | 15 | control, data/immediate | `0x01F0:STA`, `0x0205:STA`, `0x021E:STA`, `0x05EF:STA`, `0x0627:LDA`, `0x07F2:LDA` (+9) |
| `0x200A` | 4 | data/immediate | `0x0319:LHLD`, `0x0324:SHLD`, `0x0338:SHLD`, `0x0347:SHLD` |
| `0x200C` | 3 | data/immediate | `0x02EB:LHLD`, `0x02F8:SHLD`, `0x0351:SHLD` |
| `0x200E` | 2 | data/immediate | `0x0B89:LHLD`, `0x1BDA:SHLD` |
| `0x2010` | 4 | data/immediate | `0x08AD:STA`, `0x08DC:LDA`, `0x08E0:STA`, `0x08E9:LDA` |
| `0x2011` | 3 | data/immediate | `0x01F3:STA`, `0x0B96:LDA`, `0x1BCB:STA` |
| `0x2012` | 4 | data/immediate | `0x0729:STA`, `0x09FC:STA`, `0x0C95:LDA`, `0x0C9A:STA` |
| `0x2013` | 3 | data/immediate | `0x06D1:SHLD`, `0x0722:LHLD`, `0x0AC6:SHLD` |
| `0x2015` | 4 | data/immediate | `0x06D5:STA`, `0x071B:LDA`, `0x072C:STA`, `0x0AC9:STA` |
| `0x2016` | 5 | data/immediate | `0x02A8:LDA`, `0x0B8F:LDA`, `0x0CBF:LDA`, `0x1BCE:STA`, `0x1C02:STA` |
| `0x2017` | 4 | data/immediate | `0x07E4:LXI H`, `0x07EF:LXI H`, `0x0C32:LXI H`, `0x1C21:STA` |
| `0x2018` | 3 | data/immediate | `0x068A:LXI D`, `0x0747:LXI D`, `0x081E:LXI H` |

## Control References

| Source PC | Opcode | Target | Interpretation |
| ---: | --- | ---: | --- |
| `0x1E10` | `JNZ` | `0x2009` | relocation loop branch target; not an independent BASIC entry |

## Repository Donor Scan

The loop-tail byte pattern is searched at the same page offset across
`roms/`, `ref/`, and `media/`. A useful donor would be a page-shaped
hit outside the public cartridge's own final page.

| File | Page start | Pattern offset in page |
| --- | ---: | ---: |
| `roms/jbasic11.bin` | `0x1F00` | `0x0009` |

## Boundary

- The missing page maps exactly from cartridge/runtime source
  `0x2100..0x21FF`
  to runtime `0x2000..0x20FF`.
- Current direct-operand evidence concentrates all known-body references
  in `0x2000..0x2018`; the remaining
  missing-page bytes have no direct 16-bit operands from the known body.
- The only direct control transfer into the missing page is the relocation
  loop's own `JNZ 0x2009`. The other references are data/immediate operands,
  mostly to low variables/workspace in `0x2007..0x2018`.
- No current repository artifact provides a page-shaped donor beyond the
  public cartridge's own final page. A burnable cartridge fix still needs
  the real larger BASIC artifact, programming source, or a deeper manual
  reconstruction validated against the BASIC `READY` oracle.
