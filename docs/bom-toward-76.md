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

## ROUTABILITY VALIDATED (2026-07) — the board routes, DRC-clean
The generated 84-footprint board **fully routes**: freerouting v2.2.4 (Specctra DSN via pcbnew →
`.ses` import) auto-routed **819/820 connections in 72 s** (3603 tracks + 85 vias, 2 layers); the one
router-resistant link (MA4 through the congested DRAM-array channel — deterministic plateau across
runs) was **hand-routed** (a 2-via detour dodging the socket pad columns, PHI1, and the row-4 pad
row). Final board `kicad/juku_routed.kicad_pcb`: **0 unconnected, 0 electrical DRC violations**
(remaining 32 = silkscreen cosmetics). Copper-to-edge rule set to 0.3 mm (standard fab capability;
freerouting hugs the outline and KiCad's 0.5 default flags it — moving routed copper blindly creates
shorts, learned the hard way). Validation en route also caught **2 real placement shorts**
(RAM_SEL/MA1: clock column D36/D53 overlapped the bank-1..3 DRAM footprints) — fixed in the generator.
**What fab still needs (in order): power nets (GND/+5/+12/-5 — the big one), real connector footprints
(X1/X2/X3/X9 are silk), passives (R/C), then gerbers.**

## POWER DISTRIBUTION netted (2026-07) — from the schematic's own power table
Transcribed the sheet-1 power table («Подключение питания к выводам ИС») + X8 power connector
(**61=+5В/802, 62=Земля/801, 60=+12В/803, 59=-12В/808** — definitive re-crop) and netted power for
all 84 chips: **GND=85, +5V=106, +12V=5, -12V=4 pads**. Details:
- **Rails are +5/+12/-12/GND** (no -5В row!): the 8080's pin-11 -5V is **board-derived from -12**
  (R19 470 + VD network, visible at X8) → `M5V_DERIVED` net = {D1.11} until passives land.
- **ROM sockets strap pins 1,26,27,28 to +5** (2764 VPP/NC/PGM high = read mode) — period detail.
- **АП2 serial drivers are ±12V parts** (+12=8, -12=5, GND=4); УП2: +5=15, GND=8; ЛА18: 8/4.
- **ИР16 = 74295-class DIP-14** (the table's «остальные ИС» 14/7 + owner's pin-8=G read → OC pin!).
- **8253s (24/12), РУ5 (8/16), DIP-16 74xx (16/8)**: datasheet (the table is silent on them).
- **D5 (8228) data pins fixed to the real datasheet interleave** (D0=19/DB0=18 … D7=8/DB7=7): its 10
  control pins were already scan-matched to the datasheet, validating the layout; frees pin 14=GND /
  28=VCC. (Was a documented straight-interleave placeholder.)
- Power nets carry `"power": true` → **excluded from LVS** (HDL has no power pins); filters in
  `netlist_from_board.py` + `gen_kicad_sch.py`. LVS unchanged: 86 instances IN SYNC; boot byte-identical.

## CONNECTORS real (2026-07) — X1 (СНП59-96) / X3 / X8 get pads; board fully routed
Owner's board photo gave the real connector types (**СНП59-96 Р-20-2-В**, **СНП59-30-23-В**), and X1's
edge codes decode as **32 columns × rows A/B/C = 96 = СНП59-96** (2.5 mm grid, DIN41612-style).
Generated parametric PTH footprints (Ø1.6/0.8): X1 full 96-pad grid (pad names = the schematic edge
codes), X3 serial (traced codes, provisional 2×8), X8 power (59-64) — power now terminates in
connector copper. X2/X9 stay outlines until their nets (PPI ports / keyboard) are traced. Geometry
provisional pending edge photos. Gotchas: hand-built footprints need real FPIDs (empty FPID → anonymous
DSN components → SES import fails); freerouting discards imported wiring (not fixed), but SES-import
puts the router copper ON TOP of the board's pre-routes → they coexist.
Routing: 4 D24→X1 links (-ADRC..F, cols 117/118) failed deterministically across runs → **pre-routed
escapes** laid on the empty board (collision-free by construction) in the generator; the router works
around them. +1 GND link hand-laid (D43.7→D42.7, empty B.Cu band, no vias). Final:
**1052/1052 connections, 0 electrical DRC violations** (silk cosmetics + lib-footprint nits remain).

## PASSIVES Stage 1 (2026-07) — 51 components netted + routed
Parallel/tap networks (LVS-invisible by the ≥2-mapped-endpoint rule — series parts in LVS nets like
R36/R37 in Φ1/Φ2 are DEFERRED, they'd split checked nets):
- **-5V derivation**: R19 470 (-12→) + VD5 zener → completes M5V_DERIVED to D1.11 [scan parts]
- **Reset network**: R3/R4/R20/C1/C21 + S1 (the front-bracket RESET button, per owner photo) → D13.5
- **Bulk caps** C31-C33 at X8; **video-mix** R38/R39 into NODE_A (R61/R90/R91/VT1/VD4 defer to D34 stage)
- **Decoupling C35-C72** (38, BOM count) on P5V/GND, chip-adjacent positions [assumed]
Full board now: **138 net-modeled footprints, 1152 connections, routed 100%, 0 electrical DRC**.

## Owner photos of BOARD #2 (ref/photos/juku-pcb-2/, git-lfs) — MAJOR finds
Second physical board, revision **7.102.158** (vs #1's 7.102.100 — explains its heavier ECO lacing):
1. **К155РЕ3 (8904) IS SOCKETED** (blue socket, top-center) → **the V3-gating timing PROM can be
   dumped!** Also **2× КР556РТ4А socketed** (mid-left) → decode-PROM contents dumpable.
2. **X2 = СНП59-30** (short blue, "СНП51-30-25 8903"); X1 = СНП59-96Р ✓ — connector set complete.
3. Front bracket: **RESET pushbutton (S1)** + **VIDEO BNC** + DB-style tape/serial connector.
4. This board: one ЛЕ4 missing, electrolytics cut (use board-#1 photo for caps). DRAM bank unpopulated.

## GERBER DRY-RUN (2026-07) — the fab package exports clean
`kicad/export_fab.sh` → 7 gerber layers (F/B copper, F/B mask, F/B silk, edge) + excellon drill from
the routed board. Sanity: ~1600 drill hits across sensible tool sizes (0.8 PTH pads / 0.3 vias / 3.5
mounting). The deliverable pipeline is proven end-to-end; remaining before a REAL order: the parked
power-trace widening, X2/X9 connector pads (nets untraced), bodge-ECO incorporation (triage ongoing),
and a final DFM review against the original's thick-power-trace style.
