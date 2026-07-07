# WD1772 / VG93 reverse-engineering reference

Status date: 2026-07-07.

Local files inspected:

| File | SHA256 | Notes |
| --- | --- | --- |
| `/home/ddanila/Downloads/wd1772.pdf` | `d3601f97751b029d7effa493aa5094cd4726759eed0f4f34aa290cdf3305f0ef` | One-page KiCad-generated PDF titled `WD1772`, created 2019-07-13. It is a searchable transistor/gate schematic reference with visible PLA, step, DRQ/INTRQ, DIRC, write-gate/data, data-separator, and host-bus signal names. |
| `/home/ddanila/Downloads/wd1772pla.txt` | `687a62103ae5a89a3daf4c1decb8968d730802522fa142e458031545b7a34b10` | ASCII PLA/PLM table. It has 120 product rows, 19 input columns, and 20 output columns; one row contains `9` markers and needs interpretation before machine use. |

## Value

The user-provided note says the WD1772 transistor/gate schematic shows that
КР1818ВГ93 is effectively a close copy of the older FD1773/WD1772 lineage, down
to block placement and signal naming. The local PDF and PLA table are therefore
useful if this project needs a deeper ВГ93/FD1773-compatible model than the
current boot/media shim or a GPL HDL core can provide.

Concrete uses:

- Confirm the controller-family assumption behind treating WD1772, WD1773,
  FD1773, WD1793, and КР1818ВГ93 references as relevant to the Juku FDC path.
- Cross-check signal names while adapting a full FDC core, especially PLA,
  step/direction, DRQ/INTRQ, data separator, write-gate/data, and host bus
  terms.
- Preserve a pointer to the PLM dump if a future HDL implementation needs to
  validate command-decode or state-machine equations against transistor-level
  material.

## Boundary

The license/provenance of the PDF and PLA text is not established in this repo.
Do not vendor or mechanically translate these files into HDL without an explicit
decision to accept that source boundary. For the current plan they are external
reference evidence only.

This does not change the immediate M2 task: first make `juku_top` reach decoded
WD1793/VG93 I/O and the EKDOS `A>` prompt with `media/disks/JUKU1.CPM`. Revisit
this reference only if controller fidelity becomes the blocker after that
boundary is reached.
