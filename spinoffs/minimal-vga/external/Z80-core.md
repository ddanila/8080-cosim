# VJUGA Z80 HDL cores

Both T80 and tv80 are maintained simulation paths. Their submodule revisions
are pinned by the parent repository:

| Core | Repository | Pinned revision | Local wrapper |
| --- | --- | --- | --- |
| VHDL T80 | [mist-devel/T80](https://github.com/mist-devel/T80) | `f7f776b54d67dcd6b19d3b97027dfbc6db6f14f4` | `T80se` |
| Verilog tv80 | [hutch31/tv80](https://github.com/hutch31/tv80) | `66a131c38d05ef58b3d8c4f1507a72e6e4aa5d65` | `tv80s` |

T80's README and source headers retain its three-clause BSD-style license;
tv80 retains its MIT license in `LICENSE` and source headers. Preserve those
notices with redistributed sources.

## Integration

- `hdl/z80_minimal_top.vhd` and `hdl/juku_boot_top.vhd` use T80. The synthetic
  smoke runs Z80 mode; the boot top defaults to Z80 mode and also exposes an
  8080-mode parameter for comparison.
- `hdl/vjuga_juku_top.v` and `hdl/revb/revb_cpu_card.v` use tv80 in Z80 mode,
  with `T2Write=0` and `IOWait=1`.
- Keep project behavior in the wrappers under `../hdl/`. Retain the external
  cores as pinned dependencies rather than making local submodule edits.
- CPU `RFSH_n` is observable, but the Rev A DRAM experiment has a separate
  timing/refresh contract. CPU-core compatibility alone does not qualify that
  memory path or physical board timing.

Paths above are relative to `spinoffs/minimal-vga/`. Initialize both dependencies
from the repository root:

```sh
git submodule update --init spinoffs/minimal-vga/external/T80 \
  spinoffs/minimal-vga/external/tv80
```

See [HDL integration](../hdl/README.md) for the T80 compile order and smoke scope,
and [simulation checks](../sim/README.md) for boot and Rev B entry points.
