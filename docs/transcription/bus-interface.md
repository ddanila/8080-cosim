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
