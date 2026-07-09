# BASIC cartridge length audit

Status: **CARTRIDGE BASIC TAIL PAGE MISSING**

This generated report sharpens the Monitor 3.3 cartridge BASIC boundary
from `docs/basic-low-stub-inspection.md`. The launch path itself is
intentional; the remaining failure is that the public 8 KiB cartridge
shape does not cover the runtime source range used by its own relocation
bootstrap.

## Inputs

| Item | Value |
| --- | --- |
| Cartridge | `roms/jbasic11.bin` |
| Cartridge bytes | `8192` |
| Cartridge SHA256 | `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60` |
| Legacy BAS0-3 bytes | `8192` |
| Legacy BAS0-3 SHA256 | `9fc9f2216f6a95c92bdac14991145b960b41c8318d086b1d80fdf470a806c9b4` |
| First `0x0200` bytes identical | `YES` |
| Full images identical | `NO` |

## Relocation Coverage

| Field | Value |
| --- | --- |
| Monitor-loaded runtime span | `0x0100..0x20FF` |
| Bootstrap source span | `0x0200..0x21FF` |
| Bootstrap destination span | `0x0100..0x20FF` |
| Missing source span | `0x2100..0x21FF` |
| Missing source bytes | `256` |
| First destination byte sourced from missing span | `0x2000` |
| Loop target overwrite source | `0x2109` -> runtime `0x2009` |
| Loop return overwrite source | `0x2113` -> runtime `0x2013` |

The public payload loaded at `0x0100` ends at `0x20FF`, but the
bootstrap copies `0x0200..0x21FF` down to `0x0100..0x20FF`. Therefore
the last `0x100` source bytes are not supplied by the 8 KiB cartridge
image. The first missing-source write lands at runtime `0x2000`; by
the time execution reaches the loop tail, the live `MOV A,M` at
`0x2009` and the nominal `JMP 0x0100` at `0x2013` are overwritten
from zero-filled `0x2109` and `0x2113` respectively.

## Disk BASIC Candidate Cross-check

The disk-side `JBASIC.COM` candidates are useful for the proven EKDOS
`READY` path, but none is a direct byte-for-byte tail donor for the
Monitor 3.3 cartridge bootstrap.

| Candidate | Bytes | SHA256 | First bytes | Best exact overlap with cartridge | Strings |
| --- | ---: | --- | --- | --- | --- |
| `ref/extracted-software/JUKPROG2_JBASIC.COM` | 8320 | `73cc53939c501c382e610e4e81dbf19cc5154d83545757b5155ccf70a2351d9c` | `c3 40 13 c3 32 11 c3 c0` | `257` bytes at cart `0x1D30` / candidate `0x025B` | BASIC -; READY -; ERROR - |
| `ref/extracted-software/JUKPROG2_JBASIC_live_candidate.COM` | 8320 | `b1ae68b464c245a888c8e6bbf07037960f5a92d4e968c956c6205a1de6cfc545` | `c3 05 01 86 1c 31 ff b3` | `253` bytes at cart `0x0540` / candidate `0x1A47` | BASIC `0x05AD`; READY `0x0576`; ERROR `0x0569`, `0x1272` |
| `ref/extracted-software/JUKU1_JBASIC_raw_candidate.COM` | 8320 | `85522b5b662b8c353c2aad8167bea0b5fc4a94ec71cc87ea91a7a2c551255c4d` | `c3 05 01 86 1c 31 ff b3` | `253` bytes at cart `0x0540` / candidate `0x0847` | BASIC `0x05AD`; READY `0x0576`; ERROR `0x0569` |

## Boundary

- The D8/D22 cartridge window and Monitor 3.3 copy path are already proven.
- The public 8 KiB cartridge media shape is too short for the runtime
  relocation loop it contains; the missing span is exactly one 256-byte
  page, `0x2100..0x21FF` in runtime address space.
- The extracted disk BASIC candidates are separate EKDOS payload shapes,
  not an automatic replacement for the missing cartridge tail page.
- The next automatic cartridge step would require another public artifact
  or a derivable tail-page source. Otherwise this remains a media/monitor
  compatibility boundary, while disk-side `JBASIC.COM` remains the guarded
  functional BASIC path.
