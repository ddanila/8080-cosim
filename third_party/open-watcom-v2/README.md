# Vendored Open Watcom V2 toolchain

This directory vendors the official Open Watcom V2 `Current-build` C/C++
distribution published on 2026-08-20. It is the single compiler lineage for
the 16-bit DOS/Pocket8086 and 32-bit Win32/Windows 95 hosts.

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

## Bootstrap

Run from the repository root on Linux x86-64 with Bash, `unzip`, `sha256sum`
and GNU `stat`:

```sh
tools/bootstrap-open-watcom.sh
```

The script rejects an unmaterialized LFS pointer and verifies the archive's
size and SHA-256 on every run. It never downloads a moving nightly. Extraction
targets the ignored `.tools/open-watcom-v2-20260820/` directory, but is skipped
when `binl64/wcl` there is already executable. The subsequent check matches
the `wcl` product and build-date banner; it does not hash the extracted tools,
headers or libraries. Move an existing extraction aside before bootstrapping
when a fresh toolchain is required.

`tools/open-watcom-env.sh` selects this directory through `WATCOM`, `INCLUDE`
and PATH; sourcing it alone performs no verification. The DOS and Win32 build
scripts run the bootstrap before sourcing that environment.

Upstream release:
<https://github.com/open-watcom/open-watcom-v2/releases/tag/Current-build>
