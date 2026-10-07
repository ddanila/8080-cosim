# Portable C host M2 acceptance

Status: **ACCEPTED ON NATIVE LINUX AND PHYSICAL CS00015**

This report closes the native-Linux parity and Python-host-retirement gate in
the [portable C host plan](portable-c-host-plan.md). Its exact Linux build has
since passed physical M2.1 on CS00015; that evidence is retained in
[portable-c-host-m2.1-physical-acceptance.md](portable-c-host-m2.1-physical-acceptance.md).
This is a revision-qualified M2 record. DOS, macOS, Wine and Windows evidence
belongs to their separate acceptance records, indexed by
[the current host contract](portable-c-host-plan.md).

## Accepted identities

- C host source and retirement checkpoint: `8080-cosim` commit `6724d33b`.
- Native command: `build/jukuhost`, reporting `jukuhost 0.1.0-m2`.
- Frozen Python-era baseline: commit `81f64f76` and
  `tests/fixtures/jukuhost/python-era-v1.txt`.
- Linux smoke kit v2: commit `6724d33b`, OCI digest
  `sha256:579e79e9fc801266f439e5a62ec2579e474ba64642cfe6da72390826a06f64c8`.
- CP/M Plus CI image built from that kit: digest
  `sha256:245934e74520c45bb5702fa3948b4da165c80e4c1b6957fd266ed09c1916941f`.

## Accepted scope

The recorded gate compared the frozen Python-era oracle with the native C
host for stock Janet, C8/V16 boot, N3/N4, media and journal safety, host
replacement, target reset, and required log/capture behavior. Operational
launchers used the C executable. The current implementation and verification
entry points are maintained in
[portable-c-host-implementation.md](portable-c-host-implementation.md).

## Reproducible gate

Run from the repository root on Linux with Bash, Python 3/Unix PTY support,
a C compiler (`CC`, default `cc`), and materialized fixture assets. The C8
session test requires prebuilt system, V16 stage, full A: image and native B:
media in the adjacent `cpm-plus-juku/out/`. The stock-reset test also requires
`cpm-plus-juku-stock-recovery-system.bin`,
`cpm-plus-juku-stock-recovery-fastboot-v17.bin`, and `cpm-plus-juku.img` there.
`CPM_PLUS_JUKU_ROOT` selects another checkout. These tests do not build the
sibling payloads. The network-ROM builder uses the pinned zmac source and needs `make`,
`bison` and a compiler if its executable is absent. Initialize submodules first.

Run the complete local gate with:

```sh
sync/jukuhost_m2_check.sh
```

Through `sync/janet_netboot_check.sh`, the M2 gate runs the core portability
checks (signed/unsigned `char`, available Clang and sanitizers), frozen
Python-era oracle and five-system suite. It also runs the native build and
PTY media/evidence/reconnect tests, stock and C8 end-to-end simulator
workloads, operational-wrapper checks, and the current network-ROM ABI/fault
matrix. The recorded 2026-08-20 run passed; this historical result does not
establish a pass for a later source tree or changed sibling artifacts.

The structural UART/ROM checks also passed separately:

```sh
sync/network_first_rom_hdl_check.sh
sync/serial_check.sh
```

## Qualification boundary

M2 closes the Linux production-host parity and Python-host-retirement gate
for the identities above. M2.1 separately qualifies the named executable on
CS00015. DOS desk/emulator qualification is recorded in
[the M2.2 report](portable-c-host-m2.2-dos-acceptance.md); physical DOS
qualification remains open independently of Windows development. Windows
build, Wine and Windows 95 guest results are already implemented and recorded
in their platform guides, with physical serial qualification still separate.
These later results do not retroactively widen the exact M2 hardware claim.
