# Vendored third-party cores

## vm80a — die-accurate i8080 / КР580ВМ80А replica (Verilog)
- Source: https://github.com/1801BM1/vm80a (1801BM1@gmail.com)
- License: **CC-BY 3.0** (https://creativecommons.org/licenses/by/3.0/) — see `license.md`.
- Files: `vm80a.v` (the core, pin-compatible 8080 wrapper + die logic),
  `tb80a.v` + `config.h` (the upstream reference testbench, kept for reference).

Used by the current structural model to execute Juku firmware through an
8080-compatible, die-derived CPU implementation.
Attribution per CC-BY 3.0: core © 2014–2018 1801BM1@gmail.com.

The local wrapper/core parameter `FAULT_A12_INCREMENT_HIGH_LOSS` defaults to
zero and is a diagnostic extension for CS00015. It removes only the bit-12
retain-high/no-carry term from the shared register-unit incrementer. The clean
default remains upstream-equivalent; `sync/jukuravi_vm80a_a12_check.sh` guards
both modes against the physical direct-register signature.
