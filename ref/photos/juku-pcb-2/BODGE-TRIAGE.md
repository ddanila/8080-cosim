# Bodge-wire triage — board #2 (rev 7.102.158)
Goal: every white ECO wire either (a) already in our schematic-derived netlist → our copper absorbs
it, no action; (b) NOT in the netlist → a post-schematic ECO → add to board.json `[photo-traced ECO]`
+ reroute; (c) legit assembly wiring (video coax, panel/bracket pigtails) → not copper.

## Classified so far
**Legit (class c):**
- Black coax w/ white sleeve: video out → BNC; board end at the К155АГ3 pair (video one-shots). ✓
- Top-edge white pigtail bundles: bracket connectors (X3/X4/X5/RESET/VIDEO) → board holes. ✓
- Bottom-edge sleeved link (clamped): power/video lead, single fat sleeve. ✓ (verify)

**ECO candidates (class a/b) — the laced harnesses (component side):**
- H1: 2-wire harness, upper board, runs left↔right past ВН59 (D10); one end at a via near mark "41",
  other toward the АГ3/video corner. Endpoints TBD (full-res crops).
- H2: 3-4-wire harness, mid-board; one drop solders at КР531ЛА1 (8702) pin [photo 7]; others run left
  into the DRAM field.
- H3: 5-6-wire harness, lower board; **≥3 drops solder directly onto КР531ИД7 (8906) pins**
  [photo 2, pin-readable]; further drops at К155ЛН5 (8904) + КР1533ЛА3 (8906) columns; harness
  continues left across the РУ5 row toward the CPU cluster.
- Several singles in the video/clock corner (К555ИР16 / КР531ИЕ17 / decapped-ЛЕ4 region).

## Region ↔ model correlation established (photo 2, bottom-right)
КР580ИР82 8910 = D58 ✓ · РУ5В ×8 (8904/8907) = D60-D67 bank 0 POPULATED ✓ (banks 1-3 empty ✓)
· ВВ55А 8907 = D26 ✓ · ВИ53 ×3 8905 = D54/D55/D57 ✓ · ВН59 8904 = D10 ✓ · КР531ИД7 8906 = D53?
(RAS/CAS decode — the harness-H3 target!) · КР531ИЕ17 8902 = D40's real part · К555ИР16 8902 =
D42/D43 family ✓ · 2× К555КП12 8812 near ВН59 = un-modeled (serial/tape outline block?)

## Notable: H3 targets the RAS/CAS decoder (ИД7) and H2/H1 run through the clock/video corner —
## consistent with DRAM-timing ECOs (the area our РЕ3-gated abstractions live in!). The РЕ3 dump +
## these wire traces together may fully reveal the real DRAM/video timing circuit.

## Method for pin-level endpoint reads (next passes)
Full-res crops (photos are 4000×3000) around each solder joint; wire-color/lacing continuity across
photos; cross-check against board #1 (rev 7.102.100, lighter ECO set) to split revision-specific
from universal. Owner multimeter continuity beats photos where wires vanish under lacing.

## Iteration 1 — H3 endpoint read at the ИД7 cluster (full-res crop, photo 2)
**Correction:** H3's wires do NOT solder to КР531ИД7 (D53) — they pass OVER it; the 4 visible wires
terminate at solder points on the chip ABOVE (the КР531ЛН1 = D33 region; its pin numbers are outside
this crop → next crop target). H3 is starting to look like a **clock-mesh ECO set** (D33/D53/D35
territory), consistent with fixes in the RAS/CAS-phase circuit.
**Region lock (this crop = our D53/D35/D57/D58 cluster):** КР531ИД7 8906 = D53 ✓; **К155ЛН5 8904 =
D35** (phase generator — real chip series К155, not К531 as our silk says → mark fix) ✓; ВИ53 = D57 ✓;
ИР82 top pins = D58 ✓. **Two factory test-pin posts marked "1"/"2" near D35 = Φ1/Φ2 clock test
points** (with a 5К1 R between); below: VT (dark flat-pack) + grey "В 8Р2" diode + R network = the
tape/video shaping stage (VT1/VD area of our passives backlog).

## Iteration 2 — the clock mesh photographed chip-by-chip (photo 2, upper crop)
Row-for-row match with our PLACE map: y=200 row = **КС531ЛА12(D36) | КР1533ЛА3(D37) | КР531ЛН1
8901(D33) | К555ИЕ10 57(D103)**; y=176 row = **КР531ЛА1 8702(D38)** + **КР1533ЛА3 8906(D39)**.
**The decapped ЛЕ4 sits BETWEEN D38 and D39** — a position empty in our model (the emaplaat had an
unreadable refdes label right there → that label is the ЛЕ4's refdes; next: re-crop the emaplaat at
(~265-290, 168-185) to read it). **Implication:** ЛЕ4 = quad NOR; cross-coupled NORs are the
canonical 8080 Φ1/Φ2 generator → the real phase generator likely includes this ЛЕ4, in exactly the
mesh region we abstracted (clk_phase). The РЕ3 dump + this chip's tracing = the full real clock.
Real-series corrections: D37/D39 are КР1533ЛА3 (1533, not 555). H3's lower wires terminate around
D37's bottom / D33's lower pins — exact pin numbers still need a tighter crop (next).

