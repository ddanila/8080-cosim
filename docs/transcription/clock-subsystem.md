# Transcription — clock subsystem (sheet 2, top-left)  [toward-76 cluster #2]

Traced from the 400-dpi render of the processor-module schematic (`ДГШ5.109.006 ЭЗ`,
top-left corner) — far sharper than the 150-dpi `p2_sheet2.png`. All clock chips are now
**identified by refdes + type**; the output topology (Φ1/Φ2/STB/PST CLK) is read directly.

## Chips (all confirmed)
| refdes | type | role | modeled? |
|--------|------|------|----------|
| **D59** | ЛН1 (hex inverter) | crystal oscillator: Z1 + C73 + R32 1.2K + R34 8.2K, **2 gates** in a Pierce loop → **OSC** | yes (`ln1_osc`) |
| **D40** | ИЕ7 / СТ16 counter | the **divider**: data A/B/C/D, T/P enables (pin 7/10), CR clear (pin 2); Q outputs at pins **14/13/12/11**; R34 13K, R46 200, B6/C6. Q's feed the gate mesh | no |
| **D33** | ЛН1 (inverter) | clock-mesh inverter: pin 2→**8**; pin 8 → D38 pin 9. (Its other gates are routed into the video output — see dram-video-timing.md) | no |
| **D39** | ЛА3 (NAND) | clock-mesh gate (pin 1 in, pin 11 out) | no |
| **D36** | ЛА12 (NAND) | clock-mesh gate: inputs **5/4** → output **6** → D35 pin 11 | no |
| **D38** | ЛА1 (4-in NAND) | inputs **9/12/13/10** → output **8 = STB** (the 8238 STSTB) | yes (`stb_gen`) |
| **D35** | ЛН5 | phase gen: → **Φ1** (pin 10 → R37 360 → pin 7) and **Φ2** (pin 12 → R36 360 → pin 14) | yes (`clk_phase`) |

## Topology (read directly)
`Z1 → D59 (ЛН1 ×2) → OSC → D40 (ИЕ7 divider) → {D33 ЛН1, D39 ЛА3, D36 ЛА12 gate mesh} →
D38 (ЛА1) → STB,  and → D35 (ЛН5) → Φ1 / Φ2`. PST CLK (reset clock) is generated off the
same mesh (top net). Confirmed output nets: **D38.8 → STB**, **D35.10 → Φ1** (via R37),
**D35 → Φ2** (via R36), **D36.6 → D35.11**, **D33.8 → D38.9**.

## LVS re-wire DONE — model de-simplified (36 → 40 chips, IN SYNC)
The model previously tied **D35.11/D38.9 straight to OSC**, collapsing the gate mesh. The
faithful chain is now wired into the LVS model (`hdl/juku_top.v` + `devices.v` + board.json
+ map.json), green at 40 chips / 100 nets, 86/100 scan-grounded:

- **OSC** re-routed: `D59.2 → D40.2` (the divider's clock) — no longer feeds D35/D38 directly.
- **D40 (СТ16, 74161-class)** added: clock = pin 2; Q outputs 14/13/12/11; pin 1 = R, 7/10 =
  enables, 9 = load. `D40.14 (Q0) → D39.13`.
- **D39 (ЛА3)** added: `D40.14 → D39.13`; `D39.11 → D38.13`.
- **D33 (ЛН1)** added: `D33.8 → D38.9` (re-sources D38's former OSC input).
- **D36 (ЛА12)** added: `D36.6 → D35.11` (re-sources D35's former OSC input).
- **D38** upgraded from the `stb_gen` stub to a proper **ЛА1 4-input NAND** (`la1_gate`):
  inputs 9/12/13/10 → output 8 = STB.

Provenance: OSC / D40QA / CLKG_D33 / CLKG_D36 = **scan** (read directly); **D39Y** (D39.11→
D38.13) = **assumed** (the D39→D38 link is read, the exact D38 input pin is inferred from
routing). Deferred (left unconnected, documented): D33/D36 gate *inputs*, D40 data/enable
pins, D38 inputs 12/10 — these feed back from the divider/mesh and need finer crops; they are
honestly un-netted rather than invented.

## Mesh feedback nets TRACED (2026-07, high-res re-crop) — but LVS-DEFERRED [scan]
Definitive reads from a 400-dpi crop of the D40→gate fan-out (upgrading the "need finer crops"
note above — these are no longer un-traced, only un-*added*):
- **D40 pin 14 (QA) → D39 pin 13**  — already modeled (net `D40QA`).
- **D40 pin 13 (QB) → D39 pin 12**  — the deferred D39 input (`la3_gate.a`, tied `1'b0`).
- **D40 pin 12 (QC) → D33 pin 5**   — D33's *second* ЛН1 section (5→6), unmodeled.
**Why still deferred from LVS (a hard boundary, not laziness):**
1. **Abstract-clock coupling.** The runnable model synthesises the status strobe as
   `ststb_n = ~sync` (D38), which *requires* `d39_y = 1` and `clkg_d33 = 1` (constants). Wiring
   D39.12 ← QB (or D33.5 ← QC) makes `d39_y`/the D33 section toggle → `ststb_n` stops being
   `~sync` → the byte-identical boot breaks. These pins were tied to constants for exactly this
   reason. Faithful wiring needs a **cycle-accurate clock-mesh sim** (a distinct effort), not the
   abstract clock. Until then the *connectivity is known* but can't live in the LVS netlist
   (HDL const nets are skipped, so a board-only net would show as only-in-KiCad = mismatch).
2. **Multi-section models.** D33.5→6 is a *different* ЛН1 section than the modeled D33.9→8;
   adding it needs a hex-inverter model (6 sections) as `U_D33`, not the single-section `ln1_inv`.

## D35 video-mix sections (5→6, 3→4) — boundary, not addable [scan]
D35 is one physical ЛН5; its clock sections are modeled as `clk_phase` (pins 10/12/11/13, in LVS).
Its *video* sections (5→6, 3→4) feed the analog node-"A" summing mix (R38/R39) — see
dram-video-timing.md. Both walls apply: `clk_phase` doesn't expose those pins (needs the hex model),
and their outputs are the **analog node-A boundary** (dropped by LVS). Left as boundary.

## Grind status
D37 (ЛА3, D42-serial inverter) was the last gate addable *without* disturbing the runnable model
(its input was a genuinely dangling pin, D42.Q). The remaining sheet-2 glue is either analog-boundary
(node A) or abstract-clock-coupled (the mesh above) — so the misc-gates grind is **exhausted** for
chips coupled to the runnable model. Further LVS growth now needs either a faithful clock-mesh sim
or the Phase-B connector / РЕ3 dump (both bigger, separate efforts).
