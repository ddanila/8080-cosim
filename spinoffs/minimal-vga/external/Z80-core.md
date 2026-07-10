# Selected Z80 HDL core

Rechecked: 2026-07-10. The submodule is pinned at
`f7f776b54d67dcd6b19d3b97027dfbc6db6f14f4`, which matched upstream `master`
at the time of the audit.

Selected core:

- Repository: https://github.com/mist-devel/T80
- Local path: `T80/`
- Language: VHDL
- Initial wrapper: `T80se`
- License: 3-clause BSD-style license in the upstream README and source headers.

Why this one:

- VHDL, matching the preferred direction for this spin-off.
- Mature retro-computing core lineage from OpenCores / FPGA Arcade.
- Maintained fork collecting fixes used by MiST/MiSTer-style projects.
- `T80se` exposes a familiar Z80 external bus: `MREQ_n`, `IORQ_n`, `RD_n`,
  `WR_n`, `M1_n`, `RFSH_n`, `HALT_n`, `BUSAK_n`, `A`, `DI`, and `DO`.

Rejected for first pass:

- `hutch31/tv80`: MIT-licensed and well documented, but Verilog rather than
  VHDL. Keep as a fallback if mixed-language simulation becomes easier than
  VHDL integration.
- `gdevic/A-Z80`: GPL-2.0 and more transistor/schematic-oriented, but larger
  and more complex than we need for the first boot path.

Integration rule:

- Treat T80 as external IP. Do not edit submodule files directly for project
  behavior; wrap it from `../hdl/`.
- Keep Z80 `RFSH_n` observable, but the Juku DRAM-refresh experiment must use
  our own original-style DRAM timing/refresh block.
