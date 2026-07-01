# Transcription — bus interface (sheets 1 + 3)

Trace of the 7 octal transceivers (3× КР580ВА86 + 4× КР580ВА87) + the К170 backplane
drivers (2× К170АП2 + 1× К170УП2) + К580ИР82 latch. Read off the scans.

## What's already modeled (confirmed)
- **Address buffers → `BA`:** **D4 = КР580ВА86** octal buffer, near the CPU, buffering the
  CPU address out to the buffered bus (A[7:0]/A[15:8] → BA). Our model's `buf_8286`
  U_BUFL/U_BUFH = these (2 of the 3 ВА86). [scan]
- **CPU data buffering:** done by the **8238 (КР580ВК38)** system controller (D↔DB) — already
  modeled. [scan/datasheet]

## What's NOT yet modeled — the expansion/backplane interface
The remaining transceivers are the **expansion-bus (backplane) interface**, near the edge
connectors (К170АП2 seen on sheet 3 by connector X2):
- **3rd ВА86 + 4× ВА87** — buffer the buffered address/data/control **out to the expansion
  connector** (the Multibus-style card slots). ВА87 = inverting octal (8287).
- **К170АП2 ×2 + К170УП2 ×1** — the actual backplane line drivers/receivers at the connector.
- **К580ИР82** — octal latch (address latch).

## Honest assessment (the reason this is a meaty sub-pass)
This cluster is **spread across sheets 1 + 3** and its far side is the **off-board
expansion bus** — i.e. a *boundary* (the cards aren't part of this board). So adding these
to LVS means: bus-side connections (BA/DB/control) are `scan`-traceable, but the
connector-side is a `boundary` net. It's real structure (these chips ARE on the board, part
of the 76), but it's boundary-heavy and intricate to trace bit-by-bit — several more crops
across two sheets + a careful triple-sync add per chip.

It is **not needed for the digital twin** (the twin boots without the expansion bus); its
payoff is structural completeness toward 76 + the Phase-B PCB BOM.

## LOCATED + refdes-identified (sheet 1, right edge — 400 dpi)
The backplane transceivers are on sheet 1 (`ДГШ5.109.006`, PDF page 3) along the right edge,
driving the expansion-connector signals. Each has **T** (direction) + **E** (enable):
- **D23** — address transceiver → connector **-ADR0 … -ADRF** (16 bits); internal side ← `BA`.
- **D24** — data transceiver → **-DAT0 … -DAT7** (8 bits); internal side ← `DB`.
- **D25** — control → **-INHIB, -CCLCK, -PMC, -PWC, -IORC, -IOWC**; internal side ← strobes.
- **D29** — control → **-MRD, -PWR, -IOWR, -IORD**; internal side ← `memr_n/memw_n/iord_n/iowr_n`.
(Types = К170АП2/УП2 + ВА86/ВА87 per the spec.) The serial sheet (PDF page 1) additionally
carries the USART support cluster — ТВ1 D381/D382, ТМ2 D281 + ЛН2/ЛА2 gates = the baud/
handshake logic around D11 (ВВ51).

## Why this is a Phase-B batch, not a quick LVS add
The internal side joins the already-modeled `BA`/`DB`/strobe nets cleanly, but the
**connector side has no second endpoint** in the current model — and the LVS netlist allows
**no 1-node nets**. So a faithful add must first **model the expansion connector(s) X1/X2 as
component(s)** (anchoring all -ADRx/-DATx/control nets at 2 nodes), then wire 16+8+control
bits per transceiver. That is a large, mechanical per-bit pass whose natural home is **Phase B**
(it *is* the PCB/expansion BOM). Cluster is now located + identified; the wiring is queued.

## Phase-B STAGE 1 DONE (2026-07) — connector modeled + D29 control transceiver
The expansion connector is now a component (`expansion_conn`, refdes **X1**) — a boundary part that
anchors the connector-side nets so LVS's no-1-node-net rule is satisfied. First transceiver wired:
- **D29 (ВА86)** — traced on sheet 1 (PDF p.3, mid-right). A-side reads the internal command strobes
  **-MRD/-MWR/-IORD/-IOWR** (= `memr_n`/`memw_n`/`iord_n`/`iowr_n`, already-mapped nets → now
  D29 is a *checked* member of each); B-side drives the Multibus connector command pins
  **-MRC (104C), -MWC (104B), -IORC (106C), -IOWC (105B)** (edge-pin codes read off the scan).
