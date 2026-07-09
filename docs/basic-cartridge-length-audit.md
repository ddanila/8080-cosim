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

## Vendored Raw Disk Sweep

This bytewise sweep covers every vendored `*.CPM` and `*.JUK` image
under `media/disks/`, including the public `J3KUTIL4.JUK` utility
image. It looks for the known cartridge stream, the known final
cartridge page, and the first relocated body page inside raw disk
bytes. A hit in the first two categories with another `0x100` bytes
available would be a concrete tail-page donor lead.

| Probe | Hits |
| --- | ---: |
| Known 8 KiB cartridge image followed by an extra page | 0 |
| Known final cartridge page followed by an extra page | 0 |
| First relocated body page occurrences | 0 |

| Disk | Bytes | SHA256 | Best exact overlap with cartridge | Full image + tail offsets | Final page + tail offsets | Body-page offsets | Strings |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `media/disks/J3KUTIL4.JUK` | 819200 | `d7a0b766a00c80ac487e24f48499386249534418ccb42739bae83a9e5a075de3` | `464` bytes at cart `0x1D30` / disk `0x01400` | `0` | `0` | `0` | BASIC -; READY `0x1F45D`, `0x4D9F3`, `0x4DC51`, `0x52E21`, `0x560C0`; ERROR `0x05E4`, `0x4B1A`, `0x111D6`, `0x4852E`, `0x4B3F4` (+18) |
| `media/disks/JUKGAME1.CPM` | 819200 | `659ac330083f20ef41495f54240c528342ba3d431c657f0686a265383e88095d` | `150` bytes at cart `0x1D30` / disk `0x07F6A` | `0` | `0` | `0` | BASIC -; READY -; ERROR `0x05E4`, `0x37F2E` |
| `media/disks/JUKPROG1.CPM` | 819200 | `94670f3333b29e205c1586a0f52882aaa0f8cff2d45c3493676ce3ab263ae269` | `464` bytes at cart `0x1D30` / disk `0x01400` | `0` | `0` | `0` | BASIC -; READY `0x17195`, `0x17486`, `0x6205D`, `0xC67F3`, `0xC6A51`; ERROR `0x05E4`, `0x7149`, `0xA8E1`, `0x1232D`, `0x123C7` (+21) |
| `media/disks/JUKPROG2.CPM` | 819200 | `7e41d32f64a37ea2312ae81e73a6043888b97eb78d04ebacc53be2e4690a1520` | `253` bytes at cart `0x0540` / disk `0x2F847` | `0` | `0` | `0` | BASIC `0x5162`, `0x7F02`, `0x2DA9A`, `0x2E3AD`; READY `0x11F95`, `0x12286`, `0x2E376`, `0x7C639`, `0x7F3DA` (+3); ERROR `0x05E4`, `0x4CC1`, `0xCE60`, `0xD232`, `0xD2C3` (+54) |
| `media/disks/JUKPROGX.CPM` | 819200 | `3ce19c094ee2801583c277fa6012d6aae983a696c9932d39f927fa3156b78e58` | `148` bytes at cart `0x1D30` / disk `0x1C66C` | `0` | `0` | `0` | BASIC -; READY `0x1E286`, `0x1F195`; ERROR `0x05E4`, `0x1972A`, `0x1C32D`, `0x1C3DF`, `0x1E25E` (+3) |
| `media/disks/JUKU1.CPM` | 819200 | `859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27` | `253` bytes at cart `0x0540` / disk `0x67847` | `0` | `0` | `0` | BASIC `0x5102`, `0x66C9A`, `0x675AD`; READY `0x19FDA`, `0x1B809`, `0x46439`, `0x67576`, `0x9605D` (+1); ERROR `0x05E4`, `0x492D`, `0x49C7`, `0x1719E`, `0x171AF` (+27) |

## Boundary

- The D8/D22 cartridge window and Monitor 3.3 copy path are already proven.
- The public 8 KiB cartridge media shape is too short for the runtime
  relocation loop it contains; the missing span is exactly one 256-byte
  page, `0x2100..0x21FF` in runtime address space.
- The extracted disk BASIC candidates are separate EKDOS payload shapes,
  not an automatic replacement for the missing cartridge tail page.
- The vendored raw disk sweep finds no known 8 KiB cartridge image, and
  no known final cartridge page, followed by an extra `0x100` bytes.
  That rules out a direct raw-disk tail donor among the current
  vendored public media without claiming the unknown page contents.
- The next automatic cartridge step would require another public artifact
  or a derivable tail-page source. Otherwise this remains a media/monitor
  compatibility boundary, while disk-side `JBASIC.COM` remains the guarded
  functional BASIC path.
