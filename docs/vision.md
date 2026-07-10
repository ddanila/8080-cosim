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
3. runnable device behavior checked against `cosim` and MAME.

The boot path has converged: `juku_top` executes real firmware and matches the
software oracle. The full machine has not converged while physical pins remain
unnetted or simulation-only paths stand in for the shared DRAM/video timing.

No green check has a wider meaning than its scope:

- LVS checks represented connectivity, not missing endpoints or behavior.
- DRC checks routed geometry, not whether the intended circuit is complete.
- Behavioral regression checks the model, not historical authenticity.
- A checksum proves reproducibility, not fitness to fabricate.

`PLAN.md` defines the remaining convergence and physical-release criteria.
