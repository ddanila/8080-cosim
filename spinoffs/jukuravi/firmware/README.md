# Jukuravi diagnostic firmware

This directory contains burnable diagnostic ROMs, loader-callable probes and
their build scripts. Use the [project guide](../README.md) for host and
bench setup and [Loader API v2](../LOADER-API-V2.md) for the monitor protocol.
Completed firmware experiments are available in Git; physical observations stay
in the linked qualification records.

## Current hardware boundaries

- D0/D2 diagnostic ROMs are 8,192-byte D15/2764 images mapped at
  `0000h..1FFFh`. Their ladder does not read D16; it cannot qualify that chip.
- T36 (`diag-d0-row-refresh.bin`, DOS `T36HOST.BIN`) is the physical-row refresh
  monitor. T35 (`diag-d0-refresh.bin`) is retained as a falsified negative
  control, not a substitute for T36.
- T36 retains T34's clock-safe D55 test. PIT register tests require the correct
  physical clock/gate behavior; a no-edge readback is not sufficient to diagnose
  a failed counter.
- Loader/probe execution owns the relevant RAM and peripheral state. Use the
  API's declared load ranges, preserved registers and return convention rather
  than applying an older monitor's entry point to a different image.

## T36 refresh and RAM qualification

T36 version `1E`, CRC16 `C617`, calls the public refresh entry `07A9h`.
It reads `4000h..407Fh`, covering all physical MA0..MA6 rows once, preserves
BC/DE/HL/SP, and clobbers A/flags. The routine takes 2,115 nominal T-states.
Using the conservative effective RAM throughput near 1.7 MHz, cooperative code
must begin another `CALL 07A9h` within 2 ms. Non-cooperative or crashed uploaded
code remains unsafe; the throughput figure is not a crystal measurement.

T35's high-byte increment reads `4000h,4100h,...,BF00h`, repeatedly visiting one
physical row. Its long idle reattach did not prove all-row refresh. The drawing,
MK4564 requirement, exact artifacts and T35/T36 split are pinned by
`tests/jukuravi_refresh_row_address_test.py`.

The physical CS00024 local sweep passed zero, one, checkerboard and address-XOR
patterns over the `4000h..BFFFh` union after six-second refresh-on holds. It
qualifies the RAM array under T36 refresh; it does not prove raw retention or
the normal-ROM refresh schedule. See the
[T36 diagnosis](../../../docs/cs00024-t36-diagnosis.md) for exact evidence and
remaining qualification checks.

D57 channel 2 is clocked by D55 `/VER RTR`, not the channel-0 clock. The current
`d57-raw-refresh-4000.asm` emits `D57S` v2, arms the raster and waits 64 refresh
sweeps after each channel-2 write. `batch.py --only-d57` scores only this corrected
format. Legacy `D57R` captures remain evidence but are not a channel-2 fault
discriminator; CS00024 needs the corrected rerun.

## Monitor and probe selection

| Artifact family | Purpose and boundary |
| --- | --- |
| `diag-d0-alive/cpu/usart-local/serial` | Isolated startup, CPU and serial diagnostic stages |
| `diag-d0-ram/ram-fallback` | Serial survey or serial-dead audible fixed-window tests |
| `diag-d0-romcheck/pic/ppi/pit/framebuffer/noserial/pit-debug` | Historical peripheral/ROM/display ladder and audible variants; use clock-safe successors for D55 diagnosis |
| `diag-d2-loader.bin` | Earlier CRC-framed LOAD/RUN monitor; its API differs from the current transactional monitor |
| `diag-d0-buffer-verified.bin` and successors | Verified-workspace transactional PROBE/CONFIG/LOAD/READ/CRC/RUN/RESYNC monitor; CALL/RET and execution-ID duplicate suppression |
| `diag-d0-row-refresh.bin` | T36 monitor with physical-row refresh and fail-safe controls |
| `*-4000.asm` probes | Uploaded code; inspect each source's load/return/result ABI before invoking it |

The many transport and boundary-study variants are not interchangeable release
images. Their builders and physical records identify version, CRC and exact
bytes. Current monitor commands, refresh enable/disable signatures, reattachment
and result-block semantics are defined by [Loader API v2](../LOADER-API-V2.md).
JukuPoly player/score sources live in [their own project](../../jukupoly/README.md).

## Shared mnemonic diagnostic

