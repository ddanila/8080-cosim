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

## Iteration 3 — the decapped chip is D92 (К555ЛЕ4), a chip absent from our model
The emaplaat label between D38/D39 reads **D92** clearly (crop ema_clkclu). Our DRAM banks end at
D91 → D92 is a real, separate refdes we never had (outlines jumped D91→D93). **D92 = К555ЛЕ4 quad
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

## Iteration 8 — ROSETTA STONE: etched via numbers = schematic net numbers; H1 lands on net 11
Photo 7 full-res (АГ3/video corner):
- **H1 endpoint B solders to the via etched "11"** — and the board's etched numbers are the
  SCHEMATIC's net numbers (net 11 = D36.6 → D35.11 = **CLKG_D36**, the clock-phase-generator input,
  per clock-subsystem.md). H1 patches directly into the clock-phase path. Its other end sits near
  etch "41" → read that number next; if H1 = net41↔net11, the ECO bridges two schematic nets (class
  b, a real circuit delta). **Method upgrade: every numbered-via endpoint can be identified by
  READING THE NUMBER — no pin-guessing.**
- **The composite-video output stage in the flesh**: VT2 = **КТ315Г** (yellow, 8901), КД glass
  diodes, 1k/47Ω resistor network, coax braid+center landing, etch mark "Е". Real parts for the
  video-output passives (our node-A/VT2 backlog).
- Nearby: К555КП12 8812 (again — the un-modeled mux pair), К155АГ3 ×2 8901, КР531ИЕ17 8902.

## Iteration 9 — method recalibration: glue lash points ≠ endpoints
Full-res of the suspected "41" endpoint (right of ВН59/D10): it's an **adhesive lace point** (brown
glue blob over vias, verdigris around it) — the H1 wires pass THROUGH and continue left toward the
bus band. The low-res "endpoint at 41" was a misread of this lash. **Rule: only shiny solder cones
on pads/vias count as endpoints; brown blobs are glue lacing.** This shrinks the true-endpoint count
substantially (many harness "stops" are lash points). H1-endpoint-A hunt continues left of ВН59.

## Iteration 10 — serial/FDC corner: D93=ВГ93 confirmed, РЕ3 #1 located, serial placement validated
Photo 6 (top-center bracket zone):
- **КР1818ВГ93 8905 = D93 confirmed** (WD1793-clone FDC; refdes matches ВГ93; position matches our
  outline). Above it a **5th ВА87 (8804)** = the FDC bus buffer (likely D97). The FDD subsystem is
  real on-board silicon (our fdc_1793 stub's physical counterpart).
- **К155РЕ3 8904 #1 in its blue socket** at this corner (D28-position candidate); the CPU-cluster
  РЕ3 (iter 5) is #2 — matching the BOM's РЕ3 ×2, both socketed/dumpable.
- **Serial cluster placement VALIDATED**: К170АП2 ×2 (8810) + К170УП2 (8923) + КР580ВВ51А (8906)
  arranged exactly per our PLACE (D32/D14/D104/D11). Bracket hardware: СР-50 BNC + RESET switch.
- More un-modeled glue cataloged: К561ЛН2 8904, К155ЛА18 8801, К555КП12 ×2 8812, К155ЛН3(?) 8904,
  КМ53 47µ/6.3V electrolytic (survivor).
- H1's left run rises toward ВВ51А/УП2 — candidate solder cone left of ВВ51А (one more crop to
  confirm as H1-endpoint-A).

## Iteration 11 — ЛА18 = DIP-8 confirmed; H1-A continues below frame
- **К155ЛА18 8801 = DIP-8** (clear view) — consistent with the power table (8/4) and our D12 model.
- **АП2 pinout question**: the АП2 body looks compact (8-pin-ish) but the schematic explicitly uses
  pin 11 for D3's section → keeping DIP-14; verify from a better angle later. (Our АП2 section pins
  are marked [assumed] already.)
