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

## Harden-against-scan list (turn `assumed`/`convention` → `scan`)
1. Trace address byte-split (D4 vs D7) + exact bit order on the scan.
2. Trace data-bus bit pairing CPU↔8238.
3. Read 8238 (D5) real pinout + the CPU→8238 control wiring.
4. Read Sheet 2: 8224 refdes/pinout + its Φ1/Φ2/RESET/READY/STSTB wiring.

## Next subsystem
Memory: ROM/EPROM array, РУ5 DRAM array, address decode + 4-mode bank logic.
