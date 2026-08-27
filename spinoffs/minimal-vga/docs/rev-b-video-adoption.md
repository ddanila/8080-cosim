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

The **640×480 @ 60 Hz VGA counter topology and decode terms**:

- 3 × pin-compatible ST M74HC393B1R dual counters — horizontal dot and vertical line
  counters (the exact faster family is our real-silicon correction)
- the original counter-bit terms that define sync, blanking and terminal counts; these
  are re-expressed in two ATF22V10s rather than copying the original NAND/diode circuit
- a **25.175 MHz** dot-clock reference (a canned oscillator on our card)

We adopt those **counter/decode concepts**, not the Eagle gate-level circuit or layout.
The VJUGA implementation is redrawn in our own `gen_revb_boards.py` netlist so
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
- **Address mux** (CD74ACT157 ×4) switching the SRAM between the CPU address and the
  scanout (row,col) address.
- **Pixel shifter** (SN74ALS166) serialising a fetched byte into the 8-pixel dot stream.
- **Three ATF22V10s** carrying H timing, V timing/frame division, window decode,
  mode-overlay (MODE0/1), phase arbitration, and WAIT equations
  (`rev-b-gal-equations.md`).
- **Mono→RGB output**: three independent ACT drivers and on-card 470 Ω series
  resistors feeding the monitor's three 75 Ω terminations, plus the DE-15 output.
- The **pixel-doubling + crop/letterbox** mapping of the 320×241 mono source onto the
  640×480 raster (decided by the oracle at TI.2, frozen in `video-timing.json`).

## Attribution

Per the MIT license, attribution is carried in this note, in `LICENSE-TTL640x480`, and as
a silk credit line on the Video card ("VGA TIMING (c) 2019 SmallRoomLabs MIT").
