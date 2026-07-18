# VJUGA rev B — Video card adoption note (TI.1 / D2.1)

The rev B **Video card** re-uses the VGA *timing chain* from an external project. This
note records exactly what is adopted, its license, and where the line is between the
adopted work and VJUGA-original design — so the provenance is auditable and the license
obligation is met.

## Adopted work

- **Project:** [mengstr/TTL640x480](https://github.com/mengstr/TTL640x480)
- **Pinned commit:** `ea1ecd063d500982263c76a795abd84f77ccb59a`
- **License:** **MIT**, © 2019 **SmallRoomLabs** (permissive — copying and derivative
  works allowed with attribution; the full text is preserved verbatim in
  `LICENSE-TTL640x480` beside this note). This is a genuine *adoption*, unlike the salfter
  RC2014-compat files, which are all-rights-reserved and were reference-only.

## What we adopt (the timing chain, redrawn)

The **640×480 @ 60 Hz VGA sync + blanking generator** built from discrete TTL:

- 3 × 74HCT393 (dual 4-bit counters) — horizontal dot counter + vertical line counter
- 2 × 74HCT00, 1 × 74HCT10, 2 × 74HCT20 (NAND gates) — decode the sync/blank window
  edges from the counter states
- 1 × 74HCT04 (hex inverter) — sync polarity + clocking
- a 3-diode + resistor **discrete NOR** — combines two window terms
- a **25.175 MHz** dot-clock reference (a canned oscillator on our card)

We adopt the **topology and the decode terms** (which counter bits gate hsync/vsync/
blank), not the Eagle layout. It is redrawn in our own `gen_revb_boards.py` netlist so
it flows through our LVS / footprint-guard / DRC / mating pipeline like every other card.
No Eagle files are imported.

## What is VJUGA-original (NOT from TTL640x480)

TTL640x480 is a *timing-only* card (it targets an "eventual 80×25 character card" and
has no CPU bus, no framebuffer). Everything that makes this a VJUGA framebuffer card is
ours:

- **Framebuffer SRAM** (AS6C1008, reused from the mem card — D2.3) holding `0xD800`+9640.
- **CPU bus interface** — address decode of the `0xD800–0xFFFF` window, data buffer
  (74HCT245), and the **scanout-priority contention** logic that asserts open-drain
  `WAIT_N` when a CPU access collides with an active-region fetch (D2.5).
- **Address mux** (74HCT157 ×4) switching the SRAM between the CPU address and the
  scanout (row,col) address.
- **Pixel shifter** (74HCT166) serialising a fetched byte into the 8-pixel dot stream.
- **GAL22V10** carrying the window decode, mode-overlay (MODE0/1), and WAIT equations
  (`rev-b-gal-equations.md`).
- **Mono→RGB resistor DAC** + DSUB-15HD VGA output and 75 Ω terminations.
- The **pixel-doubling + crop/letterbox** mapping of the 320×241 mono source onto the
  640×480 raster (decided by the oracle at TI.2, frozen in `video-timing.json`).

## Attribution

Per the MIT license, attribution is carried in this note, in `LICENSE-TTL640x480`, and as
a silk credit line on the Video card ("VGA TIMING (c) 2019 SmallRoomLabs MIT").