`shared-memory-4000.asm` and `shared-cpu-4000.asm` are loader-callable wrappers
around the pinned `juku-common/diag` sources. Unlike the older NASM probes,
their 8080 instructions are written as assembler mnemonics. The memory wrapper
tests and restores `5000h..50FFh` with byte-cell/data-lane and A0..A7 alias
checks, holds one cell through two delay intervals, and records the restored
page checksum; the CPU wrapper covers the ALU/flags,
register-pair, INX/DAD, stack, and PUSH/POP paths. Both write their structured
results from `4E00h` and return.

Both wrappers return `A=00h` even when the diagnostic records a failure. Read
RAM to obtain the verdict:

| Wrapper | Result at `4E00h` |
| --- | --- |
| Memory | Four bytes: data-bit mismatch mask, address-alias boolean, retention mismatch mask, restored-page additive checksum |
| CPU | One byte: `00` pass, `01` ALU/flags, `02` register-pair/increment, `04` stack path failure |

For memory, the first three bytes must be zero; the fourth is a checksum,
not a failure flag. These wrappers overwrite their result block and exercise
the writable stack. The memory wrapper temporarily modifies the tested page;
do not run it over live code, stack or data that another actor may change.
Run the CPU wrapper with interrupts disabled throughout: its INX SP check
temporarily selects `9A00h` as SP. The wrapper does not change interrupt state.

From the repository root, initialize the shared sources and verify the
committed diagnostic binaries. The build uses the pinned zmac source in Intel
8080 mode, compiling it if the executable is absent; no separately installed
assembler is required:

```sh
git submodule update --init --recursive
python3 spinoffs/jukuravi/firmware/build_shared_memory.py --check
python3 spinoffs/jukuravi/firmware/build_shared_cpu.py --check
cc -O2 -Wall -Wextra -o /tmp/jukuravi-shared-memory-test \
  tests/jukuravi_shared_memory_test.c cosim/i8080.c
/tmp/jukuravi-shared-memory-test \
  spinoffs/jukuravi/firmware/shared-memory-4000.bin
cc -O2 -Wall -Wextra -o /tmp/jukuravi-shared-cpu-test \
  tests/jukuravi_shared_cpu_test.c cosim/i8080.c
/tmp/jukuravi-shared-cpu-test \
  spinoffs/jukuravi/firmware/shared-cpu-4000.bin
```

The host prerequisites for zmac are `make`, `bison`, and a C/C++ compiler. Set
`ZMAC` only to deliberately override the pinned assembler. Omit `--check`
from a builder only when intentionally replacing its tracked binary after a
source change; review that diff before using the image on hardware.

## Build and verify

Use the matching `build_*.py` writer, with `--check` to verify the committed
image. The archived `diag-d0-repetition.bin` currently differs from its builder's
output; its `--check` fails. Keep its pinned bytes as historical evidence and do
not present that variant as reproducibly rebuilt by the current script. The
remaining hash pins identify committed artifacts; verify a builder with
`--check` before relying on reproducibility.

For the physical-row monitor:

```sh
python3 spinoffs/jukuravi/firmware/build_d0_row_refresh.py --check
python3 tests/jukuravi_refresh_row_address_test.py
```

From the repository root, the broader gates are:

| Gate | Scope |
| --- | --- |
| `sync/jukuravi_d0_check.sh` | Historical D0/D2 image, cosim and HDL ladder regressions |
| `sync/jukuravi_t28_check.sh` | Transactional monitor and host API |
| `sync/jukuravi_t34_check.sh` | Exact T34 clock-setup metadata, cosim D55 fault bit, TxRDY recovery and CALL/RET; does not execute physical PIT clock timing |
| `sync/jukuravi_t36_check.sh` | Row-address proof, retention model, host/PTY refresh controls, physical-record identities and local RAM probes |

The separate [D55 structural audit](../../../docs/jukuravi-d55-diagnostic-audit.md#structural-simulation-matrix)
executes clocked PIT transfers; its recorded matrix is currently not reproduced
by the script. A T34 cosim pass does not clear that limitation.

A simulator pass does not replace programmer readback, physical clock checks or
measured board acceptance. Preserve hashes and captures in the applicable
physical record rather than duplicating them in this directory overview.

Archived image identities are pinned in [SHA256SUMS](SHA256SUMS), which the
matching builders check. Verify the committed bytes from this directory with
`sha256sum -c SHA256SUMS`; use each builder's `--check` separately to verify
reproducibility.
