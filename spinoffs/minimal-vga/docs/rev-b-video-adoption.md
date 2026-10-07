# VJUGA rev B — Video card adoption note (TI.1 / D2.1)

The rev B **Video card** adopts the VGA counter topology from TTL640x480.
This note records the adopted scope, VJUGA additions, and required license notice.

## Adopted work

- **Project:** [mengstr/TTL640x480 at the adopted revision](https://github.com/mengstr/TTL640x480/tree/ea1ecd063d500982263c76a795abd84f77ccb59a)
- **Pinned commit:** `ea1ecd063d500982263c76a795abd84f77ccb59a`
- **License:** **MIT**, © 2019 **SmallRoomLabs** (permissive — copying and derivative
  works allowed with attribution; the full text is preserved verbatim in
  [`LICENSE-TTL640x480`](LICENSE-TTL640x480) beside this note).

## What we adopt (the timing chain, redrawn)

The **640×480 @ 60 Hz VGA counter topology and decode terms**:

- 3 × pin-compatible ST M74HC393B1R dual counters — horizontal dot and vertical line
  counters (the exact faster family is our real-silicon correction)
- sync, blanking and terminal-count decode functions, implemented in two ATF22V10s
  using the count ranges frozen in `video-timing.json`
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
  `WAIT_N` when a CPU access collides with a four-dot fetch phase (D2.5).
- **Address mux** (CD74ACT157 ×4) switching the SRAM between the CPU address and the
  scanout (row,col) address.
- **Pixel shifter** (SN74ALS166) serialising a fetched byte into the 8-pixel dot stream.
- **Three ATF22V10s** carrying H timing, V timing/frame division, window decode,
  mode-overlay (MODE0/1), phase arbitration, and WAIT equations
  (`rev-b-gal-equations.md`).
- **Mono→RGB output**: three independent ACT drivers and on-card 470 Ω series
  resistors feeding the monitor's three 75 Ω terminations, plus the DE-15 output.
- **Pixel doubling with bottom-row cropping** maps source rows 0–239 onto the
  640×480 raster. Source row 240 remains in framebuffer memory but is not shown;
  `video-timing.json` freezes this mapping.

## Attribution

Attribution is retained in this note and the full notice in
[`LICENSE-TTL640x480`](LICENSE-TTL640x480), matching the
[pinned upstream license](https://github.com/mengstr/TTL640x480/blob/ea1ecd063d500982263c76a795abd84f77ccb59a/LICENSE).
The current Video PCB has no attribution silkscreen line; preserve the license
notice when distributing copies or substantial portions of the adopted work.
