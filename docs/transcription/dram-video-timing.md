# Transcription — DRAM timing + video address (Sheet 2)

Cluster #1 of the "trace it from the PDF" pass. Read off `ref/schematics/p2_sheet2.png`
(5140×3563) in high-res crops. Confidence: **[scan]** read directly, **[scan~]** structure
read but some pin-level nets at the edge of legibility, **[?]** not yet found.

## RAS/CAS decode — D53 (ИД7 = 74138)  [scan]
The РУ5 RAS/CAS/bank-select lines are decoded by **D53 (ИД7)**, read clearly:
- **Enables:** G1 (pin 4, active-H), G2 (pin 5), G3 (pin 6) — G1 is the **timed** gate
  (the RAS/CAS strobe window); G2/G3 condition it.
- **Selects:** A (pin 1), B (pin 2), C (pin 3) — fed via **config straps E2 / E3** plus
  address bits (bank/region select). The straps appear as jumper positions 53.x.
- **Outputs:** Y0 (15), Y1 (14), Y2 (13), Y3 (12) → series **R49–R52 (100 Ω)** →
  pull-ups **R53–R56 (5.1 k)** → the array's RAS/CAS/bank lines (nets tagged `E`).
- This refines our `rascas_dec U_D53` model (was `.a/.b/.c/.g/.y_n` placeholder) with the
  real pins + the R-pack. **RAS/CAS *decode* → `scan`.**

## RAS/CAS timing — АГ3 one-shots + D39 latch, clocked by ΦRTTL  [scan~]
D53's G1 (timed) enable is driven by a small timing block: **АГ3 (74123) one-shots**
(retriggerable monostables — the RAS→CAS delay / precharge) + a **latch (D39)**, gated by
the **ΦRTTL** clock. Structure is clear; the exact one-shot→enable net + R/C values are
partially legible (finer scan or follow-up crop needed for the precise timing constants).

## Video address generation → РУ5 MA  [scan]
- **ИЕ7 counters D44–D47** (74193, "СТ16" ÷16) cascade (CO chain) = the **video raster
  address counter**, clocked by ΦRTTL-domain.
- **КП14 muxes D48 / D49 (/ D50)** (74157, "MX"): **A-inputs = µP address, B-inputs =
  video-counter address**; **select = config strap E13** (the "VIDEO ADDRESS / µP ADDRESS"
  arbitration), enable G. Y-outputs → РУ5 **MA**.
- So the КП14 stage is the **µP-vs-video** arbitration (confirmed by the explicit
  `VIDEO ADDRESS / µP ADDRESS` labels). The 16→8 **row/col** muxing for the РУ5 is the
  remaining timing detail (which select toggles MA between high/low byte vs RAS/CAS) — to
  finish from the АГ3 timing block.

## Video sync — the 8253 PITs generate it  [scan]
**КР580ВИ53 (8253) D54 / D55 / D57** channel outputs are labeled **`1MHz`, `HOR RTR`
(horizontal retrace), `H.SYNC`, `VER RTR` (vertical retrace), `VER.SYNC`** — i.e. the
timers are the **raster sync generator**, not just baud/sound. The CPU programs them via
the I/O bus (CS/A0/A1/RD/WR/D0–7) — these are the **boot's OUT writes to ports 0x10–0x1B**.
Resolves the old "timer .clk()/outputs = boundary": timers → video sync is now traced.

## Clock subsystem (Sheet-2 left)  [scan]
Crystal **Z1** (+ C73, R32 1.2k) → oscillator/divider across **D33/D34/D35/D36/D38** and
flip-flops/latch **D37/D39**, plus **D58/D59** → **Φ1, Φ2, ΦRTTL, STB, PST CLK (reset)**.
More detailed than the earlier "D59/D35/D38" sketch.

## Still open (cluster #1 residuals)
- **The 2× К155РЕ3 PROMs** — NOT located in the Sheet-2 regions cropped so far (clock /
  mux / array / decode / timing). Likely elsewhere (another sheet, or an un-cropped region).
  Their role (video/DRAM-timing state? char-gen?) is the headline open item. **[?]**
- **Exact RAS/CAS timing nets** (АГ3 one-shot outputs → D53 G1, R/C constants) — partial.
- **Row/col select** for the РУ5 16→8 addressing — to pin from the timing block.