- Modeled with **`va86_out`** (a one-way ВА86: internal→connector). The die-accurate boot needs the
  A-side to never drive the strobe nets; the full inout `buf_8286` z-taps them and corrupted the
  synthetic-ROM datapath test (the ekta37 boot survived it, the synthetic ROM caught it). One-way =
  boot-safe + identical LVS connectivity. A-side spare inputs (real -IO/M / -AMWC sources) not yet
  modeled → tied inactive (boundary).
- Guards: LVS **45 instances / 103 matched nets, IN SYNC**; boot_check all byte-identical.

## Phase-B STAGE 2 DONE (2026-07) — D24 data transceiver
- **D24 (ВА87)** — traced on sheet 1 (right strip, between D23 and D25). A-side reads the system data
  bus **DB0..DB7** (now D24 is a checked member of each `DB{i}` net); B-side drives the connector data
  pins **-DAT0..-DAT7** (edge-codes 132C/132B/131C/131B/130C/130B/129C/129B). ВА87 = the *inverting*
  octal, modeled `va87_out` (one-way, `Aout = ~Ain`); inversion is a boundary detail (off-board), so it
  changes neither the boot nor LVS net membership. `expansion_conn` (X1) grew a `dat[7:0]` port.
- Guards: LVS **46 instances / 111 matched nets, IN SYNC**; boot_check all byte-identical.

## Phase-B STAGE 3 DONE (2026-07) — D23 address transceiver (high byte)
- **D23 (ВА87)** — traced on sheet 1 (right strip, above D24). A-side reads the buffered high address
  **BA8..BA15** (now D23 is a checked member of each `BA{n}` net); B-side drives connector address pins
  **-ADR8..-ADRF** (edge-codes 120C/120B/119C/119B/118C/118B/117C/117B). `expansion_conn` (X1) grew an
  `adr_hi[7:0]` port (adr_hi[i] = -ADR(8+i)).
- Note: bus ports must be declared **`[7:0]`** (0-based) — yosys enumerates bus bits from 0, so a
  `[15:8]` connector port canonicalises to ADR_HI0..7 not 8..15 (LVS mismatch until fixed).
- Guards: LVS **47 instances / 119 matched nets, IN SYNC**; boot_check all byte-identical.

**Queued (Stages 3b-4):** the LOW address byte (-ADR0..-ADR7, a *separate* ВА87 above D23 — refdes not
yet read), D25 (control → -INHIB/-CCLCK/-IO/M/…), plus the К170АП2/УП2 backplane drivers — each grows
`expansion_conn` and adds the transceiver the same way.

## ВА86/87 pinout corrected to the scan (2026-07)
A higher-res crop of the transceiver column showed the **real ВА86/87 B-side pin order is descending**:
bit 0 = pin 19, bit 7 = pin 12 (e.g. -ADR0/-DAT0 land on pin 19). The A-side is pins 1-8 (ascending),
OE=9, T=11. D29/D24/D23 were first added with a uniform bit→pin-(12+i) convention (internally
consistent, LVS-green, signal connectivity correct) and are now retyped to a shared **`VABUS`** pinmap
with the scan-accurate descending B-side, so board.json faithfully reflects the schematic. (D4 the
address *buffer* keeps its own BUF8286 pinmap — its BA-bit↔pin net mapping was already scan-traced.)

## Refdes corrected + full command transceiver (2026-07, owner-confirmed)
Owner read the transceiver refdes/signals off the schematic, correcting the earlier stage notes:
- **D23 = -ADR0..-ADR7** (addr LOW, BA[7:0]), **D24 = -ADR8..-ADRF** (addr HIGH, BA[15:8]),
  **D25 = -DAT0..-DAT7** (data, DB). (Earlier I had D23=addr-hi, D24=data — reshuffled: my D23→D24,
  D24→D25, and added the addr-low byte as the real D23.)