- **РЕ3 #1 appears loosely seated** in its blue socket — trivial to pull for dumping.
- H1-A: the wire rounds ЛА18 and exits the frame bottom — endpoint one crop lower (next).

## Iteration 12 — endpoint at the D11 serial-shaping network; endpoint-pairing caveat
Photo 6, below ЛА18/К561ЛН2: a wire from the УП2/АП2 direction **solders at the pad of the 33К
serial-level resistor beside ВВ51А (D11)** — the R18/R30-class serial output shaping from the
schematic (img #2). A second long wire runs right toward ВГ93 (D93) — endpoint off-frame.
**Endpoint catalog now (solid solder joints):**
1. D37 pin 8 (spare ЛА3 section output) [iter 4]
2. adjacent pad, trace toward the frame-int test posts [iter 4]
3. etched-net-11 via = CLKG_D36 [iter 8]
4. X1/X2-gap top-edge pad [iter 6]
5. 33К serial-shaping pad at D11 [iter 12]
6. (toward D93/ВГ93 — off-frame, pending)
**Caveat:** pairing endpoints into complete wires is at the photo-precision limit (runs vanish under
lacing between shots). The efficient close-out is OWNER MULTIMETER CONTINUITY between the cataloged
points (~15 checks: each endpoint against the other five). Photos got us from "30 mystery wires" to
"6 numbered test points" — the last hop is a beeper session.

## Iteration 14 — АП2 = DIP-8 (definitive) → D3 is К561ЛН2, model corrected
Max-zoom pin count: **К170АП2 = DIP-8** (4 pins/side, both chips), **К170УП2 = DIP-14**. This cracks
a misID chain: the power table's АП2 pins (8/5/4) fit 8-pin ✓; D14/D32's traced sections (3→6, 2→7)
fit ✓; but the schematic's "D3: 11→10" section CANNOT be an 8-pin АП2 → **D3 = К561ЛН2** (14-pin hex
inverter, pins 11/10; TTL SOUT = ~TxD; the schematic symbol was ЛН2 misread as АП2). Model fixed:
ap2_drv → true DIP-8 dual (phantom sections dropped), D3 → ln2_inv (CMOS: VCC=14/GND=7 power fix),
DIP-8 footprints mapped. LVS 86 IN SYNC, boot byte-identical, board regenerates clean.

## Iteration 15 — orientation correction: D37/D33 are notch-DOWN; H3 feeds D37 gate-1 INPUTS
Max-zoom of D37 (КР1533ЛА3 8906) + D33 (КР531ЛН1 8901): **both mounted notch-DOWN** → the
bottom-right pin = pin 1, not pin 8. Corrects iteration 4: **H3's two wires solder at D37's spare
gate-1 INPUT pins (1 and the pad by 2)** — the ECO injects signals INTO the unused gate; the gate's
output (pin 3) leaves on existing copper (trace it on the solder-side photo to find what the ECO
drives). Same class-(b) conclusion, cleaner mechanism.
**New fidelity item: CHIP ORIENTATION PASS** — the real board mixes notch-up/notch-down mounting;
our footprints assume notch-up everywhere. The emaplaat outlines carry the key marks (semicircles) →
read per-chip orientation and set footprint rotations accordingly (matters for real assembly).

## Iteration 16 — solder side carries etched numbers too; registration overlay needed
The solder-side crop at the (mirrored) clock cluster shows etched digits ("1 2", "7 14", "9", "10",
"12") — pin-1/power-pin assembly aids + net numbers on the copper side as well. Following D37 pin 3's
etch (the H3-ECO output) is feasible BUT identifying the right pad pattern in the mirrored view needs
registration better than ±10mm. **Next tool: an overlay** — mirror+scale our board render onto the
solder photo (anchors: the corner mounting hole, the DRAM-field edge, the thick power buses). That
also doubles as the first step toward photo-guided routing comparison. Parked as the next interleave.

