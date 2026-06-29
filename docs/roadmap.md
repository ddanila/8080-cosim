# Structural-track roadmap (toward the digital twin)

**Goal (north-star, see `vision.md`):** the schematic is the single source of truth →
one model that is simultaneously the **PCB netlist**, the **LVS-checked structure**,
and a **runnable digital twin**.

**Where we are:** 52-chip full-module model, LVS green on real KiCad+Yosys, CI-guarded.
Provenance **28/99 scan-grounded, 71 assumed/boundary** — structure complete, but most
detailed pin-wiring is inferred, not yet traced.

---

## Phase A — Harden the wiring (assumed → scan)  ⟶ *trustworthy netlist*
Convert the 71 assumed/boundary nets to scan-traced, subsystem by subsystem (the way
the CPU core already is 100% scan). LVS stays green throughout; `provenance.py` tracks
the climbing scan fraction. Rough order by leverage:

- **A1 — Address bus B-side:** trace the 8286 buffer outputs → `BA` (input side done).
- **A2 — Memory bus:** EPROM/РУ5 data-pin order + per-chip chip-selects (which decode line).
- **A3 — Clock subsystem:** real pins of D59/D35/D38 + the phase-gate logic (D33/D38).
- **A4 — ИД7 I/O decoder:** isolate its refdes (un-found so far) + A2:A0 / enable / Y wiring.
- **A5 — Address mux + DRAM org:** КП14 select source + pin→`MA` map; how the 20 РУ5 split into banks/video.
- **A6 — Peripheral pins:** 8253 clock sources, 8255 port pins, USART/SIO signals → connectors.

**Milestone A — REACHED (realistic ceiling):** **82/99 scan-grounded + 9 `prom`
(off-schematic decode tables = emulator-recovered maps) + 8 remaining** (RAS/CAS
DRAM-controller timing, OSC/PHI2TTL clock internals, VD video-plane boundary). The
netlist is fabrication-faithful except those inherently-off-schematic / intricate-timing
/ boundary nets. LVS green throughout.

### Progress log
- **A1 done** — 8286 B-side derived from the traced A-side + datasheet (8286 A_n↔B_n):
  D4 B-pins BA8←19, BA9←18, BA10←12, BA11←13, BA12←16, BA13←15, BA14←14, BA15←17.
  BA13–15 (buffer+decode only) → `scan`; BA8–12 stay `assumed` (EPROM taps = A2).
  Provenance **28 → 31/99**.
- **A2 (partial)** — EPROM array = 2764-class; address/data straight bus taps
  (R21-R28 pack); chip-selects = CS4/CS5/CS6/CS7 + OE<-ROE (cross-sheet). `BA8-12`
  flipped to `scan`. Provenance **31 -> 36/99**. DB data nets pending 8238/РУ5;
  CS4-7 decode pending cross-sheet trace.
- **A2 done** — 8238 data pins -> standard 8228 datasheet; РУ5 bit-order confirmed
  on scan (D60->DB0, D61->DB1, ...). Data bus `DB0-7` flipped to `scan`. Provenance
  **36 -> 44/99**. Remaining memory item: EPROM chip-selects CS4-7 are cross-sheet
  (fold into the decoder trace, A4).
- **A3 (outputs done)** — clock Φ1<-D35(ЛН5) pin10, Φ2<-D35 pin12, STB<-D38(ЛА1)
  pin8 (read on scan) -> CPU Φ1/Φ2 + 8238 STSTB. `PHI1/PHI2/STSTB` -> `scan`.
  Provenance **44 -> 47/99**. Oscillator (D59) internals + ФRTTL + RESET/READY
  (Sheet-1 D13/D30) remain structural.
- **A4 done (finding)** — I/O chip-select decode is a **РТ4 PROM (D2)** + glue, NOT
  a 74138 (the power-table ИД7 = D53, the RAS/CAS decoder). Like the memory decode
  (D6), the decode lives in **off-schematic PROM contents** = the known I/O map. So
  the CS *decode* nets can't be wiring-traced to scan (only РТ4-out->chip-CS wiring,
  intricate/untraced). Model decoder relabeled DID7 -> D2. Provenance 47/99 (unchanged).
- **Milestone A refined:** a handful of nets (PROM-decode: CS_*, ROM_SEL, ROE, CS4-7)
  are inherently PROM-internal -> they reach `prom`(contents off-schematic), not `scan`.
  The achievable target is "all WIRING traced; PROM decode contents = emulator-recovered."
- **A5 done (main batch)** — address mux КП14 D48/D49 (A=μP BA, B=video counter,
  Q->РУ5 MA) + ИЕ7 counters D44-46 read on scan. Flipped BA0-7, MA0-7, VCTR, CO ->
  `scan` (bit-parallel per datasheet). Provenance **47 -> 74/99**. Remaining: RAS/CAS
  (D53, DRAM-controller timing, not confirmed).
