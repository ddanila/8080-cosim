# Vendored third-party cores

## vm80a — die-accurate i8080 / КР580ВМ80А replica (Verilog)
- Source: https://github.com/1801BM1/vm80a (1801BM1@gmail.com)
- License: **CC-BY 3.0** (https://creativecommons.org/licenses/by/3.0/) — see `license.md`.
- Files: `vm80a.v` (the core, pin-compatible 8080 wrapper + die logic),
  `tb80a.v` + `config.h` (the upstream reference testbench, kept for reference).

Used in Phase C (the merge) to give the LVS-verified structure a real, die-accurate
КР580ВМ80А — the exact CPU the Juku uses — so the schematic can *execute*.
Attribution per CC-BY 3.0: core © 2014–2018 1801BM1@gmail.com.