## Iteration 17 — overlay tool built; first render-vs-real-copper comparison
`kicad/overlay_photo.py`: mirrors our B.Cu render and affine-warps it onto the solder photo via 3
board-corner anchors (v2 anchors: 585,299 / 3758,295 / 594,3020 for PXL_..202031273). Registration
~2-5mm center (perspective residual at edges — local anchors per region when pin-level work needs it).
First findings from the comparison: the REAL board's solder side favors HORIZONTAL runs where our
freerouting chose vertical (opposite layer discipline!) — relevant if we ever do photo-guided routing;
pad-grid alignment is good enough for region navigation (D37 pad hunt now feasible with a local anchor).

## Iteration 18 — solder-side etch digits located in the clock zone; local anchors defined
Affine-computed crop at D37's mirrored position found the zone's etched assembly digits: a "14 7"
pair (power pins of a DIP-14 ≈ board (248,188) → D38 or D36) and a "1 2" pair (pin-1 mark ≈ board
(254,214) → D36 or D53). Local registration residual ≈10mm (y) in this zone — too coarse to name
D37's pin-3 pad honestly. **Overlay v3 plan: use these etch-digit marks as LOCAL anchors** (once
their chips are pinned by one cross-check), giving ~1mm local registration for the pin-level trace.
Alternative close-out remains the owner's continuity check. Also re-confirmed: real solder side =
long horizontal bus runs (flipped discipline vs our route).

## Iteration 20 — tape/serial cluster physical IDs (the D94-D102 outline zone)
Consolidating photo 6/7 reads: the un-modeled outline zone right of D93 (board ~x 225-310, y 40-120)
physically contains: **К555КП12 ×2 (8812)** (dual 4:1 muxes — tape/serial data steering), **К155АГ3
×2 (8901)** *in addition to* the video D56 (so the BOM's АГ3 ×2-3 = D56 + this tape pair — tape pulse
shaping one-shots), КР580ВА87 (8804) = the FDC bus buffer (D97 candidate), К561ЛН2/К155ЛА18 CMOS/OC
glue, К555ИЕ7 ×3 (8908) more counters, ИР9/ИЕ11/ИМ1 (from the earlier sheet-3 reads) = the tape
(МАГ) modem chain. **This whole cluster = the sheet-3 tape subsystem** — its schematic tracing is a
self-contained future pass (the sheet-3 regions we surveyed: ИР9 shifters D89/D99/D100, ИЕ11 baud
counter D108, ЛА7 glue D206/D400 ... plus these). Not boot-relevant (tape I/O), pure completeness.

## Iteration 21 — H2 endpoint at D38 (the STB gate); D38 mounts dot-UP
Pin-level crop (photo 7): **D38 = КР531ЛА1 8702** with an H2 wire soldered into the via immediately
right of its pin column (pins 3-5 zone) + a second wire ending at a pad lower-left. The ECO set now
touches: D37's spare gate (H3), net 11/CLKG_D36 (H1), the frame-int corner, and D38's STB region
(H2) — **every ECO lands in the clock/timing circuit**. D38's pin-1 DOT is at its TOP (dot-up),
unlike notch-down D36/D37/D33 → orientation truly per-chip (sweep required). The 330R/910R pair
right of D38 = the D35-area video divider (R35 330 + 910) from the schematic.
Endpoint catalog grows to 8 solid points. DB5/DB6 router casualties pre-routed in the generator
(deterministic freerouting confirmed: identical results across "re-rolls").

