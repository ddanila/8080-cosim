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

## Mesh feedback nets TRACED (2026-07, high-res re-crop) — now ADDED to LVS [scan]
Definitive reads from a 400-dpi crop of the D40→gate fan-out:
- **D40 pin 14 (QA=Q0) → D39 pin 13**  — modeled (net `D40QA`).
- **D40 pin 13 (QB=Q1) → D39 pin 12 = D36 pin 5**  — ADDED (net `D40Q1_D39`, 3 nodes); Q1 fans to
  D39.12 (`la3_gate.a`) and D36.5 (`la12_gate.a`).
- **D40 pin 12 (QC=Q2) → D33 pin 5**   — ADDED (net `D40Q2_D33`); D33's 2nd ЛН1 section (pin 5→6).
- **D33 pin 6 → D36 pin 4**            — ADDED (net `D33_6_D36`); D33 section output → `la12_gate.b`.
- **D36 pin 6 → D35 pin 11**           — modeled (net `CLKG_D36`); the ЛА12 output feeds the ЛН5 phase gen.
The full mesh loop D40 → {D39, D33} → D36 → D35 is now in the LVS netlist (owner-confirmed trace).
D33's top-section input is **pin 9** (from the C6/R46 oscillator RC — a boundary), corrected from the
earlier approximate pin-2.

**Resolved (was: "LVS-deferred, abstract-clock coupling").** These were blocked because wiring
them made `d39_y` toggle → broke the `ststb_n = ~sync` abstraction. Two changes unblocked them:
1. **Functional mesh chips.** `ln1_osc` (D59), `ct16_ctr` (D40) and a dual-section `ln1_dual`
   (D33) are now real (were z-stubs / single-section). LVS still reads them as `-lib` blackboxes,
   so only the *ports/nets* matter to the check; the bodies are sim-only.
2. **Frozen-divider boot / running-divider proof.** The boot-tb ties `D59.xin = 0`, so the divider
   sits at 0 → `d39_y = clkg_d33 = 1` → `ststb_n = ~sync` **unchanged → boot stays byte-identical**.
   A separate `hdl/sim/clock_mesh_tb.v` drives the crystal with a real clock and proves the running
   divider (all 16 states) + D39 feedback still yields a **valid SYNC-qualified `ststb_n`** (it
   narrows, doesn't vanish). So the mesh is faithful *and* the boot is preserved.

**D38 (ЛА1) STB gate — fully traced (2026-07, owner):** pin 9 ← D33.8 (clkg_d33), pin 12 ← **SYNC**,
pin 10 ← **D39.11** (d39_y, net `D39Y` — corrected from the earlier pin-13 assumption), pin 13 tied
high (the 4th NAND leg). So `ststb_n = ~(clkg_d33 & sync & d39_y)` — a SYNC-qualified strobe, and the
`D39Y` net now lands on D38.10.

**Still open:** D33's pin-9 section input is the oscillator RC (C6/R46) — an analog boundary, tied to
a constant in the model.

## CPU-on-mesh-clock — DONE (2026-07) [self-clocking boot proven]
The die-accurate CPU now boots **entirely on the mesh's own clock**, no forced Φ1/Φ2, no external
sampling clock. Compile juku_top with **`-DSELF_CLOCK`** and:
- **D40 divider runs** on the crystal (`clk` → D59 → osc_clk). With a 10 ns crystal, `d40_q`
  increments every 10 ns.
- **`sclk` (vm80a `pin_clk`) = `d40_q[0]`** — the divider LSB (20 ns period).
- **Φ1 = `~d40_q[1]`, Φ2 = `d40_q[1]`** — generated by D35 (`clk_phase`) from the divider phase bit
  (`phsel`, a sim-only pin dropped by the LVS allowlist). 40 ns two-phase.
This reproduces the boot-tb's exact relationship — one `sclk` posedge mid-phase, phases change on
`sclk` negedge (no sampling race) — but self-generated. **`juku_selfclk_tb` boots ekta37
byte-identical to the cosim reference** (guarded in `boot_check.sh`). The one remaining abstraction is
D35's *analog* RC-shaped Φ1/Φ2 waveform (R37/R36 + clock caps) — not derivable from the netlist — so
the sim locks a valid two-phase to the divider phase directly (`phsel`); the *connectivity* (D36→D35,
divider→gates) is the real traced mesh. The forced-clock `juku_top_tb` remains the default (no define)
and is unchanged, so all existing guards are intact.

Why a sim-only `phsel` bit rather than deriving Φ1/Φ2 from the real mesh node clkg_d36: with the
gates as traced, `clkg_d36 = ~(d40_q[1] & ~d40_q[2])` is an irregular waveform (the clean two-phase
comes from D35's RC shaping, which is analog). Locking to `d40_q[1]` gives the clean valid two-phase
the die needs while keeping the mesh connectivity honest.

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
