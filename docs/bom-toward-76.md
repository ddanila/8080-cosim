# BOM gap map — toward the real ~101-chip board

> **TWO COUNTS, both correct (reconciled).** Summing the BOM line-item quantities (Всего column)
> on `ДГШ3.031.006` pp.3–4 gives **~101 socket positions** (page 3 = 37, page 4 = 64; 40 memory +
> 61 non-memory), and the PCB placement independently reached **102 positions** (±1 of the faint
> scan). But the owner's **76** is the **populated**-chip count: per `project-status.md`, only
> **8 of 32 RAM sockets** (one 64 KB К565РУ5 bank) and **2 of 8 EPROM sockets** are populated; the
> other ~26 are **unpopulated expansion sockets**. So **~101 = the max/all-sockets board; 76 = the
> as-shipped populated board** (101 − ~25 empty expansion ≈ 76). The PCB layout shows all socket
> *positions* (max config); the populated subset is what the digital twin models. Not a
> contradiction — just two different things being counted.

The component spec is `ДГШ3.031.006 ВП` (`~/fun/juku3000/docs/…nimekiri komponendid.pdf`, IC list
on pp.3–4). The LVS model (`hdl/juku_top.v` + `kicad/juku.board.json` + `sync/map.json`) currently
net-models **40**; the PCB additionally shows **62 placement-only outlines** (102 positions total).

**Why each addition is real work:** the component list gives type+count *totals*, but a chip
only enters LVS once its **pin-level nets** are traced from the schematic (processor module
`ДГШ5.109.006`, scans in `ref/schematics/` + `juku3000/docs/…protsessori moodul.pdf`). So
toward-76 is a per-cluster *tracing* grind (each like `docs/transcription/dram-video-timing.md`),
not a transcription of the BOM. PROM **contents** (РЕ3/РТ4) still need a dump, but their
**connectivity** can be added now (LVS checks wiring, not bits).

**Tracing tip:** the `ref/schematics/*.png` scans are only 150dpi — often too faint to read pin
numbers. Render the juku3000 processor-module PDF at **400dpi** and sharpen (`magick -sharpen 0x1`);
far more legible. That's how the clock subsystem (`docs/transcription/clock-subsystem.md`) was pinned.

## Modeled today (34) — the booting, interactive core
CPU (D1) · 8238 (D5) · 2× ВА86 addr buf (D4/DLB) · D6 decode-PROM · D7 gate · 2× EPROM
(D15/D16) · 8× РУ5 DRAM (D60–67) · 2× 8255 (D26/D27) · 8251 (D11) · 3× 8253 (D54/55/57) ·
8259 (D10) · clock D35/D38/D59 · I/O decode D2 (74138) · 4× ИЕ7 video ctr (D44–47) ·
2× КП14 addr mux (D48/49) · D53 RAS/CAS decode (ИД7).

## The gap (~42) by cluster — the grind backlog

| # | Cluster | Chips (type ×qty, refdes where known) | Trace source | Serves |
|---|---------|----------------------------------------|--------------|--------|
| 1 | **Video output chain** | КП14 mux D50/D51 (×2), ИЕ10 ctr D102, АГ3 one-shots D56 + (×2–3, 74123), ИР16/ИР6 pixel shift-reg (×1–2), ЛП5/ЛП2 XOR combine, VT2 (КТ315) | `dram-video-timing.md` (mostly traced; ИР16 load/shift needs 1 crop) | **twin** — makes it serialize/emit real video |
| 2 | **Clock subsystem** | ✅ **DONE** — D40 (СТ16), D33 (ЛН1), D39 (ЛА3), D36 (ЛА12) added; D38 upgraded to ЛА1; OSC re-routed through the divider+gate mesh (de-simplified). `clock-subsystem.md` | **scan** (4 nets) + 1 assumed | twin fidelity (gate inputs/data pins deferred) |
| 3 | **DRAM RAS/CAS addressing** | wire the validated К565РУ5 row/col model (`dram_unit_tb.v`) + the 16→8 row/col mux + АГ3 RAS/CAS strobe timing into the twin | partial — row/col split + АГ3 RC un-traced (needs crops) | **twin** — removes the last behavioral abstraction |
| 4 | **Bus / backplane (Phase-B)** | ✅ **DONE** — expansion connector X1 + D23 (addr-lo), D24 (addr-hi), D25 (data), D29 (8 bus commands) all ВА86/87 → -ADR/-DAT/commands; + **D58 (ИР82) DRAM write-data latch**. `bus-interface.md` | **scan** (owner-confirmed refdes + edge-codes) | expansion bus interface + DRAM write path — **49 mapped instances, IN SYNC, boot byte-identical** |
| 5 | **Decode / timing PROMs** | 2× К155РЕ3 (timing-state; contents need dump) + extra К556РТ4 (I/O decode) | connectivity traceable now; contents deferred | fidelity + PCB |
| 6 | **Keyboard encoder** | 74148 priority encoder (col → 3-bit code + GS) | `keyboard.md` (behavior known; schematic pins TODO) | twin (currently modeled behaviorally in ppi0_b) |
| 7 | **Misc gates** | remaining К531/К555/К561 ЛА/ЛН/ЛИ/ТМ/ТЛ2 glue | per-sheet as encountered | completeness |

Counts are read from the scanned spec (pp.3–4: e.g. К170АП2 ×2, К170УП2 ×1, ВА86 ×3,
К556РТ4 ×2, К155ИЕ10/ИР6, К531ИД7/ИД14×4, К561 ИР9/ЛА7/ЛН2/ЛП2/ТМ2/ТВ1) and are ±1 where
the scan is faint; each is pinned exactly during its tracing pass.