## THE MULTIMETER SESSION SHEET (closes the triage — ~20 min with a beeper)
The 8 cataloged solder endpoints, with board-frame coordinates (component side, X1 top-left):
| # | Point | Where (mm) | Landmark |
|---|-------|-----------|----------|
| E1 | D37 gate-1 input (pin 1) | (268, 208) | КР1533ЛА3 8906, notch-down, bottom-right pin |
| E2 | pad beside E1 (pin-2 side) | (268, 206) | same chip, next pad |
| E3 | via etched "11" = net CLKG_D36 | ~(263, 145)? | right of К555КП12 pair, etched digit 11 |
| E4 | X1/X2-gap top-edge pad | ~(112, 27) | between the blue connectors, near etch "17" |
| E5 | 33К pad at D11's right | ~(212, 95) | serial-shaping resistor by ВВ51А |
| E6 | wire toward D93/ВГ93 | off-frame right of E5 | follow the long wire from E5's photo |
| E7 | via right of D38 pins 3-5 | (256, 174) | КР531ЛА1 8702, dot-up, right column |
| E8 | pad lower-left of D38 | (247, 180) | same photo, stripped wire end |
Also: the frame-int test posts "1"/"2" at D35 (≈(262,228)) and D37 pin 3 (the spare gate's output,
(268, 205) third-from-bottom right) — probe these against E1-E8 too.
**Protocol:** continuity-beep each Ex against every other + against D37.3 + posts 1/2 (~40 quick
touches). Record pairs → each confirmed pair = one complete ECO wire → I diff against board.json
and either absorb (already-in-netlist) or add as `[photo-traced ECO]` + reroute.

## ECO hypothesis (to test with the dump + beeper)
All four touchpoints live in the clock/timing circuit. Most plausible story: the factory re-derived
a timing qualification — e.g. the FRAME INT (or a DRAM refresh/slot strobe) needed gating against a
mesh phase that the etched revision lacked: signal(s) → D37 spare NAND (E1/E2 in) → pin 3 out →
via etch to the frame-int/STB region (E7/posts). The РЕ3 dump + continuity pairs decide.

## Iteration 23 — orientation sweep: the big blocks are key-UP (no change needed)
Emaplaat key-mark reads: **DRAM array rows = notch-UP** (row-2 semicircles clearly at top; array
uniform), **ROM sockets D15-D22 = key-UP** (socket key bars at the top edge). So the 40 memory
positions match our existing notch-up footprints ✓. Confirmed exceptions so far: D36/D37/D33
notch-DOWN (fixed), D38 dot-UP, D92 up. Bonus: the drawing places the decoupling caps BETWEEN the
DRAM rows — matching our chip-adjacent cap placement. Remaining sweep: the logic rows + bus band
(~35 chips), mechanical per-crop reads when needed.

