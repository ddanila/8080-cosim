# Vendored Open Watcom V2 toolchain

This directory vendors the official Open Watcom V2 `Current-build` C/C++
distribution published on 2026-08-20. It is the single compiler lineage for
the 16-bit DOS/Pocket8086 host and the later 32-bit Win32/Windows 95 host.

| field | pinned value |
| --- | --- |
| upstream | `open-watcom/open-watcom-v2` |
| upstream tag | `Current-build` |
| annotated tag object | `25be8e688cf166842347399195353f14d2615e5e` |
| source commit | `cf43271464fdd57065d3d72de8ca917c55c6a887` |
| release timestamp | `2026-08-20T03:29:55Z` |
| asset | `open-watcom-2_0-c-linux-x64` |
| vendored filename | `open-watcom-v2-c-linux-x64-20260820` |
| bytes | `129055748` |
| SHA-256 | `f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85` |

The unmodified upstream distribution is stored through Git LFS. It contains
the Linux-x64 compiler host plus DOS and Win32 target headers/libraries. Its
`license.txt` and `readme.txt` remain inside the original archive.

Run `tools/bootstrap-open-watcom.sh` to verify and unpack it into the ignored
`.tools/` directory. The bootstrap never downloads a moving nightly; a clone
must materialize this exact LFS object.

Upstream release:
<https://github.com/open-watcom/open-watcom-v2/releases/tag/Current-build>