## Suggested order
Clusters **1–3** harden the *runnable twin* (video out, real clock, real DRAM addressing) —
highest fidelity payoff. Clusters **4–5** feed the *PCB/BOM* (Phase B). Cluster 6–7 are
opportunistic. Recommend grinding 1 → 2 → 3, each as its own traced LVS-green commit.

## Phase-B status (2026-07): expansion bus DONE — deferred items documented
**Done (49 mapped instances, LVS IN SYNC, boot byte-identical):** the expansion-bus interface +
DRAM write path — connector X1, transceivers D23/D24/D25 (ВА87: addr-lo/addr-hi/data → -ADR/-DAT),
D29 (ВА86: 8 bus commands), and D58 (ИР82 DRAM write-data latch). All tie into real mapped buses
(`BA`/`DB`/strobes/РУ5 DIN) so they're LVS-*checked*, not just boundary anchors.

**Deferred (documented, not modeled) — these are the "missed" chips and why:**
1. **Serial-port I/O drivers (К170АП2 D14/D32/D3, К170УП2 D104 + connector X3).** Turned out to be a
   *separate subsystem* (serial, not backplane): they buffer the ВВ51 USART TxD/RTS/DTR/SIN to X3, with
   level-shaping glue D12 (ЛА18/ЛА55) + R18/R30/R101. **Deepest boundary + near-zero LVS value** (X3
   connector out, USART-stub in). Adding them = a distinct serial-I/O cluster (X3 + 4 К170s + glue +
   fleshing the USART serial outputs). Located + traced (see bus-interface.md); wiring deliberately skipped.
2. **D58 STB/OE control.** D58 is modelled transparent; its STB (pin 11, ≈ a net shared with D42.A —
   uncertain read) and OE (pin 9 ← D37.6, the ЛА3 section 4,5→6 not yet modelled) are left as boundary
   constants. Doesn't affect the boot (transparent latch) or the checked data-bus connectivity.
3. **Unpopulated РУ5 banks (D68–D91).** 3 of the 4 DRAM banks' sockets are unpopulated on the real
   board; only bank 0 (D60–D67) is modelled. Pure PCB-BOM completeness.
4. **Video/DRAM arbitration (V3): КП14 muxes D50/D51, node-"A" analog mix (D34 ЛП5, D35 ЛН5 video
   sections), РЕ3 timing PROMs (×2).** All gated on the un-dumped К155РЕ3 slot-timing PROM — see
   dram-video-timing.md / clock-subsystem.md. Parked, needs a physical PROM read.
5. **Misc glue gates + keyboard 74148.** Scattered К5xx gates (completeness only); the 74148 keyboard
   encoder is almost certainly on the keyboard *module*, not this processor board.

Net: the structurally-meaningful chips (everything that ties into a checked bus/strobe/data net) are in.
What remains is boundary drivers (serial X3), unpopulated sockets, V3-PROM-gated video timing, and glue —
none of which add *checked* structure to the LVS.

## Outline-conversion loop findings (2026-07) — mechanical wins done, rest is coupled
The autonomous conversion loop converted the **mechanical** outlines (memory sockets: 24 DRAM D68-D91
+ 6 ROM D17-D22 = 30 chips, 48->78 net-modeled footprints). Then it hit the remaining functional
chips, which are NOT clean footprint adds — each is coupled to a deferred subsystem:
- **D13/D30 (reset/ready):** D13 drives D5 STSTB (cpu-core.md), conflicting with the clock-mesh's
  `ststb_n=~sync` (D38). Boot-critical STSTB-source reconciliation needed first.
- **D50/D51/D52 (КП14 muxes):** the µP-vs-video address arbitration — converting them faithfully
  means replacing our D48/49 *row/col* simplification with the real µP/video mux, which is **V3 /
  РЕ3-gated** (dram-video-timing.md).
- **D34 (ЛП5):** the analog node-"A" video combine (boundary).
- **Serial block (D3/D12/D32 К170 + X3, D93-D106):** deepest boundary (serial-connector drivers,
  USART-stub inputs) — needs the X3 connector + serial-cluster modeling.
- **D9, D107, D41:** need schematic location + per-chip tracing (the locating bottleneck).
**Conclusion:** the outlines split cleanly into (a) mechanical socket-parallels [DONE] and (b) coupled
functional chips that each need a *deliberate, often owner-guided* pass (like the D29/D58 traces that
succeeded with owner pin-reads) — not an autonomous grind, which just defers. 78/102 positions are
net-modeled; the remaining 24 are the coupled set above.

## Serial cluster converted (2026-07) — D14/D32/D3/D12/D104 + X3
Added the serial-port driver cluster as net-modeled footprints (owner scan img #2):
- **D14/D32/D3 (К170АП2)** buffer the USART serial side to **X3**: D14→SOUT, D32→RTS/DTP, D3→TTL SOUT.
- **D12 (ЛА18 OC-NAND)** → OC SOUT; **D104 (К170УП2)** = SIN receiver → USART RxD.
- The **USART (D11 8251)** now exposes TxD/RTS/DTR/RxD (idle stubs, off the CPU bus → boot-safe); TxD
  fans to the SOUT/TTL/OC drivers (same data, different levels).
**Honest caveats (boundary cluster, low LVS value):** the USART serial engine is a stub (idle outputs),
so the driver *inputs* are consistent-but-not-exercised; the АП2/УП2 pinouts + X3 SIN edge-code are
partly *assumed* (owner img gave the section/output pins + X3 signal codes, not full datasheet pinouts);
PCB placement is *approximate* (parked in the clear band below the DRAM array — the real serial area
still holds un-modeled outlines D28/D93/... to place later).
Guards: LVS **86 instances / 152 matched nets, IN SYNC**; boot_check all byte-identical. PCB: **84
net-modeled footprints + 20 outlines = 104/~101 positions**.