- **A6 done** — control nets (8238 strobes IORD/IOWR/MEMR/MEMW, INTR/INTA, RESET,
  banking PROM_EN/MEM_MODE0 via the confirmed D7 gate) flipped to `scan`. PROM-decode
  nets (CS_*/ROM_SEL/ROE) marked `prom`. Provenance **74 -> 82/99 scan + 9 prom**.
  **Phase A complete** — 8 remaining are intricate-timing/boundary (RAS/CAS, OSC,
  PHI2TTL, VD) and the 9 prom nets are off-schematic by nature.
- *Note:* provenance is per-net (weakest link), so a net flips to `scan` only when
  ALL its endpoints are traced — progress is lumpy (later steps flip nets in batches).
  A per-endpoint provenance refinement would make the grind more measurable.

## Phase B — Real PCB artifact  ⟶ *fabricable board*
- Swap in the **real Juku schematics** when available (parsers unchanged; only pin maps).
- Either keep the generated net-label schematic and go netlist→footprints→layout, or
  author a proper graphical KiCad schematic (symbols + routed wires).
- **Milestone B:** a KiCad project with footprints + a DRC-clean PCB layout.

## Phase C — Merge the tracks  ⟶ *the schematic runs (north-star)*  [STARTED]
**Step 1 DONE:** vendored **vm80a** (die-accurate КР580ВМ80А, CC-BY 3.0) in `hdl/vendor/`;
smoke test (`hdl/sim/vm80a_smoke_tb.v`) runs a trivial program through the real 8080
bus protocol in iverilog -> store lands correctly (PASS). We now have a real 8080 core.
**Step 2 DONE:** the die-accurate vm80a **boots the real Juku BIOS (ekta37)** in
iverilog (`hdl/sim/juku_sim_tb.v`). The "system" is a behavioral memory/banking/I-O
model mirroring cosim (4-mode overlay, Port-C banking, IN=output-latch), driven
through the real 8080 status-byte bus protocol. **Cross-validated: the VRAM is
byte-for-byte IDENTICAL to cosim** after 6000 video writes — two independent CPU
cores (Verilog die-replica vs C superzazu) produce the same framebuffer. Running
`+maxvram=43000` draws the **full boot banner** (`docs/boot-banner-ekta37-hdl.png`)
-- 42623 video writes, byte-for-byte identical to cosim's complete framebuffer. Key bug found+fixed: the status byte
must be latched on a `clk` edge *inside* the sync window, not at `posedge sync`
(sync and D update on the same f2 edge → a posedge-sync read gets the stale bus).

**Step 3a DONE:** the memory subsystem is now **discrete chip modules on a shared
tri-state bus** (`hdl/sim/juku_chips_tb.v`), not a monolith: `mem_decode_prom` (D6
К556РТ4, the recovered map as a truth table), `eprom` (ekta37), `dram` (К565РУ5),
and an `io_block` whose 8255#0 Port-C register drives the banking mode → D6. The boot
flows CPU → D6 decode → ROM/RAM drive the bus. **Byte-identical to cosim at 6000
video writes** (full-banner / banking-path validation running).

Next steps: (3b) turn the I/O `io_block` into D2-decoded peripheral chips (8255/8253/
8259/8251); (4) drive it through the structural top so the *verified wiring* carries
the boot; (5) keep cross-validating vs cosim + MAME.
LVS stays green (device internals don't change the top netlist).

- Give the **verified structure** behavior: replace HDL device stubs with behavioral
  models (8080 core + ROM/RAM with content + 8255/8253/8259/…), or bind the `cosim/`
  behavioral models onto the netlist chips.
- Simulate the structural model executing the ROM (Verilator/iverilog) → **banner in VRAM**.
- **Cross-validate** against the oracles: `cosim/` software emulator + MAME (same banner,
  same reactions). LVS already guarantees the structure matches the schematic.
- **Milestone C:** run emulation *on the digital schematic*; cosim/MAME become validation oracles.

---

## Sequencing — DECIDED: harden-first (A → B/C)
Make the structure trustworthy *before* giving it behavior, so when the schematic
finally runs (Phase C) it runs on verified truth, not assumptions — consistent with
the project's "scan = source of truth" discipline. Phase C waits until Phase A is
substantially done.

**Immediate next step: A1 — trace the 8286 address-buffer B-side outputs → `BA`**
(then A2 memory bus, A3 clock, A4 ИД7, A5 mux/DRAM, A6 peripheral pins). Each:
read the scan → flip the net's provenance `assumed → scan` → re-run LVS (stays green)
→ watch `provenance.py` climb toward 99/99.
