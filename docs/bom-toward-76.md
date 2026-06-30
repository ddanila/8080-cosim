# BOM gap map — toward the real ~101-chip board

> **COUNT CORRECTION (was "76").** Summing the BOM line-item quantities (Всего column) on
> `ДГШ3.031.006` pp.3–4 gives **101 ICs** (page 3 = 37, page 4 = 64), of which **40 are memory**
> (565РУ3Г ×32 + К573РФ5 ×8) and **61 non-memory**. The PCB placement independently reached
> **102 positions** (matching within ±1 of the faint scan). So the real board carries **~101
> chips, not 76** — the earlier "76" looks like a subset (perhaps excluding the 32-chip DRAM array,
> or the analog К554СА3 / К170 drivers). Worth reconciling with the owner, but the BOM math is
> objective. The phrase "toward 76" below is retained only for history.

The component spec is `ДГШ3.031.006 ВП` (`~/fun/juku3000/docs/…nimekiri komponendid.pdf`, IC list
on pp.3–4). The LVS model (`hdl/juku_top.v` + `kicad/juku.board.json` + `sync/map.json`) currently
net-models **40**; the PCB additionally shows **62 placement-only outlines** (102 positions total).

**Why each addition is real work:** the component list gives type+count *totals*, but a chip
only enters LVS once its **pin-level nets** are traced from the schematic (processor module
`ДГШ5.109.006`, scans in `ref/schematics/` + `juku3000/docs/…protsessori moodul.pdf`). So
toward-76 is a per-cluster *tracing* grind (each like `docs/transcription/dram-video-timing.md`),
not a transcription of the BOM. PROM **contents** (РЕ3/РТ4) still need a dump, but their
**connectivity** can be added now (LVS checks wiring, not bits).

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
| 4 | **Bus / backplane** | **LOCATED** (sheet 1 right edge): D23 (addr→-ADR0-F), D24 (data→-DAT0-7), D25/D29 (control→-MRD/-PWR/-IORC/...), each T/E; types К170АП2/УП2 + ВА86/ВА87 | `bus-interface.md` (refdes pinned; per-bit wiring + connector model = Phase-B batch) | PCB BOM / expansion (needs connector X1/X2 modeled; no 1-node nets) |
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
