# Open-source tooling roadmap

Status date: **2026-07-10**.

Status: **EVALUATED / NOT IMPLEMENTED**

This document records tools that may reduce evidence-processing and bring-up
risk. It is a roadmap, not an installation manifest: none of the tools below is
currently required by the repository, and no photo-derived connection becomes
historical evidence merely because a tool proposes it.

## Immediate candidate: registered photo evidence

Pilot [PCB ReTrace](https://github.com/dev-lab/pcb-retrace) on only the VG93
quadrant. It is an AGPLv3, local-first browser application that can align macro
images, mirror top/bottom views, annotate components and nets, and export
KiCad-compatible data. Its output remains candidate evidence rather than a new
source of truth.

Whether or not that pilot is retained, build a small repo-native registration
step with [OpenCV](https://docs.opencv.org/4.x/d1/de0/tutorial_py_feature_homography.html).
The durable artifacts should be ordinary JSON/CSV plus review images, not only
an opaque interactive project:

- source-image path, SHA256, dimensions, side, and acquisition order;
- manual fiducials and the resulting homography;
- mirror/orientation state and held-out registration error;
- endpoint annotations with image coordinates, refdes/pin, confidence, and
  review state;
- generated component/solder overlays and a candidate endpoint table.

Use [Hugin](https://hugin.sourceforge.io/docs/manual/Hugin.html) only to make
convenient multi-row visual mosaics. A flattened panorama is not sufficient
provenance for an electrical endpoint.

The older [PCBRE](https://github.com/pcbre/pcbre) demonstrates useful concepts
such as multiple aligned images per layer, vias, traces, and airwires. It has no
published releases, describes its documentation as incomplete, and carries an
old dependency stack, so it is a design reference rather than a proposed
project dependency.

### Promotion rule

An interactive export or computer-vision result must first become a reviewed
endpoint record with source-image coordinates. Only unambiguous, reviewed
records may be translated into `kicad/juku.board.json`; all others remain
continuity asks. The board model and existing provenance vocabulary remain
authoritative.

## KiCad verification additions

After reviewed photo endpoints begin changing the model, port the existing
minimal-VGA ERC reporting pattern to the main board and add:

- `kicad-cli sch erc` with a machine-readable report;
- `kicad-cli pcb drc --schematic-parity`;
- explicit intentional-no-connect accounting;
- a generated disposition report used by the design-release gate.

KiCad documents both
[schematic ERC and PCB/schematic parity](https://docs.kicad.org/9.0/en/cli/cli.html).
These checks supplement endpoint coverage and LVS; they do not prove that a
historical connection was interpreted correctly.

[KiBot](https://github.com/MicroType-Engineering/KiBot) can automate ERC, DRC,
BOMs, Gerbers, and interactive assembly outputs. A wholesale migration would
duplicate the repository's evidence-aware generation and release scripts, so
KiBot is deferred. A narrowly scoped interactive BOM may be reconsidered after
netlist freeze.

## Powered-board capture

Use [sigrok/PulseView](https://sigrok.org/wiki/Pulseview) when powered-board
validation begins. Add a small Juku-specific Python protocol decoder rather
than relying on screenshots. The sigrok decoder API supports streamed Python
decoders and stacked outputs:
[protocol decoder API](https://sigrok.org/wiki/Protocol_decoder_API).

The decoder should turn selected 8080 address/data/control and FDC signals into
the same bus-cycle vocabulary used by `cosim`, allowing physical captures to be
diffed against the behavioral oracle. Capture raw input files, decoder version,
probe map, sample rate, trigger, board state, and decoded output. Channel count
and voltage compatibility must be checked before choosing analyzer hardware.

## Programmable parts

[minipro](https://gitlab.com/DavidGriffith/minipro) is a maintained open-source
CLI for supported XGecu programmers. Use it for repeatable D15/D16 M2764 reads
only when its current device database explicitly supports the selected part.
Automate two independent reads, byte comparison, all-zero/all-one rejection,
hashing, and programmer/version provenance.

Do not assume that `minipro` supports К155РЕ3 or КР556РТ4. Unless exact device
and adapter support is demonstrated, retain the MCU sweep in
`docs/prom-dump-procedure.md` for those bipolar PROMs.

## Later verification

- [SymbiYosys](https://github.com/YosysHQ/sby) can prove small, targeted digital
  properties after the physical nets settle: mutually exclusive bus drivers,
  legal READY/WAIT behavior, reset convergence, and bounded FDC handshakes.
  Whole-machine formal verification is not planned.
- [ngspice](https://ngspice.sourceforge.io/) or
  [Qucs-S](https://github.com/ra3xdh/qucs_s) can model the composite-video,
  sound, RF, and derived-rail boundaries once component values and topology are
  evidence-complete. Approximate device models remain bench hypotheses.
- [gerbv](https://gerbv.github.io/) can provide a third independent Gerber/drill
  view at final release, supplementing KiCad and Tracespace.

## Adoption exit criteria

A tool becomes a repository dependency only when it has a pinned version or
reproducible environment, a small documented invocation, machine-readable
outputs, a check that fails usefully, and a maintenance benefit larger than its
dependency cost. Until then, it remains an evaluated aid recorded here.