- **D29 (ВА86) = the full 8-signal bus-command transceiver** (not 4): B0..B7 =
  **-INHIB(106B), -CCLCK(111C), -IO/M(109B), -MWC(104B), -MRC(104C), -AMWC(102B), -IORC(106C), -IOWC(105B)**.
  A-side reads the 4 known strobes (memw→-MWC, memr→-MRC, iord→-IORC, iowr→-IOWC); the other 4 sources
  (-INHIB/-CCLCK/-IO/M/-AMWC) aren't modelled → tied inactive (boundary).
- **Inversion:** all connector signals are active-low (the `-` prefix) **except CCLCK** (active-high).
  Captured by the transceiver type: ВА87 (D23/D24/D25) *invert* → -ADR/-DAT are `~BA`/`~DB`; ВА86 (D29)
  is non-inverting → the active-low commands pass straight through; CCLCK (active-high) likewise.
- Guards: LVS **48 instances / 131 matched nets, IN SYNC**; boot_check all byte-identical.

**Remaining:** К170АП2/УП2 backplane line drivers + К580ИР82 address latch.

## D58 (К580ИР82) — data-bus latch, LOCATED sheet 2 right-middle (owner trace, 2026-07)
Not an address latch (earlier guess) — it's an **octal data latch in the DRAM data path**:
- **Inputs D1–D8 = pins 1–8** ← a data bus (nets labelled 1..8).
- **Outputs Q1–Q8 = pins 19..12** → a data bus (nets labelled 31..38) that fans to the **РУ5 RAM data
  pins** (e.g. net 38 → a РУ5 "D1") **and** to the output data **D0..D7 (→sheet 1 / connector)**.
- **STB ≈ pin 11** → net "5" (reported as also the A input of D42 ИР16 — surprising, needs confirm).
- **DE/OE = pin 9** ← **D37.6** (ЛА3 section 4,5→6 output; D37 also inverts D42.Q on 12,13→11).
**WIRED (2026-07)** as the **DRAM write-data latch** (architectural read, owner-confirmed direction):
`РУ5 DIN ← D58.Q ← D58 ← DB`. Inputs D1-D8 (pins 1-8) ← `DB`; outputs Q1-Q8 (pins 19-12) → a dedicated
write-data bus (`WD0..7`) → the РУ5 **DIN** pins (pin 2). РУ5 **DOUT** (pin 14) stays on `DB` (read path).
Modelled TRANSPARENT (`ir82_latch`, q=d) so the RAM sees the same write data → **boot byte-identical**;
the real latch holds it stable across CAS/WE (the hardware reason our sim could master-clock-sample writes).
STB (pin 11) + OE (pin 9 ← D37.6 ЛА3) = boundary for now (the STB↔D42.A read was uncertain; deferred).
LVS: **49 instances / 139 matched nets, IN SYNC**; D58 checked on both `DB` (in) and the РУ5 DIN (out).

## К170 backplane drivers — LOCATED (owner, 2026-07)
- **К170АП2 ×2 = D14, D32** (sheet 3, bottom-rightish) — backplane line drivers.
- **К170УП2 ×1 = D104** (sheet 3, left-bottom) — backplane receiver.
These are the physical-edge line drivers (deepest boundary); wiring queued behind D58.

## К170АП2/УП2 are the SERIAL-PORT line drivers (correction, 2026-07)
Located (owner): **D14, D32, D3 = К170АП2** are NOT backplane drivers — they're the **serial-port
line drivers** buffering the ВВ51 USART's outputs to connector **X3**:
- **D14** → SOUT (X3.29/net 308); **D32** → RTS (X3.30/310) + DTP/DTR (X3.51/311);
- **D3** → TTL SOUT (X3.23/303); D12 (ЛА18/ЛА55) → OC SOUT (X3.32/312); R18/R30/R101 = level/pull shaping.
- **D104 = К170УП2** = the serial line *receiver* (SIN, from X3).
So the "К170АП2 by X2" note was wrong — they sit by **X3 (serial)**, part of the USART I/O subsystem, not
the expansion/backplane bus. They're deepest-boundary: connector-side → X3, internal side ← the ВВ51
(D11) TxD/RTS/DTR + the serial glue (D3/D12). Adding them faithfully = modeling the serial output stage
(drivers → X3, inputs ← USART) — a distinct small cluster with boundary value, separate from Phase-B proper.
