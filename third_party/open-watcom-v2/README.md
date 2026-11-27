# Open Watcom V2 for DOS and Windows

The Linux x86-64 build host uses the official
[2026-08-01-Build release](https://github.com/open-watcom/open-watcom-v2/releases/tag/2026-08-01-Build)
for the Pocket8086 DOS and Windows 95 executables.

| Archive field | Pinned value |
| --- | --- |
| Asset | `open-watcom-2_0-c-linux-x64` |
| Bytes | 128821776 |
| SHA-256 | `e1bc4e88fa47191118f29e53731e7f4542803c7f4c503e15d72f1f571ac0832f` |

The DOS and Windows build scripts invoke `tools/bootstrap-open-watcom.sh`.
On first use the bootstrap downloads the dated asset with curl, checks its
SHA-256, and extracts it under `.tools/open-watcom-v2-20260801/`. Later
builds verify the archive in `.tools/downloads/open-watcom-20260801` and
reuse the extraction offline. An offline builder can prepopulate that archive.
An invalid cached archive stops the build. Move it aside to fetch a fresh
copy. To refresh an extraction, move its directory aside and rerun the build.
Bootstrap checks the compiler banner on reuse.

For the transition from the August 20 nightly, both compilers built identical
executables from the same host sources and checked-in Windows payload catalog.

| Executable | SHA-256 |
| --- | --- |
| JUKUHOST.EXE | `d5005c5959efc8bcf9cfb1d756fee898886c184f97dfa2908e6b08253193cc28` |
| JUKUWIN.EXE | `016a8f74a58d6d0358851366b4ad34b9b6e371532c4ab9b2ca586942f8ad6da1` |

The Win32 executable passed the Windows 95 import audit, the threaded
self-test in an original Windows 95 VM, and stock/C11/C12 serial simulations
under Wine using the embedded payload identities. The DOS executable uses a 32 KiB stack for
the current serial and NetDisk paths. With a 24 KiB stack the C8 run failed
during journal recovery. Relinking the same objects with a 32 KiB stack
passed the 19,200-baud C8 serial workload in DOSBox-X. Physical serial
hardware was outside this toolchain comparison.
