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

## Key finding: the current LVS model SIMPLIFIES the clock
`hdl/juku_top.v` ties **D35.11 and D38.9 directly to the OSC net** (the gate mesh collapsed
to a single oscillator node). The real circuit interposes the **D40 divider + D33/D39/D36
gate mesh** between OSC and the Φ/STB generators. The model is *functionally* fine for the
twin (the sim drives the clock as a boundary anyway) and LVS-green, but it is not the
faithful connectivity.

## Why no LVS chip-count add yet (honest)
A faithful add must re-wire the mesh as a unit — partially re-routing D35.11/D38.9 off OSC
would leave OSC with <2 nodes (no dangling-net support) unless D40's clock is simultaneously
placed on OSC. Two residuals block a clean, non-invented re-wire:
1. **D40's exact pinout/type** — outputs at 11-14 + T/P enables read like a 74161-class
   synchronous counter, but the label reads "ИЕ7" (74193); which clock pin OSC drives needs
   disambiguation (datasheet cross-ref + one more crop).
2. **Gate-input routing** — which D40 Q-output feeds which of D33/D39/D36 inputs is only
   partially legible.

So this pass is a complete **identification + output-topology** trace (major understanding
gain, chips pinned for the gap map); the LVS re-wire is the next focused step once (1)+(2)
are resolved. No wiring invented.
