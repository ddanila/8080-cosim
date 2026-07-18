# VJUGA rev B — order-readiness note (TG.4)

State of the four rev B boards for fabrication. **T1.10 (placing the order) is now a
purchasing decision — the engineering gates below are green.** Last updated 2026-07-18.

## Boards

| board | size (mm) | layers | qty | notes |
|---|---|---:|---:|---|
| cpu | 100 × 70 | 2 | 1 | Z80 + clock + diag; unbuffered (D1.21) |
| mem | 100 × 60 | 2 | 1 | ROM + SRAM + GAL decode |
| io | 100 × 100 | 2 | 1 | 8251 UART + GAL; B3 parts footprinted DNP (D1.26) |
| backplane | 100 × 115 | 2 | 1 | 6 slots; grown past 100×100 per D1.31 (one-off) |

All four pass `check_revb_drc.py --total` at **0 violations / 0 unconnected**, obey the
mechanical mating contract (`check_revb_mating.py`), and boot byte-identical to cosim in
the digital twin (`revb_tier_suite.sh`).

## Connector BOM (the mating interface)

- **Per card:** 1× right-angle male 1×39 (base bus) + 1× right-angle male 1×10 (ext),
  0.1″ pitch, on the bottom (mating) edge — base row 4 mm from the edge, ext row 9 mm
  (contract `mating.json`).
- **Backplane:** 6× (female 1×39 + female 1×10) sockets, base at x=50 / ext at x=14.45,
  16 mm slot pitch; plus USB-C power, reset supervisor + button, FTDI header, power LED,
  and the bus pull-ups/CC resistors.

## Power budget (re-checked against the final BOM)

Unchanged from the bus contract's B1-population estimate: **~712 mA** worst-case, **~47 %**
of a 1.5 A USB-C source (under the 60 % / 0.9 A headroom rule). The backplane discretes
(reset supervisor ~5 mA, power LED ~2 mA, six 4.7 kΩ pull-ups + two 5.1 kΩ CC resistors
≈ 1 mA each) are already included and negligible. Per-column current is trivial for the
0.3 mm bus-column tracks at these draws. Bench-supply remains the safe primary bring-up
input (no PD negotiation — don't assume the full 1.5 A from an arbitrary host).

## Fab package

`kicad/revb/export_fab.sh` writes Gerbers + Excellon drill per board to
`fab/minimal-vga/revb/package/<card>/` (untracked, D1.25) and zips each. SHA256 of a
representative export (regenerable — KiCad embeds timestamps, so re-exports differ; the
board `.kicad_pcb` is the source of truth, content-checked):

| package | sha256 (snapshot) |
|---|---|
| mem.zip | 87e0129826b60796772a2119ba07bc41049ff1735e37fcd504dfefb8d1934046 |
| io.zip | 7b1eb8f0e086ac3b97a1704084c01529bc9049ef72c1b09bb0b2dfee176b3487 |
| cpu.zip | 378945d922c0bf7dbd4bfc22bf4e54881b909caab489a3dd317bcbabb33059ee |
| backplane.zip | ad8577f50c287dbad37441a5cbceca350454ffc46d24e0ab77aa2ddcb211d562 |

## Open risks to weigh before ordering

- **Keying is convention-only (D1.32b):** a reversed card can seat (centred base is
  symmetric). Mitigation is silk/orientation marks + care, not a mechanical block. The
  blocking-post option (D1.32a) is held in reserve for after bench experience.
- **Backplane is 100 × 115** — past the 100×100 cheap-tier cliff. Deliberate (D1.31:
  grow the one-off backplane rather than drop slots or cramp the pitch). Cards stay
  ≤100×100.
- **Slot pitch 16 mm** is tighter than mainline RC2014 (~20 mm). FreeCAD clearance is a
  conservative 4.16 mm; confirm on the bench (T1.11) before committing to many boards.
- **Routing is freerouting-stochastic** (D1.33): the pipeline reliably *reaches* 0/0 but
  does not reproduce byte-identical copper; the `.kicad_pcb` is the artifact of record.
- **Digital twin does not cover signal integrity / bus timing** — VJUGA is slow (few
  MHz), low risk, but this is a bench-validated assumption, not a proven one.

## What ordering unblocks

T1.11 bench bring-up (hardware-blocked): populate cpu/mem/io per the DNP staging,
flash the bring-up ROM, and confirm the banner / RAM-PASS TX stream against the twin.
