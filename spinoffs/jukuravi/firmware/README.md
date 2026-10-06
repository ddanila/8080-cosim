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

## Pinned build identities

The image builders require these SHA-256 pins alongside their byte checks.
This identifies archived variants without treating them as current burn advice.

| Image | SHA-256 |
| --- | --- |
| `diag-d0-adaptive.bin` | `0a76064fc669762faf575474b8a43807d17be57f4a5786cec6d5b25d07511835` |
| `diag-d0-alive.bin` | `dfd4327b2752a143fdbd4c199013e53dfb9dc2b9ea897379f3015b4cda92ec9c` |
| `diag-d0-best-effort.bin` | `a9bc32c22d41acda0d8bed4708f85ce70dabc353abc2a9697a33421545adc098` |
| `diag-d0-buffer-verified.bin` | `e2a18fc2741cc0db10eea278bedede0787220d853ec88dc5dff7e785ba9a95ea` |
| `diag-d0-clocked-pit.bin` | `63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5` |
| `diag-d0-cpu.bin` | `a9ca9d59a2a23891b90eb088e1b6901cc210baca30dc03c46c900048efdb67ec` |
| `diag-d0-d55-stress.bin` | `703514bd36ea3fb1c695b91259040571d601880f475f4562698c851ffbdfd0ce` |
| `diag-d0-echo-filtered.bin` | `4105eadcf2a3f9a310fee82ad5349982b7ad4a85f83cf82cf6b181330177002d` |
| `diag-d0-framebuffer.bin` | `d77c4a381440ed9166a24762b303c8ec0407e6d00c480a151a23c807234d7dd7` |
| `diag-d0-host-recover.bin` | `c92b9760633c4d73a92bd1d2f737dd9c0ac94061c7331eee487be5ce02b69536` |
| `diag-d0-low4k.bin` | `a4fed9185616bbfbef22ab6f0b18202e6d79ad7dbe3b7c46a77a700d3af3676c` |
| `diag-d0-noserial.bin` | `df553334c23a4167b5372f1d9c69d91af0a160c67cdf13b1f4fafab9267a8922` |
| `diag-d0-pic.bin` | `65d84269bcd0d2859e31ca343e3640899c3179b0af6404e184a53a304b1b9496` |
| `diag-d0-pit-debug-slow.bin` | `34c110f209e7ccfffb3a261bea25b3b2e9d361eaaad57bcde638d744e8eed72a` |
| `diag-d0-pit-debug.bin` | `ea52ef2cd3b56727d9c2d2d39cce2442e5faa247ccbb88fb51e91d10978ac22c` |
| `diag-d0-pit.bin` | `b7ab8c3c5d7b32c5402510787216e099b0adbd37d64fb2c4a01f5695eb5401cf` |
| `diag-d0-ppi.bin` | `c75fc47b4966532c67794a317ab23b0e75c32977acb799d3e08a94d53baf2685` |
| `diag-d0-ram-fallback.bin` | `96a9417e4dc3a9270671d76b85500727d8a519c76ff977f15fd48e9f3076c8fc` |
| `diag-d0-ram.bin` | `50f35da507947232c2e2ab0e7b6ab519f3ce16e8310c4c1f02d544b504149baf` |
| `diag-d0-refresh.bin` | `ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274` |
| `diag-d0-repetition.bin` | `d03d39055d3ac6f5d189ee65f39f6f681cf7de63365d4b18495fd8ec60c68bde` |
| `diag-d0-resilient.bin` | `a3182957b68d9c7e3d7c9127ca79c7131fd73bb385066e3065beb9e73b22d673` |
| `diag-d0-robust.bin` | `fa4376b6cb094d13350f4dfb627eac4706c17ec97940feb9bffb01a9339ef658` |
| `diag-d0-romcheck.bin` | `d102a6320f9446e103ab34a07b73ddca72907163a9444c061efdccbd47841da5` |
| `diag-d0-row-refresh.bin` | `32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb` |
| `diag-d0-serial.bin` | `e9bebf4cbcca4556a779eef3fcb42f69706892df28a2cc93fc1f3a5d235eb2e0` |
| `diag-d0-solicited.bin` | `6d174c0164119eda9ae7fa4438c545661f8c315ebd9bf56f8002fc886c1c8c56` |
| `diag-d0-stopwait.bin` | `050e409878d7517b1d235eb3bb63d2580aa2fcaa229cce9f40f7d3783bc1bfab` |
| `diag-d0-txready.bin` | `804562b2a0e28f8380773b2e331587973b5a5928a646ac4f93ee99e355e51f2a` |
| `diag-d0-usart-local.bin` | `c708f78adc9b87ba6dfc926314f3937798814d79f1e66512c9ae8d1db8b03a7f` |
| `diag-d0-waitclass.bin` | `61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2` |
| `diag-d2-loader.bin` | `5396f33244bfac5eae25404958afdcc4c0aac8a06255f7b11e20d2f0bcb0bedf` |
