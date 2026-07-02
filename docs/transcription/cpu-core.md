# Transcription — CPU core (Sheet 1, left)

Confidence levels: **[T]** topology read directly from the scan; **[D]** pin numbers
from the standard datasheet (КР580ВМ80 = i8080A, pin-compatible); **[?]** to verify.

## Chips identified [T]
| refdes | marking | part | role |
|---|---|---|---|
| D1 | КР580ВМ80 | i8080A | CPU |
| D5 | БК38 (КР580ВК38) | i8238 | system controller — decodes status+DBIN/WR → MEMR/MEMW/IORD/IOWR |
| D7 | БА86 (КР580ВА86) | i8286 | octal bus transceiver — address buffer (a 2nd one buffers the high byte) |
| D13 | ТМ2/ТА2 | 7474-class | reset / -INIT / strobe glue |
| (Sheet 2) | ГФ24 | i8224 | clock generator (crystal Z1); Φ1/Φ2/RESIN cross to Sheet 1 |

## CPU (D1) pins
Control (read on scan, matches datasheet) [T][D]:
`Φ1`=22, `Φ2`=15, `RESET`=12, `HOLD`=13, `INT`=14, `INTE`=16, `DBIN`=17,
`/WR`=18, `SYNC`=19, `HLDA`=21, `READY`=23, `WAIT`=24; power `+5V`=20, `GND`=2, `-5V`=11. [D]

Data bus [D]: D0=10, D1=9, D2=8, D3=7, D4=3, D5=4, D6=5, D7=6.
Address bus [D] (verified, Wikipedia Intel 8080 — note +12V at pin 28 splits the run):
A0=25, A1=26, A2=27, A3=29, A4=30, A5=31, A6=32, A7=33, A8=34, A9=35,
A10=1, A11=40, A12=37, A13=38, A14=39, A15=36.
Power: +5V=20, +12V=28, -5V=11, GND=2.
(Earlier scan-read high-address numbers were wrong — datasheet is authoritative for a standard part.)

## Topology [T]
- **Data path:** CPU `D0..D7` ↔ D5 (БК38) data pins ↔ system data bus `DB0..DB7`
  (БК38 also takes `DBIN`,`/WR`,`SYNC`,`HLDA`,`BEN` and emits the bus strobes).
- **Address path:** CPU `A0..A15` → БА86 buffers (D7 + sibling) → buffered address
  bus, carried to Sheets 2/3 (annotated `(2)`,`(3)`).
- **Reset/clock:** RESIN network (R2 20k, VD1 zener, C1 47, R4 100, R20 1.5k) →
  D13 → `RES`/`-INIT`; `Φ1`/`Φ2` arrive from the Sheet-2 ГФ24.
- Control strobes out of D5 (БК38): `-MRD`,`-MWR`,`-IORD`,`-IOWR` feed memory + I/O
  (seen on the right edge / connector area).

## Implication for the HDL  ← important
The schematic is at **discrete-chip granularity**: 8080 + 8224 + 8238 + 8286. Our
current `hdl/juku_top.v` abstracts all of that into one `cpu_8080` that emits
`memr_n/iow_n` directly. For LVS to compare like-for-like, the HDL top must be
refined to instantiate these as **separate chips** (`cpu_8080`, `clk_8224`,
`sysctl_8238`, `buf_8286`×2) wired on the un-buffered vs buffered buses. Do this
before transcribing the full netlist, so the two sides are at the same level.

## Support-chip pinouts
- **8286 (КР580ВА86)** DIP-20 [datasheet, confirmed against scan EN=9/T=11]:
  A0–A7 = pins 1–8; OE = 9; GND = 10; T = 11; B0–B7 = pins 12–19; VCC = 20.
  Address buffers: **D4** + a sibling (one per byte). A-side ← CPU address,
  B-side → buffered bus BA.
- **8238 (КР580ВК38)** D5: pinout still to source (no clean fetchable datasheet;
  read from scan). Bridges CPU `D0–D7` ↔ system `DB0–DB7`; emits MEMR/MEMW/IORD/IOWR/INTA.
- **8224 (КР580ГФ24)**: on Sheet 2; supplies Φ1/Φ2/RESET/READY/STSTB.

## Verified CPU (D1) pinout — matches scan
8080 standard (note +12V at pin 28 splits the address run):
A0=25 A1=26 A2=27 A3=29 A4=30 A5=31 A6=32 A7=33 A8=34 A9=35
A10=1 A11=40 A12=37 A13=38 A14=39 A15=36; D0=10 D1=9 D2=8 D3=7 D4=3 D5=4 D6=5 D7=6;
Φ1=22 Φ2=15 RESET=12 HOLD=13 INT=14 INTE=16 DBIN=17 /WR=18 SYNC=19 HLDA=21 READY=23 WAIT=24;
+5V=20 +12V=28 -5V=11 GND=2.

## Open accuracy note
Pin numbers for the support chips are confident (8080 + 8286 done). The exact
**wire order** (which CPU address bit → which 8286 A-pin → which BA bit, and the
byte split between D4 and its sibling) needs careful per-wire tracing on the scan —
the slow part. For an *independent* LVS check the wire order must be read from the
scan (not assumed), else the check is circular.

## Status: CPU-core block built + LVS-green — but mostly NOT scan-traced yet
`kicad/juku.board.json` holds the CPU core (D1 8080, D4/D7 8286, D5 8238, D90 8224)
→ `kicad-cli` netlist → **LVS vs refined HDL = IN SYNC (33 nets)**. Every net and
chip carries a **provenance tag**; run `python3 sync/provenance.py kicad/juku.board.json`.

