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

Data bus [D] pins: D0=10, D1=9, D2=8, D3=7, D4=3, D5=4, D6=5, D7=6.
Address bus [D]: A0..A9 = 25..34; A10..A15 on the high pins (1,40,36–39) — **finalize
from the datasheet PDF, the scan's small numbers are ambiguous** [?].

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

## Next
1. Finalize CPU address pin numbers from the datasheet PDF.
2. Refine HDL to chip-level (8224/8238/8286 instances).
3. Build `kicad/juku.board.json` CPU-core block; generate; LVS.
