# WD1772 / VG93 reverse-engineering reference

Status date: 2026-07-07.

Vendored files:

| File | SHA256 | Notes |
| --- | --- | --- |
| `ref/wd1772-vg93/wd1772.pdf` | `d3601f97751b029d7effa493aa5094cd4726759eed0f4f34aa290cdf3305f0ef` | One-page KiCad-generated PDF titled `WD1772`, created 2019-07-13. It is a searchable transistor/gate schematic reference with visible PLA, step, DRQ/INTRQ, DIRC, write-gate/data, data-separator, and host-bus signal names. |
| `ref/wd1772-vg93/wd1772pla.txt` | `687a62103ae5a89a3daf4c1decb8968d730802522fa142e458031545b7a34b10` | ASCII PLA/PLM table. It has 120 product rows, 19 input columns, and 20 output columns; one row contains `9` markers and needs interpretation before machine use. |

## Value

The user-provided note says the WD1772 transistor/gate schematic shows that
КР1818ВГ93 is effectively a direct copy of the older FD1773/WD1772 lineage, not
just a loose functional analog, down to block placement and signal naming. The
local PDF and PLA table are therefore useful if this project needs a deeper
ВГ93/FD1773-compatible model than the current boot/media shim or a GPL HDL core
can provide.

Concrete uses:

- Confirm the controller-family assumption behind treating WD1772, WD1773,
  FD1773, WD1793, and КР1818ВГ93 references as relevant to the Juku FDC path.
- Cross-check signal names while adapting a full FDC core, especially PLA,
  step/direction, DRQ/INTRQ, data separator, write-gate/data, and host bus
  terms.
- Preserve a pointer to the PLM dump if a future HDL implementation needs to
  validate command-decode or state-machine equations against transistor-level
  material.

Additional interpretation notes from the source material:

- The schematic is a KiCad-generated searchable PDF from a transistor/gate
  reconstruction. Component and net names should be searchable in the PDF.
- The note explicitly treats КР1818ВГ93 as effectively a direct FD1773/WD1772
  copy rather than merely a loose "analog", with matching internal block layout
  and signal names.
- Shared term signals named `SHT_xxx` differ between the WD1772 and ВГ93
  reconstructions and need normalization/renumbering before comparing equations.
- Transistors are drawn uniformly in the schematic; real pull-up/"upper"
  transistors in logic gates use built-in normally-on channels.
- The PLM dump was published after the PDF note, on 2019-07-15, and is the better artifact for
  command-decode/state-machine cross-checks than manually reading equations from
  the schematic drawing.

## Boundary

These files are vendored as project reference material, not as HDL-derived
source. Do not mechanically translate the PDF or PLA text into HDL without an
explicit implementation decision. For the current plan they are reference
evidence only.

This does not change the immediate M2 task: first make `juku_top` reach decoded
WD1793/VG93 I/O and the EKDOS `A>` prompt with `media/disks/JUKU1.CPM`. Revisit
this reference only if controller fidelity becomes the blocker after that
boundary is reached.
