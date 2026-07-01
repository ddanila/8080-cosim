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

## Video readout + dot-clock chain (sheet 2 bottom-right) — toward-76 video cluster
Traced the video data/timing path beyond cluster #1:
- **Dot clock:** **16 MHz** generated via **АГ3 one-shot D56** (74123, with R59 33k / C8 15n);
  divided by **ИЕ10 counter D102** (СТ16) → **1.23 MHz** char/pixel clock. [scan]
- **Address mux:** a 4th КП14 **D51** (+ strap E14) joins D48/D49/D50 in the µP/video
  address muxing → РУ5 MA. [scan]
- **Video output stage:** **ЛП5 D34** (XOR) combines the pixel stream with **B SYNC**
  (blanking) → **VT2 (КТ315 transistor)** → the **ВИДЕО** connector. [scan]
- **DRAM extent confirmed:** the РУ5 array runs **D60–D91** = 32 sockets (4 banks), of
  which 8 (D60–D67) are populated — validates the memory reduction. [scan]
- **Still to pin:** the **ИР16 pixel shift-register(s)** (PISO serializer: load the
  framebuffer byte, shift out at the 16 MHz dot clock into the ЛП5 combine) — located the
  output + the clock, the serializer itself needs one more crop to nail its load/shift nets.

So the video subsystem = video-address counters (ИЕ7) → mux (КП14) → РУ5 → [ИР16 serialize
@16MHz] → ЛП5+B-SYNC combine → VT2 → ВИДЕО; sync from the 8253 (cluster #1). Structurally
mapped; LVS-instance adds for ИР16/АГ3/ИЕ10/D34 are the next (slow, per-chip-wiring) step.

## Video-output stage — confident refdes/type reads (toward-76 cluster #1)  [scan]
High-res crops of sheet-2 bottom-right (`ДГШ5.109.006 ЭЗ`, "Модуль процессора") nailed the
dot-clock + output chips (corrects earlier guesses — the divider is **D103**, not D102, and
**D34 = ЛП5 XOR**, not a clock chip):
- **D56 (АГ3 = 74123 dual one-shot):** two RC monostables, **R47 40K** + **R58 33K** + caps
  (C 560p / C8) → the **16 MHz** dot clock (label read at D56's output). [scan]
- **D103 (ИЕ10 = СТ16 counter):** clocked by 16 MHz, C/D/LD/R + CO → **1.23 MHz** char/pixel
  clock (label read at the CO net). The dot→char divider. [scan]
- **D34 (ЛП5 = К531ЛП5, XOR "=1"):** pins 12/13→11, combines the pixel stream with **S SYNC**
  (blanking) → the video-mix net. The "combine" stage. [scan]
- **D33 (ЛН1 = К531ЛН1 inverter):** gate "1", pins 1/2 — clock/logic inversion near D34. [scan]
- **Output analog:** **VT2 (КТ315)** transistor + **VD3 (КС147Б, 4.7 V zener)** + R64/R65 430
  + R66 1k → the **ВИДЕО** connector (pins 3–6). [scan]
- A small on-sheet BOM block confirms К565РУ5/РУ6 (DRAM, qty incl. populated 9-ish), К581РУ4,
  К531 ИД7/КП14, ЛА12, ИР82 counts — cross-checks the gap map.

Still open in this cluster: the **ИР16 pixel shift-register** (the actual framebuffer→serial
PISO) — its load/shift nets need one more crop (it sits between the РУ5 data-out latch and
D34). With D56/D103/D33/D34 now pinned, the dot-clock pair is the cleanest LVS add.

## V2-LVS tracing pass (sheet-2 rendered at 400dpi) — output stage confirmed, ИР16 still elusive
Rendered sheet 2 of `ref/schematics/juku_es101_processor_module.pdf` (= juku3000 processor-module
PDF) at 400dpi (13706×9500) and searched the whole video-output region in high-res crops. **Confirmed
(refines earlier reads):**
- **D56 (АГ3):** one-shot — B(1), R(3, via R61 12k), C(14, cap C8), Q̄(4) → the 16 MHz dot clock.
- **D103 (СТ16 = ИЕ10):** CK(2) ← 16 MHz; A/B/C/D preset (pins 3-6), LD(9), P(7)/T(10); out pin 11
  → **1.23 MHz** char clock (pin 13). The dot→char divider.
- **D34 (ЛП5, XOR):** two gates — 9/10→8 (one input = **B SYNC**) and 12/13→11 (one input = **S/G**).
  Combines the pixel stream with sync → the video mix → VT2.
- **D57 (ВИ53 = 8253):** the raster **sync generator** — outputs labelled 1.23M / SHEC R / BAUD R.
- **D50/D51/D52 (КП14):** the µP-vs-video **address** mux; **D53 (ИД7)** the RAS/CAS decode (R-packs).

**Still NOT locatable: the ИР16 pixel serializer.** Searched the output/left/middle bands at 400dpi;
no DIP-16 with the PISO signature (8 parallel-in + serial-out + shift/load) is clearly labelled in
the video path. This matches the original "needs one more crop" flag. **Consequence:** the ИР16 (and
therefore D34's *pixel* input net) can't be added to LVS without inventing a refdes/pinout — which
violates "scan = source of truth". So the video-output stage stays **functional-but-unmapped** in
`juku_top` (arc V2, working: it emits the banner) and its **LVS add is blocked pending a
higher-resolution scan** of the serializer region (or a physical-board read / another sheet).

## ИР16 pixel serializer LOCATED — D42 + D43 (sheet-2 TOP-right)  [scan, clean]
(Pointer from the owner: page-2 top-right corner, "traces are very clean" — and they are. I had been
searching the bottom-right output stage; the serializers are top-right, by the РУ5 array data-out.)
- **D42, D43 — both ИР16** (two 4-bit shift registers = the 8-bit pixel serializer, byte -> 8 pixels).
  Drawn as an `RG` parallel-load box + the `ИР16` shift box. Pinout (both):
  - parallel data in: **D=pin5, C=pin4, B=pin3, A=pin2**  (fed from the РУ5 array data-out side)
  - **LD=pin6** (parallel load), **G=pin8** (enable), **CK=pin9** (clock), **DS=pin1** (serial in)
  - **serial out = pin10**
- **D37 (ЛА3, re-cropped 2026-07):** pins **12 & 13 are TIED TOGETHER and driven by D42.Q (pin 10)**
  — so D37 is an **inverter of D42's serial stream**; output **pin 11** enters the node-"A" analog mix
  (via R38 1k). (D43's pin-10 routes separately to D35/node A — D37 does *not* combine both ИР16.)
  **Added to the LVS netlist** (`la3_gate U_D37`, input ← D42.Q): promotes D42's serial output from a
  dangling pin into a checked net {D42.10, D37.12, D37.13}. Output pin 11 = analog boundary (dropped).
- So the full readout chain is now fully identified:
  РУ5 array data-out -> **D42/D43 (ИР16) serialize @ dot clock** -> **D37 (ЛА3)** -> **D34 (ЛП5) XOR sync**
  -> VT2 -> ВИДЕО.  Refdes + pinout are scan-clean; the remaining detail for the LVS add is the exact
  РУ5-DO -> ИР16-input bit mapping (and whether an ИР82/ВА82 latch sits between) — a focused pass.

## Video-output combine = an ANALOG resistor-summing node "A" (not a digital gate)  [scan, owner+trace]
Refined the output routing (owner reading + crops):
- **D42 / D43 (ИР16)** serial outputs (pin 10) feed the common node **"A"** through resistors
  (R38 1k …) and also drive **D35 (ЛН5, dual inverter: 5→6, 3→4)**, whose output ties to "A" via
  R39 (12k). **D43 pin 1 (DS) is tied to GROUND** (⊥); **pin 8 = G** (a control input, NOT ground).
- **"A" is a COMMON named net** — the **analog video-mix summing node**. Multiple sources tie into it
  through different-value resistors (R38 1k, R39 12k, R61 12k near D34…), building the composite-video
  level. It's drawn as `→ A` arrows all over the sheet; they're one node.
- **"A" → D34 (ЛП5) leg 13**; D34's other leg (12) = sync; D34 out → **SIG** → VT2 → ВИДЕО.
- So the output is a **resistor-summed analog mix** (pixel from D42/D43 + inverted/sync from D35 →
  node A → D34 → SIG), NOT a clean digital combine (corrects the earlier "D37 ЛА3" guess for the mix).
- **LVS-add implication:** the *digital* connectivity is addable (D42/D43 parallel-in ← РУ5 data,
  CK ← dot clock; D35; D34 legs), but node "A" + its summing resistors are the **analog output
  boundary** (like VT2). The exact byte→8-pixel serialization scheme across the two 4-bit ИР16 +
  the analog sum isn't fully pinned, so the runnable sim keeps the abstracted 8-bit serializer while
  the LVS gets the real chips wired per this trace.

## Video arc status (2026-07): V1/V2 done, V3 PARKED (РЕ3-gated)
- **V1** — ИР16 serializer modeled + proven (framebuffer → serial pixel stream → banner). Done.
- **V2** — the video-output stage wired into juku_top (emits composite video) AND the ИР16
  serializers **D42/D43 added to the LVS netlist**, fully wired to real checked nets: data ← DB
  (the РУ5 byte), CK ← DOTCLK16M, LD ← VID_LD. Done. (D34 ЛП5, D35 dual-use ЛН5, node-"A" analog
  mix all traced.)
- **V3 (faithful video-read slot timing) — PARKED, blocked on a physical PROM read.** The µP-vs-video
  arbitration + the *slot schedule* (WHEN video steals a bus cycle) is set by the **К155РЕ3 timing
  PROM (+ АГ3 one-shots)**, and the **РЕ3 contents are un-dumped** (MAME omits them; the twin boots
  byte-identical without them). So the exact slot timing is **not derivable from the schematic** —
  it needs a РЕ3 dump (universal programmer / MCU sweep; РЕ3 ≈ 32×8 ≈ 74188/82S23). A functional-intent
  schedule is possible but would be an *assumed* timing on the boot-critical DRAM path, so per
  "scan = source of truth" V3 waits for the dump. Everything up to the slot timing is modeled;
  when the РЕ3 is dumped, V3 = reclaim the КП14 arbitration (D48–51) + drive the video RAS/CAS from
  the dumped schedule, replacing today's sim va/vq read + abstracted ir16_sr. See project-status.md.
