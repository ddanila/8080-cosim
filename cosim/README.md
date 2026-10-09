# Native emulator compatibility paths

The canonical emulator is [dac-emulation](https://github.com/ddanila/dac-emulation), pinned by the `third_party/dac-emulation` Git submodule. Initialize it after cloning or pulling a changed pin:

```sh
git submodule update --init third_party/dac-emulation
```

The four C sources and three headers in this directory only forward to that dependency. Existing scripts and sibling CP/M checkouts can keep compiling the same source list, including commands without extra include flags:

```sh
cc -O2 -o /tmp/trace cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
```

`trace.c` combines the native runner, machine core, and shared tracing; `juk_disk.c` combines the disk adapter, shared media, and native file storage. The CPU and FDC files forward directly. Do not link these wrappers together with the DAC library: choose one build route. Headers and feature-test macros resolve inside the dependency, so callers need no additional build system.

Make emulator changes in `dac-emulation`, validate them there, and update this repository's submodule pin. Keep hardware reconstruction, HDL, machine-specific verification, rendering/disassembly tools, firmware evidence, and photographs here. `juku-common` continues to own shared guest software.

Fast native consumer checks:

```sh
bash sync/emulation_check.sh
```

No HDL or external ROM/media is needed for that check. Full existing hardware guards remain available separately. Known automatic-PTY and structural-HDL failures recorded during extraction are not fixed by changing dependency ownership; see the dependency's `docs/juku-extraction.md`.

The CPU's original MIT notice remains in `I8080_LICENSE`; the dependency's `LICENSE` and `NOTICE` govern its sources. The smoke-kit build includes those notices and records the dependency commit while retaining its v2 executable paths and manifest contract.

## Migration validation

The initial consumer pin is `06f11ed923893f40e10dfbafb6c571e38d52a182`.
Against the pre-migration `8080-cosim` revision `8e74542e`, ten bounded native scenarios match RAM/state, framebuffer, bus/read traces, stdout and stderr exactly. The fast consumer checks pass, as do both CP/M repositories' unchanged sibling-checkout builds and their checkpoint checks. The exported smoke-kit source compiles and passes the checkpoint check; this is not a claim of a locally rebuilt/published container image. Keyboard-matrix/photo and refresh-row source guards pass. CI manifest, timeout and selector tests pass. No full Verilog simulation was run for this migration.