**Honest provenance right now:** scan/datasheet-grounded nets = **0/33**.
- `scan`-grounded: chip *identities* (D1=8080, D4=8286, D5=8238) and D1/D4 *pinouts*.
- `assumed` (24 nets): address + data **bus bit-order / byte-split** (straight-through, NOT traced).
- `convention` (9 nets): clock/control wiring (8224↔CPU, CPU↔8238) — **8224 on Sheet 2 not even read yet**; pure 8080-system convention.

So the *structure* is right but the *wires* are inference, not the scan. LVS only
proves the schematic-model matches the HDL-model — both currently encode the same
assumptions, so this is a consistency check, not yet an independent verification.

## Hardening progress — 19/33 nets now scan-traced
DONE (flipped to `scan`):
- **Address low byte**: CPU A0–A7 → D4 (8286) pins 1–8, **straight** (col-3 pin
  numbers on the scan read 1,2,3,4,5,6,7,8). 8286: A=1–8, OE=9, T=11, B=12–19.
- **Data bus**: CPU D0–D7 → D5 (8238), straight connectivity traced.
- **8238 (D5) control pinout** read off the scan, matches standard 8228:
  STSTB=1, HLDA=2, WR=3, DBIN=4, BUSEN=22, INTA=23, MEMR=24, IORD=25, MEMW=26, IOWR=27.
  (D5 *data* pin numbers still placeholder — interleaved D/DB, hard to read; connectivity is straight.)
- **Control into 8238**: DBIN (CPU17→D5.4), WR (CPU18→D5.3), HLDA (CPU21→D5.2).

CORRECTION found by tracing: **D5 STSTB (pin1) is driven by D13 (ТМ2), NOT the
8224** — our HDL/convention models 8224→8238; that net is tagged
`convention-WRONG:scan-says-D13` and must be remodeled (add D13).

- **Address HIGH byte traced**: it's **D4** that buffers A8–A15 (correcting the
  earlier D4=low guess); **D7** buffers the low byte. The 8286 A-pins are assigned
  for **PCB routing, not address order** — traced physical pins of D4:
  A8→8, A9→7, A10→1, A11→2, A12→5, A13→4, A14→3, A15→6 (recorded in
  `_traced_D4_highbyte_Apins`). Bit identity is preserved end-to-end, so LVS stays
  at the logical level (CPU A_k ↔ BA_k) and is green.

**MAJOR correction (from Sheet 2): there is NO 8224 (ГФ24).** The clock is
**discrete**: crystal Z1 + D59 (ЛН1) oscillator + phase gates D33/D38/D36/D35,
producing Φ1/Φ2 (via D35 ЛН5), STB (via D38 ЛА1, pin 8). RESET ← D13 (Sheet 1 RC),
READY ← D30, 8238 STSTB ← D13. The fictional 8224 has been removed from the HDL/model.

**Status: CPU core = D1(8080)+D4(8286 high)+D7(8286 low)+D5(8238). All 27 internal
nets scan-grounded → IN SYNC.** Clock/reset/ready/ststb are **boundary** signals to
the discrete clock subsystem (see `_boundary_to_clock_subsystem` in juku.board.json).

NEXT subsystems:
1. **Clock/reset subsystem**: D59 osc + D33/D35/D36/D38 gates (Sheet 2), D13 reset,
   D30 ready — transcribe + model (replaces the removed 8224).
2. **Memory**: ROM/EPROM + РУ5 DRAM array + decode + 4-mode bank logic.
3. **PCB fidelity (later)**: per-instance 8286 pinmaps for routed A/B pins; D5 data pins.

## Next subsystem
Memory: ROM/EPROM array, РУ5 DRAM array, address decode + 4-mode bank logic.

## Outline→footprint conversion status (2026-07, loop)
Converting the reset/ready glue to net-modeled footprints hit a **boot-critical discrepancy** to
resolve first:
- **D13 (ТМ2)** per this doc drives **D5 STSTB (pin 1)** — but the current LVS model synthesises the
  status strobe in the clock mesh as **`ststb_n = ~sync` via D38 (ЛА1)**. Both can't be the STSTB
  source. Wiring D13→STSTB (faithful) would fight/replace D38 and risks the byte-identical boot, so
  D13's conversion needs a **deliberate STSTB-source reconciliation pass** (trace D13's clock/D
  inputs, confirm whether D38 is really a different gate, re-home ststb_n), NOT a blind footprint add.
- **D30 (ready)** + D13's reset output land on `ready`/`reset_sys`, which the boot-tb **forces**
  (boundary) — so those *can* be added footprint-safely, but locating their exact pins needs the
  CPU-sheet crops (D1/D13/D30 sit together; Φ1/Φ2 arrive from Sheet-2, so the CPU block is elsewhere).
**RESOLVED (2026-07):** STSTB reconciliation DONE. D13 (ТЛ2 dual Schmitt NAND) is now the modeled
8238 status-strobe source: section B `ststb_n = ~sync` -> D5 STB(pin1); section A = RESIN Schmitt ->
RES (boundary). D38 (ЛА1) re-homed to a clock-mesh strobe (no SYNC input, output = boundary stb_d38).
SYNC now routes to D13, not D38 -- matching the scan (`convention-WRONG:scan-says-D13` net corrected).
Modeled ~sync (Φ-gating tied high) so the boot stays **byte-identical** (all 6 guards green). D13 is a
net-modeled footprint. LVS 80 mapped instances, IN SYNC.
