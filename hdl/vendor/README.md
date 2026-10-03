# Vendored third-party cores

## vm80a — die-derived i8080 / КР580ВМ80А core (Verilog)

- Source: https://github.com/1801BM1/vm80a (1801BM1@gmail.com)
- License: **CC-BY 3.0** (https://creativecommons.org/licenses/by/3.0/) — see [the retained license](license.md).
- Files: `vm80a.v` (the core, pin-compatible 8080 wrapper + die logic),
  `tb80a.v` + `config.h` (the upstream reference testbench, kept for reference).

Used by the current structural model to execute Juku firmware through an
8080-compatible, die-derived CPU implementation.
Attribution per CC-BY 3.0: core © 2014–2018 1801BM1@gmail.com.

The local wrapper/core parameter `FAULT_A12_INCREMENT_HIGH_LOSS` defaults to
zero and is a diagnostic extension for CS00015. It removes only the bit-12
retain-high/no-carry term from the shared register-unit incrementer. At zero, the
parameter selects the clean increment/decrement result; it does not enable
the injected fault.

Run `sync/jukuravi_vm80a_a12_check.sh` with NASM and Icarus Verilog installed.
It assembles the register probe and checks five result words in both clean and
fault modes, reproducing the selected CS00015 direct-register signature.
That focused check does not establish complete upstream equivalence, every
8080 instruction, or the transistor-level cause of the physical fault. For
CPU instruction coverage, see
[the instruction differential guard](../../docs/cosim-runtime-reference.md#how-it-works).