## Iteration 26 — CPU-cluster reverse angle: D52=К155ЛА3; КП14 series mix; РК-171 position
Photo 4 (right-edge frame = board x 0-165): **D52 = К155ЛА3 8905** (the ТМ2/ТЛ2/ЛА3 trio matches
D30/D13/D52's drawing positions) → converted to an untraced footprint. **The КП14 population is
mixed-series: КР531КП14 ×3 (8808/8809) + К555КП14 ×1 (8904)** — the S-series sits in the video/DRAM
address path (which of D48-D51 has the К555 one = TBD; marks left as-is until pinned). Also visible:
a possible КР531ЛИ1(?) 8809 (a type we don't model), РЕ3 #2 + РТ4 ×2 socketed (again), and the
**РК-171 8903 crystal + trimmer at the D59 corner** ("Д1" ink stamp, "05-9-6(1)") — Z1's physical
spot for the future crystal footprint (passives stage 2).

## Iteration 27 — right-edge electrolytic values read (passives ledger)
Full-board photo right edge: **К53-series tantalum/oxide cans: 47µF/6.3V (+22µF/16V nearby, К53-18В
0.22µ?/...)** — these are the "cut caps" survivors on board #2's edge; values feed the passives
ledger for stage 2 (bulk/rail caps beyond C31-C33). Baud-row chip ID attempt missed (photo-1 frame
calibration off — the baud row needs a re-crop next pass).

## Iteration 28 — right-side region mapped: КП12 ×2 LOCATED, D106=К155АГ3, 4-row grid
The re-crop (native +2650+620 / +1080, the "baud row" calibration fix) resolves the whole
right-side glue region into four chip rows (model-frame mm, ±4):
- **y≈70**: К555ИЕ7 (~x257, 8908), ?555ЛН5? (~x273, behind the video cable), КМ555ТМ2 (~x285, 8905)
- **y≈89**: **К555КП12 (~x253, 8912)** + two chips hidden behind the cable (~x274, ~x285)
- **y≈105**: **К555КП12 #2 (~x245)**, К155АГ3 (~x270, 8901), **К155АГ3 = D106 (~x297, 8901,
  label-down)** — lands exactly in the D106 outline → converted to an untraced footprint (rot 180)
- **y≈127**: КР531/К555ИЕ17 (~x256) — CT16 counter territory
So: both un-modeled **К555КП12 muxes are now physically located** (nets still untraced); a SECOND
АГ3 exists at ~(270,105) — candidates for its refdes: D100 (TBD in this exact region) or a
D56 relocation (D56=АГ3 is net-modeled at (302,200), but the photo shows ИЕ10+ЛУ? there, not АГ3 —
suspicious, needs the drawing re-read before touching a net-modeled chip). D101/D102 outlines
(y=82) sit between photo rows 70/89 — held as outlines until an etch-refdes read pins them.
**New endpoint E9**: a white lacing wire crosses the y≈89 КП12 and terminates at a solder cone
~(240.5, 101.4) just NW of it — log for the multimeter session (likely legit video/socket lacing,
but it now has a coordinates entry).
Board-frame note: photo x reads ~4 mm left of model coords on the right half (perspective);
y-rows 55/70/89/105/127 vs model boxes 55/82/108 — the 82-row assignment was the earlier miss.

## Iteration 29 — endpoint 6 RESOLVED at ВГ93's corner via; D107 = 2nd ВА86 (user call)
Photo 6 full-res, the wire-run band between ВН59 (D10) and ВГ93 (D93):
- **Endpoint E10 (= the pending "endpoint 6")**: the long wire from the D11 33К-pad zone runs right
  and terminates on a via at **~(235, 116) mm, just SW of ВГ93's bottom-left pin corner** — the
  joint is a DULL/oxidized solder blob (matte gray), not a shiny cone; medium confidence, flag for
  the beeper list. No etch number visible at the via. A wire into the FDC corner + a wire into the
  serial shaping (E5) smells like the H1 harness is SERIAL/FDC plumbing (class c: legit wiring),
  not a clock ECO — unlike H3.
- The **К555КП12 pair (both 8812)** shows again right in this band (~x 235-253, y 110-125),
  cross-checking iteration 28's position fix.
- The lower wire of the band passes a brown GLUE LASH (verdigris, center) and bends south around
  the КП12 — off-frame; its endpoint is on the next crop down (bottom-right quadrant).
- **D107 resolved = КР580ВА86** (converted to an untraced footprint at (57,185)): the angled CPU
  photo (201940304) shows TWO stacked ВА86 8901 — D4 is one, and the D107 outline sits exactly
  below D4. Credit: owner's "same bus one as one next to it" nudge.

## Iteration 30 — H3 junction crop: D36/D37/D53 placement triple-confirmed; endpoints E11/E12
Photo 7 full-res at the harness junction (the big verdigris'd lash, board ~(245,195)):
- **Placement triple-check ✓**: КС531ЛА12 8905 = D36, КР1533ЛА3 8906 = D37 (right of it),
  К531ИД7 8906 = D53 (below) — all three exactly at PLACE's (253,200)/(265,200)/(253,225).
- **E11: solder-cone via at ~(249,185)** — a harness wire rises from the lash and terminates on a
  via in the mesh channel ABOVE D36 (between the D40/D41 divider row and D36). No etch digits
  legible at this angle; a solder-side read may give the net number (Rosetta method).
- **E12 (candidate, low-med confidence): joint at D36's bottom-left pin** — green flux residue +
  metallic blob at the ЛА12's bottom-left pin (= pin 7 = GND given the row's notch-DOWN mounting).
  If real, likely a harness GROUND stitch, which would fit an ECO carrying a clock-quality signal
  (twisted/grounded return). Verify by beeper (E12 ↔ GND).
- The photo-6 "lower wire" (iter 29) merges into THIS harness at the lash → H3 and the serial/FDC
  band wires are one laced tree; only per-endpoint continuity separates the circuits. Beeper list
  now E1-E12.

## Iteration 31 — owner IDs: D9 = К555ИД7; D7's real series is КР1533ЛА3
- **D9 = К555ИД7** (owner) → untraced DIP-16 footprint at the bus-band slot (122,136). Note the
  architectural hint: D2's schematic role is the IO decoder (74138-class) but the physical D2 is a
  socketed РТ4 PROM — a SECOND ИД7 right in the bus band is a strong candidate for where the real
  138-style decode lives. When D9's nets get traced, compare against our IO_DEC138 model netlist.
- **D7 = КР1533ЛА3 on the real board** (owner), not К555ЛА3 as assumed. Logic + pinout identical
  (ALS vs LS: faster edges, ~1/3 the power); electrically drop-in for the recreation, so only the
  silk MARK changes. Pattern now: ALL three ЛА3s outside the CPU cluster (D7/D37/D39) are 1533 on
  board #2 — consistent with a late-80s production run preferring ALS.

## Iteration 32 — owner ID batch: D105/D41 converted; D98/D96 flipped horizontal
- **D105 = К155ЛА3** (owner) → untraced footprint at (30,240), lower-left column.
- **D41 = К555ИР16** (owner; photo confirms 8902, DIP-16, label-down) → untraced footprint at
  (255,155) next to D40 — matches the survey's earlier "К555ИР16 8902 in the clock corner" sighting.
  First placement (252) clashed with D60's DRAM pads; 255 clears it.
- **D98/D96 orientation: HORIZONTAL per the real photo** (owner call). Bonus finding from the corner
  crops: the top-right corner at (290+, <50) is the bracket NOTCH (RESET/ОТК switch sits in it), so
  the drawing-derived vertical boxes at y42-68 physically can't be right. Exact centers still need a
  clean corner crop; boxes provisionally at (293,55)/(298,65).
- Top-band reality check (photo 6, reliable frame): D28 РЕ3 (225,56) ✓, D97 ВА87 8804 (247,52) ✓,
  vertical trio at x≈258/272/285 y≈57-80 (ИЕ7 / ЛН3-or-ЛП1 / ТМ2 reads) — candidates for
  D95/D94/D98 or D102/D101; etch "18" near (285,40). One clean zoom of the (272,70) chip decides.
- Route v18: 1151/1151, 0 unconnected, 0 electrical DRC (PHI1 healed by the re-route; v15's
  finishing-pass experiment on an already-routed DSN did NOT complete the link — full re-route did).

## Iteration 33 — D94/D95 zone is ONE horizontal К155ЛП11; E13 = RESET-switch wire landing
Clean zoom of the (272,70) mystery chip (photo 6, the one behind photo-1's video cable):
- **К155ЛП11 8904, HORIZONTAL, spanning ~(258-276, 64-70)** — one chip, not the "vertical trio"
  members I split it into (the black cable bisected it in photo-1; the earlier ЛП1/ЛН3/ЛН5 partial
  reads were all of THIS die). It covers BOTH the D95(263) and D94(277) box centers → the drawing's
  two vertical outlines there are wrong; one of {D94,D95} is this ЛП11 (refdes pending an etch
  read), the other lives elsewhere in the band. Boxes left as-is until pinned.
- **E13: solder cone at the ЛП11's bottom-right pin (~274.5, 71.6)** — the white wire descending
  from the RESET/ОТК bracket switch (seen rounding the corner notch in the d98d96 crop) lands here.
  Bottom-right pin of a label-upright horizontal DIP-16 = **pin 8 = GND**... OR the joint is on the
  adjacent via. **Etched net number "18" sits right beside it** — first direct etch-number-at-
  endpoint since the net-11 Rosetta hit. Net 18's schematic name is unmapped so far (RESET's etched
  number is a prime candidate — the wire IS the panel switch's drop). Classification: **legit
  wiring** (panel-mounted S1 must reach the PCB by wire), pin-level confirmed.
- Net-18 lookup is the next Rosetta target: read the solder-side etch run from this via, or find
  "18" on the schematic sheet-1 reset network (R3/C21/S1).

## Iteration 34 — H2 correction: the wires at D38 are CUT ends, not solder drops
Photo 7 full-res at D38 (КР531ЛА1 8702, dot-UP ✓ matches the model orientation):
- The earlier low-res claim "H2 drop solders at КР531ЛА1 pin" is WRONG at pin level: the two white
  wires near D38 are **dangling CUT ends** — bare snipped conductor hovering over open board at
  **~(249,172)** and **~(249,186)**, no pad/via beneath the tips. A third end at **~(266,172)**
  (between D38 and the D40/D41 divider pair) does look tinned and sits AT a via — possible real
  endpoint E14 (medium confidence).
- Implication: part of the H2 harness was **snipped** at some point (board decommissioning, or an
  ECO that was UNDONE by cutting rather than unsoldering — same treatment as the desoldered ЛЕ4?).
  The cut ends cannot be beeped to anything; the multimeter list stays E1-E14 with E14 flagged.
- H2's classification shifts from "ECO drop into the clock gate" toward **(possibly reverted)
  patch** — the surviving H2 conductor path needs its OTHER end (left run across the bus band, per
  iteration 9) read before any netlist action. No model change.

## Iteration 35 — H1-A RESOLVED: left-edge via at (9,111); the H1 bridge is board-length
Photo 201933909 (mid-board frame x 0-170) full-res at the left edge:
- **E15 = H1-A: shiny solder joint on a via at ~(9, 111)** — left edge, below the D15 ROM socket,
  on a VERTICAL etched trace. The wire leaves right, passes a **1К0 resistor pair** at the D2 (РТ4А
  8810 socketed ✓) corner, and continues toward ВН59/the bus band = precisely the iteration-9
  trail ("H1 continues left of ВН59"). CPU-cluster placement double-check: D4 = КР580ВА86 8901
  vertical ✓ next to the socket.
- **H1 now reads end-to-end: net-11 via (CLKG_D36, clock-phase) ↔ left-edge via (9,111)** — a
  board-length bridge. The (9,111) vertical trace heads toward the X1 expansion-edge zone; if the
  solder-side read confirms it reaches an X1 pad, the ECO exports/imports a clock phase on the
  expansion bus (diagnostic clock injection? external sync?). Next Rosetta: the via's etch number
  on the solder side; also whether the 1К0 pair is IN the wire's circuit (series terminator?) or
  coincidental neighbors.
- Beeper list: E1-E15. АП2 queue item note: pinout verification CLOSED back in iter 14 (DIP-8
  definitive) — removing it from the standing queue.

### Iteration 35b — solder-side check at (9,111): power-rail neighborhood, via ID pending
The solder side around H1-A's zone (mirrored crop at the left edge) shows the **edge power-rail
strip** (wide tinned run along the board edge) with several solder-wicked power traces teeing into
it, plus normal signal traces ending in vias. At ±5mm registration the specific (9,111) via can't
be singled out from this shot. Open question it raises: if H1-A's via sits on one of the TINNED
(power) traces, H1 is a clock-phase SHIELD/ground wire rather than a signal bridge — which would
downgrade H1 from "class b ECO" to "legit wiring". Resolution: overlay-v3 local anchors on this
corner, or beeper E15↔GND / E15↔E3(net-11).