## Iteration 3 — the decapped chip is D92 (К155ЛЕ4), a chip absent from our model
The emaplaat label between D38/D39 reads **D92** clearly (crop ema_clkclu). Our DRAM banks end at
D91 → D92 is a real, separate refdes we never had (outlines jumped D91→D93). **D92 = К155ЛЕ4 quad
NOR at ~(270,176), inside the clock mesh** — cross-coupled NORs being the canonical 8080 two-phase
generator, D92 is the prime suspect for the REAL Φ1/Φ2 circuit our clk_phase abstracts. Added as a
placement outline; its nets are the top tracing target (photos + РЕ3 dump together = the full real
clock). Chip count: the populated board has ≥105 ICs (D92 + КП12×2 join the ~101 estimate).

## Iteration 4 — H3 endpoints pin-read: D37 pin 8 (spare section) + the FRAME INT corner
Tight crop (photo 2, D35/D57 region):
- **H3 wire #1 solders at D37 pin 8** — the OUTPUT of D37's spare ЛА3 section (pins 8/9/10 are
  unconnected in our netlist!). Classic factory-ECO pattern: route the fix through an unused gate.
  → H3 is **class (b): post-schematic ECO**, and its logic likely runs THROUGH D37's second section.
- **H3 wire #2** solders at the adjacent pad; its trace runs down the long vertical toward the
  test-post area.
- **Test posts "1"/"2" correction:** they sit on the **FRAME INT path** — D35 pin 8 → post → **R60
  5К1 (5.1k)** → toward D57 (ВИ53) — matching the schematic's "FRAME INT (1)" + R60 5,1к read
  (dram-video-timing.md), NOT Φ1/Φ2 as guessed in iteration 1. The VT + VD network below = the
  frame/video pulse shaping. **The factory ECO cluster is tuning the frame-interrupt/video timing —
  the exact circuit our sim treats as the `frame_tick` boundary.**
Remaining for H3: the far (left) ends across the РУ5 row; wire #2's destination; D37.9/10 (the spare
section's INPUTS) sources.

## Iteration 5 — CPU cluster read: D2 is really a РТ4 PROM; D13/D30 confirmed
Photo 10 (CPU area):
- **2× КР556РТ4А 8810, both socketed, beside the CPU** → **D2 (our io_dec138/74138 model) is REALLY
  the second К556РТ4 PROM** (BOM said РТ4 ×2 all along). The I/O decode is PROM-based → **contents
  dumpable** (like D6/РЕ3). Functional equivalence holds for the boot, but the real part + pinout
  needs a deliberate re-trace pass. MARK fixed via MARK_REF.
- **К155РЕ3 8904 socketed in the CPU cluster** (left of the РТ4 pair) — position located.
- **К555ТЛ2 8810 + КМ555ТМ2 8905** right of the CPU = **D13 (ТЛ2, the STSTB source) and D30 (ТМ2,
  ready) confirmed in silicon** — validates the STSTB reconciliation.
- D1 (ВМ80А 8902), D5 (ВК38 8905), 2× ВА86 8901 (D4+DLB, mounted horizontally SIDE-BY-SIDE above the
  CPU — our PLACE has D4 vertical; placement nuance to fix), К555КП14 8904 + К555ИЕ7 ×3 8908 groups ✓.
- Wires here: singles at the РЕ3 socket + РТ4 pin areas; the 3-wire harness (H2?) runs down between
  КП14 and ТМ2/ТЛ2 toward the crystal corner. Endpoint pin-reads = next.

## Iteration 6 — X1/X2-gap wire noted; power-widening interleave PARKED (WIP)
Photo 202047595 turned out to be the X1/X2 mounting closeup (not the crystal corner): one ECO single
solders to a top-edge pad in the X1-X2 gap (near the etched "17" / penned "11") — endpoint cataloged.
Interleave attempt (power-trace widening to match the original's thick runs): the widen→DRC→narrow
cycle stalls on a self-inconsistent DRC count (the script claims violations on a board that greps
clean); isolation confirmed the committed board is clean and pcbnew round-trips safely. Parked as
kicad/widen_power.py (WIP header documents the state); the right fix is geometric pre-checking
(nearest-copper distance) instead of DRC round-trips. Board left untouched (restored from git).
