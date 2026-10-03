# Shared Juku facts and spin-off consumers

The root reconstruction owns the original-machine evidence. Spin-offs consume
that evidence through references, derived artifacts and focused guards. A
spin-off's new hardware design or qualification result remains specific to
that design; it does not establish the same result on an original Juku.

## Sources

| Shared material | Source | Consumer |
| --- | --- | --- |
| Behavioral reference | `cosim/` and its firmware/framebuffer checks | Rev A/B boot and framebuffer comparisons |
| Firmware | `roms/` | Z80-patched images built by the minimal-VGA ROM tools |
| Small PROM truth tables | `ref/physical-proms/` and `ref/reconstructed-proms/` | Decode models and their focused checks |
| Memory, ports, PIC and model timing | [juku-machine-facts.json](../ref/juku-machine-facts.json) | [Rev B bus contract](../spinoffs/minimal-vga/docs/rev-b-bus-contract.md), board checks and selected HDL constants |
| Owner measurements | [Measured facts](owner-measured-facts.md) and topic-specific evidence | Referenced source boundaries and qualification records |
| Device behavior | Root `hdl/` models | Spin-off simulations using the corresponding devices |
| Bring-up procedure | [Rev A workbench](../spinoffs/minimal-vga/docs/workbench-plan.md) and [Rev B build plan](../spinoffs/minimal-vga/docs/rev-b-build-plan.md) | Staged board validation |

The facts JSON includes provenance for the shared model values. Its timing
assumptions and framebuffer conventions require their recorded scope; they
are not measurements of every firmware mode or physical board. Derived ROMs
and decode outputs must be regenerated from their inputs rather than edited.

## Guard coverage

Run from the repository root:

```sh
python3 scripts/check_spinoff_commons.py
```

The CI guard checks the facts file's required sections, provenance fields,
framebuffer size arithmetic and base-address consistency. It checks that the
Rev B bus-contract document contains the selected canonical values and that
any `FB_BASE` definitions found in Rev B HDL match the canonical base.

Missing consumer files are reported as skipped. The document checks look for
values in text; they do not parse every table field or detect every conflicting
number. This guard does not regenerate ROMs, GAL equations or PROM exports,
or establish complete timing/connectivity agreement across all spin-offs.
Use the corresponding subsystem checks for those boundaries.

## Updating shared facts

1. Record new original-machine evidence in its root source artifact, retaining
   board identity, provenance and uncertainty.
2. Update affected model facts and consumers, then regenerate the relevant
   derived artifacts.
3. Run the commons guard and the affected subsystem checks. Commit the source
   evidence and resulting consumer changes together.

Record findings made on spin-off hardware as spin-off evidence. Promote a
claim about the original machine only when the original-machine sources or a
suitable repeated test support it.
