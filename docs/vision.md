# Project invariant: one evidence-rooted machine

The end state is one Juku model whose physical connectivity and executable
behavior can be traced back to evidence.

The project has two kinds of authority:

- Factory drawings, photographs, dumps, and measurements under `ref/` are the
  historical authority.
- `kicad/juku.board.json` is the current machine-readable interpretation of
  that evidence. It must retain provenance and explicit boundaries wherever
  the historical record is incomplete.

From that model, the project maintains:

1. a KiCad schematic/PCB and fabrication outputs;
2. an independently written structural HDL model checked by LVS; and
3. runnable device behavior checked against `cosim`, with MAME as a
   reference for selected machine behavior.

`juku_top` executes real firmware. The [boot guard](../sync/boot_check.sh)
compares framebuffer bytes with `cosim` at a bounded video-write stop, and the
[bus guard](../sync/cosim_check.sh) compares ordered CPU-bus events within its
configured window. These checks cover their named ROM and model profiles.
Physical endpoints remain untraced or represented only by boundary nets, and
simulation-only paths still stand in for shared DRAM/video timing; the full
machine has not converged.

No green check has a wider meaning than its scope:

- LVS checks represented schematic/JSON connectivity against structural HDL;
  PCB copper and omitted endpoints require separate audits.
- DRC checks routed geometry, not whether the intended circuit is complete.
- Behavioral regression checks the model, not historical authenticity.
- A checksum identifies artifact bytes; reproducibility requires rebuilding
  those bytes, and fabrication readiness requires the physical-release gates.

`PLAN.md` defines the remaining convergence and physical-release criteria.
