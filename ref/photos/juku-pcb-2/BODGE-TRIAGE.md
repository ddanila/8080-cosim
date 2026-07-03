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

## Iteration 36 — E15 coordinate RETRACTION + photo-201933909 tilt calibration
Anchor recalibration of photo 201933909 (using model-validated D10/ВН59 and D27/ВВ55А positions)
shows the frame is HEAVILY tilted: constant-px/mm mapping breaks across it. Consequences:
- The socketed РТ4А near the wire run maps to **x≈86 = D2's model slot ✓** (so the MODEL's CPU
  cluster is fine — it was my photo mm-mapping that was off, not PLACE).
- **E15's "(9,111)" is RETRACTED**: depending on where the scale is trusted, the H1-A via lands
  anywhere in x 9-56, y 111-173 (board-edge zone vs CPU-cluster corner — materially different
  stories: X1-expansion tap vs CPU-area signal). The SEMANTIC read stands: shiny solder joint on a
  via, wire exits right past the D2 socket + 1К0 pair toward ВН59. Position needs overlay-v3 local
  anchors or the left-half straight-on photo (photo 4) before the beeper sheet is printed.
- Lesson (add to method rules): **absolute mm from tilted frames only via ≥2 model-validated chip
  anchors bracketing the target**; single-anchor + global px/mm is what produced the bad (9,111).
- Bonus reads from the corridor crop: К555ЛА1 (label-down, 89xx) right of the РЕ3 #2 socket — an
  un-modeled type sighting; another КР531КП14 8808 below it (series-mix census grows).

## Iteration 37 — E15 recovered by bracketing: ~(40,143), right below D5/ВК38
Applying iteration-36's own method rule: the two РТ4А sockets in frame are model-known anchors
(D6 = horizontal РТ4 at (68,136); D2 = vertical РТ4 at (83,158) — labels' orientation
disambiguates them, and this also explains the "РТ4 ×2" as D6+D2, both DEC_PROM/КР556РТ4 class).
Local px/mm comes out x=15.1 / y=23.5 (the tilt is real), and the H1-A via lands at
**E15 ≈ (40, 143) — 3 mm below the bottom pin row of D5 (КР580ВК38 system controller)**.
Revised H1 hypothesis: **net-11 (CLKG_D36 clock phase) wired to the ВК38 pin zone** — a
strobe/timing qualification ECO at the system controller (STSTB-class fix), far more coherent than
the retracted "X1-edge tap". Class (b) post-schematic ECO, pending: which D5 pin/via exactly
(solder-side or beeper E15↔D5.x), and whether the 1К0 pair beside the run is in-circuit.
Beeper priorities now: E15↔D5 pins, E15↔E3(net-11), E12↔GND, E1/E2 (D37 inputs) ↔ everything.

## Iteration 38 — D37's spare-gate SOURCES found: Φ2 taps at D35 pin 14; the ECO story closes
Component-side full-res at D35 (К155ЛН5 8904, **vertical notch-UP ✓** — model orientation correct;
the solder-side "horizontal DIP-16" inference from the previous crop was anchor-less misregistration,
discard it):
- **E16/E17: TWO wire drops solder at D35's pin-14 corner (~(268,213)/(270,214))** — and per
  docs/transcription/clock-subsystem.md, **D35 pin 14 is the Φ2 output** (pin 12 → R36 360Ω → 14).
  The H3 harness taps the CPU's Φ2 clock phase right at the phase generator.
- **E18: solder cone on a via etched "2", SE of D35 (~(272,222))** — Rosetta hypothesis: net "2" =
  the Φ2 net itself (Φ1/Φ2 as schematic nets 1/2; net 11 = CLKG_D36 already proven). If so, E18 is
  a second Φ2-family tap point.
- Solder side of this zone shows several BULBOUS hand-soldered cones (non-factory profile) — the
  ECO's through-joints seen from the back; exact pad IDs deferred (needs bracketed anchors).
- **ECO narrative now closes end-to-end**: Φ2 tapped at D35.14 (E16/E17, possibly + net-2 via E18)
  → D37 spare NAND gate-1 inputs (E1/E2 at pins 1/2, iter 15) → gate output pin 3 → existing copper
  toward the frame-int/STB corner (E7, iter 4) — i.e., a **Φ2-qualified strobe/interrupt fix**:
  class (b) post-schematic ECO. Remaining to prove: beeper E16↔E1 (or E2), and D37.3's copper
  destination (solder-side trace with proper anchors).
No netlist change (the ECO is documented, not yet incorporated); LVS/boot untouched.

## Iteration 39 — ВГ93 quadrant rebuilt per owner's layout; ZERO placeholders left
Owner supplied the authoritative 4-row layout around D93/ВГ93 (connectors up, L-to-R, T-to-B):
row 1 horiz: РЕ3, ВА87, ЛП11 · row 2 vert: ИЕ7, ЛН3, ТМ3[ТМ2 per label] · row 3 horiz: КП12,
АП3[АГ3 assumed — behind cable, VERIFY] · row 4 horiz: КП12, АГ3, АГ3. Implemented, reconciled
with the per-chip crops + D93's own footprint envelope (rows 3 starts right of D93's pin field;
row 4 drops below it, y=124, matching the h1a_run КП12 read at ~(242,120)):
- D28=РЕ3 ✓, D97=ВА87 ✓ (already placed) · **D95=ЛП11 (268,52)** · **D94=ИЕ7 (262,70)** ·
  **D102=ЛН3 (272,70)** · **D101=ТМ2 (284,70)** · **D98=КП12#1 (268,89)** · **D96=АГ3? (288.5,89)**
  · **D100=КП12#2 (243,124)** · **D56 RELOCATED (302,200)→(268,124)** (photo shows ИЕ10+ЛУ? at the
  drawn spot, not АГ3) · D106=АГ3 (295,124).
- **All refdes PROVISIONAL** (nearest drawing-box; owner warns the drawing's layout differs here).
  Etch reads settle them. Types/positions/orientations are photo-grade.
- **D99 (К561ИР9) relocated (296,82)→(302,200)**: the quadrant rows exclude ИР9; the un-IDed
  "К5xx…/1068" chip at the old D56 slot is the best ИР9 candidate [verify]. tape-serial.md's
  ИЕ11/ИМ1/ИР9 baud-chain prediction did NOT materialize in this quadrant — sheet-3 re-read queued.
- **The un-modeled К555КП12 pair is now PLACED (D98/D100)** — queue item closed at placement level
  (nets still untraced).
- Board: **0 placement outlines remain** — all 160 positions are real footprints.

## Iteration 40 — BEEPER SESSION SHEET v2 (supersedes the E1-E8 sheet above)
All 18 endpoints consolidated; coordinates are component-side board-frame mm (X1 top-left).
Confidence: ● solid solder cone read · ◐ medium (dull joint / tinned end) · ✗ retracted/cut.
| # | Point | Where (mm) | Landmark / note |
|---|-------|-----------|------------------|
| E1 ● | D37 spare-gate input pin 1 | (268,208) | КР1533ЛА3 8906, notch-DOWN, bottom-right |
| E2 ● | pad beside E1 (pin 2 side) | (268,206) | same chip |
| E3 ● | via etched "11" = CLKG_D36 | ~(263,145) | the Rosetta via |
| E4 ● | X1/X2-gap top-edge pad | ~(112,27) | near etch "17" |
| E5 ● | 33К pad at D11 | ~(212,95) | serial shaping by ВВ51А |
| E6→E10 | (superseded by E10) | — | iter 12's "toward ВГ93" resolved |
| E7 ● | via right of D38 pins 3-5 | (256,174) | frame-int corner |
| E8 ◐ | pad lower-left of D38 | (247,180) | stripped wire end |
| E9 ◐ | cone NW of КП12/D98 | ~(240,101) | white lacing wire (likely legit video/socket) |
| E10 ◐ | via SW of ВГ93 pin-20 corner | ~(235,116) | DULL oxidized joint; wire from E5 direction |
| E11 ● | via above D36 (mesh channel) | ~(249,185) | harness riser from the big lash |
| E12 ◐ | D36 bottom-left pin (=pin 7 GND?) | ~(250,207) | green flux; harness GROUND stitch? |
| E13 ● | ЛП11/D95 bottom-right pin zone | ~(274,72) | RESET-switch wire landing; etch "18" beside |
| E14 ◐ | tinned end on via, D38-D40 gap | ~(266,172) | rest of H2 is CUT (✗ ends at (249,172)/(249,186)) |
| E15 ◐ | via below D5/ВК38 bottom row | ~(40,143) | H1-A (bracketed-anchor position) |
| E16 ● | D35 pin-14 corner drop #1 | ~(268,213) | Φ2 output corner (К155ЛН5) |
| E17 ● | D35 pin-14 corner drop #2 | ~(270,214) | second drop, adjacent via |
| E18 ● | cone on via etched "2" SE of D35 | ~(272,222) | net "2" = Φ2? (Rosetta hypothesis) |
**Priority pairs (expected story, ~25 touches):**
1. E16/E17 ↔ E1/E2 — Φ2 into the spare NAND inputs (the core ECO claim)
2. D37 pin 3 (268,205) ↔ E7 — spare-gate output into the frame-int corner
3. E15 ↔ E3 — the H1 board-length bridge; then E15 ↔ D5 pins (which ВК38 signal?)
4. E12 ↔ GND, E15 ↔ GND — shield-vs-signal disambiguation
5. E18 ↔ D35.14/E16 — net-2 = Φ2 confirmation
6. E13 ↔ S1/RESET network (R3/C21 zone ~(23-67,214)) — legit-wiring confirmation
7. E5 ↔ E10 — the serial/FDC band wire (legit wiring hypothesis)
Every confirmed pair = one complete wire → diff vs board.json → absorb / add `[photo-traced ECO]`
behind LVS / mark legit. РЕ3/РТ4/2764 dumps (docs/prom-dump-procedure.md) close the rest.

## Iteration 41 — CORRECTION: D35.14 is VCC, not Φ2; the Φ2 tap is E18 (net-2 via)
Cross-check against board.json (LVS-verified, the source of truth) while closing the ЛА18/ЛН2
queue item: **D35 pins are Φ1=10, Φ2=12, OSC=11, Φ2TTL=13, GND=7, VCC=14**. Iteration 38 misread
the transcription's "(pin 12 → R36 360 → pin 14)" — pin 14 is +5V, so:
- **E16/E17 (drops at D35's pin-14 corner) are most likely +5V pickups** (ECO pull-up/supply
  stitches), not phase taps. Beep them against P5V first.
- **E18 (cone on via etched "2", ~(272,222)) becomes the Φ2 tap candidate** — and geometry backs
  it: the Φ2 copper (D35.12 → D53.3 at (253,225)) passes exactly through that zone, and "2" as
  Φ2's schematic net number fits the low-numbered CPU-cluster nets (net 11 = CLKG_D36 precedent).
- Revised priority pair #1: **E18 ↔ E1/E2** (Φ2 into the spare NAND); E16/E17 ↔ P5V as check #0.
- The transcription line in clock-subsystem.md ("→ pin 7"/"→ pin 14") is ambiguous shorthand —
  flagged for a re-read; board.json remains authoritative (Φ1/Φ2 nets verified by LVS + boot).
ЛА18/ЛН2 queue status: D12 (ЛА18) section 1/2→3 drives S_OC→X3.32; D3 (ЛН2) 11→10 drives
S_TTL→X3.23; both already net-modeled and LVS-green — the "connectivity" item is CLOSED at the
modeled-section level (spare sections of both remain unmapped, as on the schematic).

## Iteration 42 — silk audit of the rebuilt quadrant; D56 mark -> К155АГ3
Render-level silk audit of the ВГ93 quadrant: key notches, along-body marks and key-adjacent
refdes all render correctly for the 10 new/moved footprints (D95/D94/D102/D101/D98/D96/D100/D56/
D106 + relocated D99). One authenticity fix: **D56's silk mark КМ555АГ3 (BOM) -> К155АГ3** (both
row-4 АГ3s on board #2 are К155 8901; real board wins per the D7 precedent). Netlist untouched;
v22 route re-imported clean (0 unconnected / 0 electrical DRC). Silk-polish queue item: the
quadrant portion is CLOSED; remaining silk work is the mixed-series КП14 pinning (which of
D48-D51 carries the К555 part) — blocked on an etch/date-code read.

## Iteration 43 — D106 refdes collision found and fixed: the row-4 АГ3 is NOT D106
Cross-checking the quadrant's provisional refdes against the transcriptions surfaced a hard
conflict: **tape-serial.md has D106 = К554СА3 tape-input comparator, VERIFIED at net level on the
scan** (W/W/E pins 3/4/2, R86 1М8 hysteresis, DATA IN net). So the schematic's D106 is taken, and
the row-4-right АГ3's provisional "D106" tag (inherited from my own early drawing misread of this
area) is wrong. Fix: footprint renamed to the explicitly-non-refdes **'AG3B'** (same convention as
CT16_CTR/DLB for refdes-unknown chips) until an etch read gives its true number.
Knock-on questions now open:
- WHERE is the physical К554СА3? Candidate: the un-IDed "К5xx…/1068" chip at (302,200) — the slot
  I just gave to D99/ИР9. A СА3-vs-ИР9 re-read of that chip is queued (it decides both refdes).
- The other quadrant refdes (D94/D95/D96/D98/D100/D101/D102) came from the same tape-serial agent
  table that was explicitly marked "ignore its refdes" — they stay PROVISIONAL, weight lowered.
Also this pass: D56 silk mark -> К155АГ3 (board-#2 series, D7 precedent); locked PHI1 escape added
for D35.10 (the router's recurring casualty); a longer locked PHI1 west-spine was tried and
REVERTED (shorted on the 2nd DRAM row -- blind hand corridors don't survive this board's density).

## Iteration 44 — the "1068" Rosetta flip: D56 was right where the drawing put it
Max-zoom of the (302,200) chip (photo 7): **К155АГ3 8901, label-down** — and the old
"К555ЛУ?/1068" read of that spot was THIS label upside down ("1068" = "8901" rotated 180°).
Consequences, all applied:
- **D56 restored to its drawn (302,200)** — the iteration-39 relocation is reverted; the drawing
  was right here, my upside-down read was the error. (Add to method rules: a date-code that reads
  "10xx" is almost certainly "8x01" flipped — Soviet date codes are 8yww/9yww.)
- The quadrant row-4 middle АГ3 (owner's layout) is a **third refdes-unknown АГ3** -> footprint
  'AG3C' at (268,124), joining 'AG3B' (295,124).
- **D99/К561ИР9 comes OFF the board**: both location candidates are now refuted ((296,82) excluded
  by the owner's rows; (302,200) is D56's АГ3). The sheet-3 ИР9 goes back on when physically
  located — likely wherever the К554СА3/D106 tape corner actually is.
Board stays at 160 footprints (-D99 +AG3C).

## Iteration 45 — freerouting hang root-caused and FIXED (custom build from the owner's fork)
The v27/v28 "0% CPU forever" runs were NOT GUI hangs: the log tail shows the same
**PolylineTrace.combine() infinite recursion** that killed v10 — this time triggered by the PHI1
escape pre-route. The recursion has no progress guarantee: degenerate/overlapping geometry keeps
combine_at_start/end succeeding, the worker dies by StackOverflowError, and CLI mode then polls
the never-completing job at 0% CPU. (Confusion resolved: the GUI window the owner saw came from a
--help probe launched without --gui.enabled=false — my mistake, unrelated to the hangs.)
Fix: patched combine() into a bounded iterative loop (10k cap + warning) in the owner's fork —
branch `fix-polylinetrace-combine-recursion` at github.com/ddanila/freerouting (build needed
settings.gradle foojay 0.8.0 -> 1.0.0 for Gradle 9.5). The patched executableJar routes the
same DSN at full CPU where stock 2.2.4 died before pass 1. Candidate for an upstream PR.
Addendum (the full saga, for the record): the combine fix STOPS the crash but the degenerate
geometry then LIVELOCKS the 2.2.4 engine (the caller re-invokes combine forever; 49k warnings, 0
passes) — and the fork-master engine, which doesn't livelock, converges 8-unrouted on this board
(weaker router than the 2.2.4 release). Root cause of the degeneracy was OUR PHI1 hand-escape
pre-route; removing it fixed everything: **stock 2.2.4 + mp200 (the persisted GUI max_passes=20
cap was the silent run-killer all along) routes the corrected board FULLY CLEAN (v33: 1151/1151,
0 unconnected, 0 electrical DRC)**. Lessons pinned: (1) no hand pre-routes except straight
long-segment escapes; (2) check ~/tmp freerouting.json for GUI-persisted caps; (3) fork 'custom'
branch (rebased on master) carries the combine guard + patience tuning for future experiments.

## Iteration 46 — X3/X4 looms visually classified LEGIT; СА3 hunt round 1 negative; LVS+boot green
- **X3 (serial) and X4 (DB-26HD) wire looms read end-to-end**: ~8 and ~10 white wires respectively,
  each descending from the connector body straight onto the pad row beneath it — textbook
  panel-connector pigtails, CLASS (c) LEGIT WIRING. Together with E13 (RESET switch drop) and the
  BNC video braid, the entire top-bracket wire population is now accounted for as legit — the ECO
  set stays confined to the clock/timing harnesses (H1/H3 + the cut H2).
- Serial cluster placement re-confirmed in passing: D104 УП2 8923, D14/D32 АП2 8810 ×2, D11 ВВ51А,
  D28 РЕ3 socketed, D97 ВА87 8804, and the 33К serial-shaping resistor (E5's landmark) ✓.
- **К554СА3 (the real D106) hunt, round 1: NEGATIVE in the top corridor** (X3→corner swept at
  full res). Next candidates: the X9 bottom-edge zone (if tape I/O enters there) and the strip
  under the black video cable. ИР9 (D99) likely cohabits with it.
- **LVS: IN SYNC (86 mapped); boot_check: PASS (all 6 guards)** — re-verified after the v33 board
  state; no netlist change in iterations 39-46, invariants hold.

## Iteration 47 — quadrant y-ladder corrected +25 mm (photo-6 grounded); v36 route clean
Row-3 hunt crop delivered a calibration catch instead: **К155ЛН3 8904 + КМ555ТМ2 8905 sit at
y≈90-103** (photo 6, scale verified against D28 and D93's pin field), not y≈70 — photo-1's
top-region compression had the whole quadrant ladder ~25 mm too high. The rows now sit BESIDE
ВГ93, which also matches the owner's "chips around ВГ93" description better. Re-laddered:
row 2 (D94/D102/D101) y=96 · row 3 (D98/D96) y=115 · row 4 (D100/AG3C/AG3B) y=131-132.
ЛП11 (D95, y≈67) was direct-measured and stays. Route v36: 1151/1151, 0 unconnected, 0 electrical
DRC (BA1 was the new ladder's lottery net for two rolls; a D100 nudge cleared it).
СА3 hunt round 2: the row-3 "АП3" (cable-hidden, DIP-8-sized) is now the PRIME К554СА3 candidate —
"АП3" isn't a real part and the tape comparator belongs in exactly this corner. Needs one clean
read past the cable (owner eyeball or a different-angle shot).

## Iteration 48 — Z1 crystal footprint added (passives stage 2 opener); photo sweep complete
- **Z1 = РК-171 crystal** (8903, "Д1" ink stamp) added to board.json + the board at (103,262), the
  D59-corner spot located in iteration 26 and re-confirmed by the angled corner shot
  (PXL_202052986). Footprint: HC49-U horizontal (closest stock shape to the flat РК-171 can);
  nets stay SIM_ONLY (crystal drives D59/ЛН1 — LVS re-verified IN SYNC after the board.json add).
  The trimmer next to it is the remaining stage-2 passive for this corner.
- **Photo inventory now fully swept** (all 22 files opened at least once): the remaining
  unexplored ones turned out to be X1/X2 connector angles, two solder-side corner shots and the
  crystal-corner angle. None sees behind the video cable → the СА3/"АП3" confirmation and the
  quadrant etch-refdes reads are formally OWNER-GATED (eyeball or new photos).
- v37 route (with Z1 as obstacle) running at commit time; board commit follows its completion.

## Iteration 49 — corner photo mined: КП14 series pinned to the D48/D49 cluster; v40 clean
The crystal-corner photo (202052986, board-rotated 180 — '05-9-6'/'7.102.158' read inverted)
delivered more than Z1's spot:
- **The lone К555КП14 (8904) sits in the D48/D49 cluster** next to the ИЕ7 pair — so D50/D51 are
  КР531КП14 (marks corrected; they had inherited К555 from an old assumption). Which of D48/D49
  is the К555 unit still needs one more read (both marks stay КР531 with a comment until then).
  Iteration-26's series-mix census is now positionally anchored.
- The corner's REAL passive arrangement is visible (РК-171 + wire strap, trimmer 8811, МУЗ?
  resistor, КД522 glass diode, green КМ cap, electrolytic pair) and differs from our assumed
  chip-adjacent passive grid (VD5/R19/C31-33 at y~272) — **corner passive re-layout queued** as
  its own iteration with proper photo anchors. Z1 parked at (71,263) until then (the HC49 stand-in
  is fatter than the РК-171 can and collided with the assumed grid at the photo-true spot).
- Route v40: 1151/1151, 0 unconnected, 0 electrical DRC (the Z1 insertions cost three lottery
  rolls: BA0/MA7+ADRB/DB2+ADR1 came up short on v37-v39; v40 clean).

## Iteration 50 — photo-1 Y-SCALE bug found (9.50 not 9.87); corner re-laid, bottom row -6mm
Root-cause of the recurring photo-1 y-drift: **the y-scale is 9.50 px/mm (board spans 2528 px over
266 mm), not the 9.87 px/mm x-scale** I'd been using for both axes. Every photo-1-derived y was
inflated by ~4% (growing toward the bottom edge; the earlier "top-region compression" story was
this same bug seen from the other end). Method rule: measure y EDGE-RELATIVE with the local scale,
or use 9.50 globally; x keeps 9.87.
Fixes applied (edge-relative, straight-on corner crop):
- **Corner cluster re-laid to photo-true spots**: Z1 crystal (78,271) — where the assumed C31-33
  grid used to squat; D59/ЛН1 (105.5,267.5) (was (112,275), 7 mm off); C31-33 -> (86-98, 257);
  R19/VD5 -> the left-edge cluster (60/55, ~272). The trimmer (8811 disc) still needs a footprint.
- **Bottom row -6 mm**: D42/D43/D58 y=269 (pads at 265.2/272.8, ~15 mm body-to-edge — matches the
  photo margin better than the earlier 275), C66/C67 follow at 261.5.
- NOT touched: D26/D54/PIT stack (drawing-derived, not photo-1-derived; their earlier photo
  "confirmations" used the buggy scale and are hereby demoted to unverified).
Route v41: 1151/1151, 0 unconnected, 0 electrical DRC, first roll.

## Iteration 51 — bottom-right stack re-measured on the fixed scale; v46 clean
Edge-relative re-measure of the D26/PIT corner (photo-1, 9.50 y-scale):
- **ВИ53 stack pitch 24 mm CONFIRMS the model exactly**; absolute y was ~7-8 mm inflated (same
  scale-bug family). **D57/D55/D54 -> y 223/245/269, D26 -> (245,265)** — their old positions'
  photo "confirmations" had used the buggy scale, now genuinely re-verified.
- C51 (D26's decoupling cap) took four pockets to re-home — the channel above a horizontal DIP-40
  is too narrow for a disc cap — final spot: (240,278.5), below D26 in the X9 gap.
- Route v46: 1151/1151, 0 unconnected, 0 electrical DRC. (Lottery casualties along the way:
  ADRA/MEMR/DOTCLK16M each came up short once on v42-v45 rolls; DOTCLK16M twice — watch it.)
Un-modeled sighting from the audit crop: a small TO-126-style transistor (КТ815-class?) at
~(250,240) by the D26 corner — the video/beeper driver VT candidates live elsewhere, so this one
needs an ID pass; added to the passives-stage-2 list.

## Iteration 52 — trimmer footprint on the board; mystery transistor = tape-driver hypothesis
- **CT1 trimmer (КТ4-23-class, '8811' disc)** added at (64,261), left of the crystal per the corner
  photos — disc-D7.5 stand-in (stock KiCad has no trimmer lib); ref 'CT1' is a placeholder until
  the schematic yields the real designator. board.json + LVS: IN SYNC (netless part).
- **The (250,240) mystery component read at max zoom**: flat TO-126-class plastic package with a
  heatsink hole and 3 formed leads, no legible marking, sitting between the ВИ53s just above X9 —
  hypothesis: the TAPE motor/relay driver transistor from sheet 3 (X9 = tape I/O). Needs an owner
  ID (marking faces away from all cameras). Not modeled until then.
- Route v48: 1151/1151, 0 unconnected, 0 electrical DRC. Board now 162 footprints.

## Iteration 53 — power traces widened (geometric method); parked widen_power.py retired
**~570 power-net segments (GND/P5V/P12V/M12V/M5V_DERIVED) widened up to 1.0 mm** via the geometric
nearest-foreign-copper method (kicad/widen_power_v2.py) + a targeted DRC-driven repair pass
(narrow_at_violations.py). Final: 0 unconnected, 0 electrical DRC. Matches the original board's
thick power runs (the real solder side shows wide tinned rails).
Gotchas found & handled: (1) mutual widening -- neighbouring power tracks each measured against
the other's OLD width (repair pass catches it); (2) RECT pin-1 pad corners exceed the
circumscribed max(w,h)/2 radius (use the diagonal); (3) freerouting emits 0.2 mm NECKDOWNS near
tight pads -- a repair that "narrows to 0.25" can actually widen those (re-neck to 0.2).
The DRC-count-broken widen_power.py (parked since the first attempt) is deleted.

## Iteration 54 — gerber dry-run + status snapshot + silk polish + width-model fix
- Gerbers/drill export clean on the final board; docs/project-status.md got a dated PCB-track
  snapshot (Phase B substantially complete).
- Silk polish: passive labels stagger in dense rows; the X9 silk box pulled 0.4 mm off the edge
  cut (silk_edge_clearance resolved).
- Width-model correction: freerouting's native routed width is **0.2 mm** (not 0.25) — the earlier
  "neckdown" story was a misread of that. widen_power_v2/narrow_at_violations now use 0.2 as the
  floor/repair target; rebuilt pipeline: 602/865 power segments widened, one repair pass,
  **0 unconnected, 0 electrical DRC**.

## Iteration 55 — SCHEMATIC DESK SESSION (no probing needed): wire numbers decoded; E18 revised
Reading the sheet-1/2 scans directly (ref/schematics/) — the "manual-work-free" pass:
- **The inter-sheet WIRE numbers are the etched numbers' source**: Φ1 = wire 7 (D35.10 → R37 360),
  **Φ2 = wire 14** (D35.12 → R36 360), both "(1)" cross-refs to sheet 1 (CPU 22/15). The
  solder-side "14"/"7" digits near the clock zone (dismissed in iter-38 as power-pin aids) are the
  Φ nets' OWN etched labels. **Iteration-41's "etched 2 = Φ2" is REFUTED** — E18's net-2 identity
  is open again (candidate: a numbered mesh wire on sheet 2 — cross-reference next). Three-digit
  etches (102 etc.) = the X1 edge-pin family (101В INIT, 103С RESIN, 107В BLOCK…), so solder-side
  "102" near D37 marks a net to X1.102B (= AMWC per the connector map!).
- **The clock-corner passive set fully designated from sheet 2**: trimmer = **C73 4/20 pF**
  (CT1 placeholder renamed, board.json + generator updated, LVS IN SYNC), R32 1,2к (Z1 group),
  R37/R36 360 (Φ output series — the long-deferred "R36/R37" item now has values+topology),
  R35 330 / C29 56 / R40 910 (phase RC), R34 13к, R46 200, C6, R31 820.
- **D38 confirmed ЛА1** (4-input NAND, ins 9/12/13/10 → out 8 = /STB) — matches the model; sheet-1
  RESET network confirmed matching the model (S1 → R3/R2/VD1/C1/R4/C21/R20 → ТЛ2 D13 → CPU.12,
  -RESIN at X1.103C).
- Route v50 (with C73): 1151/1151, 0 unconnected, 0 electrical DRC, power re-widened (580 seg).
Next desk steps: sheet-2 wire-number sweep for "2", "18", "41" (closes E13/E18/H1-lash IDs), and
the D37.3 solder-side copper trace with bracketed anchors.

## Iteration 56 — SHEET-3 MINED: tape cluster decoded; quadrant refdes wave; D37-LATCH reframe
Full sheet-3 (tape/serial) + more sheet-2 reading — the biggest single desk haul yet:
- **The drawing's D94-D108 are the К561 CMOS TAPE cluster, not the quadrant's TTL chips**:
  D94=К561ЛН2, D95=К561ЛП2, D96=К561ЛА7, D97=К561ТВ1 (dual JK), D88=К561ТМ2, **D99+D100=К561ИР9
  (the missing ИР9s — there are TWO)**, D101=К561ИМ1 (SM adder), **D106=К554СА3 ✓** (schematic
  confirms the scan verdict), **D108=К561ИЕ11** (refdes run past 107!). Passives: R79 10к/C20
  0,022/C22 1,0/R80 1к (REC.DATA), R87 3к/R88 12к/R89 130к/R100 10к, R102 270 (SYNC out).
- **Wire numbers**: 40=TAPE RUN (→408), **41=SYNC (D12/ЛА18 output via R102, →501)** — the H1
  lash-zone "41" etch is the SYNC net; 42=REC.DATA (→502), 43/44=DATA IN pair (→503/504). Sheet-2:
  **Z1 = 16 MHz** (master net labeled; Z1 value set), 1,23 MHz out of D103/ИЕ10.
- **Board renames applied** (all provably-wrong provisional refs -> type placeholders): D94→IE7X,
  D95→LP11, D96→AG3D, D97→VA87E, D98→KP12A, D100→KP12B, D101→TM2X, D102→LN3X. The physical tape
  cluster (К561 chips) is UNPLACED on our board — its real location is probably the serial corner
  (the К561ЛН2/К155ЛА18 sightings) — a future placement pass.
- **D37 REFRAME**: sheet-2 shows D37 pins 1/2→3 driving **LATCH** (via D33/ЛН1 13→12), fed from
  the D41/ИР16 chain — the "spare gate" isn't spare. The H3 wires at D37.1/2 may RE-IMPLEMENT the
  schematic's own LATCH-source nets (etch fault or revision delta) — class (a)/(c) candidate, not
  a new-logic ECO. Beeper pair #1 should now test E1/E2 ↔ D41 outputs (12/13) FIRST.
- Also confirmed from the schematic: D41=ИР16 ✓ (owner ID), D34=ЛП5 → video SYNC ✓, D47=ИЕ7 with
  an S3.1-S3.6 DIP-switch bank, D38 second section → LOAD, D53 Y-outs through R49-R56 100Ω,
  VT2 КТ315 + VD3 КС147 video mixer (R62-R71, C9/C13).
- Route v51 (renamed board): 1151/1151, **2-unrouted router score is the locked-ADR echo count**,
  0 unconnected, 0 electrical DRC after widen+repair. LVS IN SYNC.

## Iteration 57 — D41 + the LATCH/LOAD chain NET-MODELED (netlist grows: 157 matched, 1156 conns)
The sheet-2 LATCH/LOAD chain is now in the LVS model (the first netlist growth of the
schematic-mining program, and it's exactly the ECO-adjacent circuit):
- **D41 (К555ИР16) net-modeled** (was an untraced footprint): outputs QB(12)/QA(13); parallel
  inputs from the numbered timing-wire bus [boundary]. Instance U_D41, moved into PLACE.
- **New nets (src=scan, sheet-2)**: LATCH_A (D41.12→D37.1), LATCH_B (D40.11/Q3→D37.2),
  LATCH_PRE (D37.3→D33.13), D39_O8 (D39.8→D59.11), LOAD_PRE (D38.6→D59.13). Second sections added
  to la3_gate (D37: 1,2→3; D39: 9,10→8), la1_gate (D38: 5,4,2,1→6), inverter sections to
  ln1_dual (D33: 13→12 = LATCH) and ln1_osc (D59: 13→12 = LOAD, 11→10).
- **Tooling fix en route**: gen_kicad_sch.py built each type's symbol from the FIRST chip of the
  type, silently dropping per-instance extra pins (D37 vs D7) — symbols now take the pin UNION.
- **LVS IN SYNC (157 matched, was 153); BOOT-CHECK PASS (all 6 guards)** — the added sections have
  deferred constant inputs, so the boot stays byte-identical.
- Route v52: **1156/1156** connections, 0 unconnected, 0 electrical DRC, power re-widened.
The ECO's D37 gate now exists in copper: when the beeper (or further tracing) resolves what the
bodge wires actually feed into pins 1/2, the model diff is a one-net edit.

## Iteration 58 — sheet-2 MX zone: D52 = the 5th КП14; E2/E3 jumpers; D53's real feed topology
- **Schematic D52 = КП14 (MX)** — a FIFTH КП14: selects VIDEO ADDRESS vs µP ADDRESS onto D53/ИД7's
  A/B select inputs, **through configuration jumpers E2/E3** (1-2 vs 2-3 positions — board-variant
  timing config!). My untraced "D52"=К155ЛА3 (the lower-left trio read) is disproven -> renamed
  'LA3B'; the trio's ЛА3 is D105 (owner's ID, consistent). The physical 5th КП14's location is
  open (candidate: the (59,237) chip itself — К555КП14 8904 was read in this cluster).
- **D53's real input topology differs from the model**: schematic feeds A/B from the D52 mux via
  E2/E3, C grounded(?), G-enables from RAM SEL; outputs V0-V3 through **R49-R52 100Ω** with
  **R53-R56 5,1к pulls**, then off-region as numbered wires (11-14 family — numbering overlaps the
  Φ wires' 7/14 reads, flagged for re-read; the tape 40-44 family is distinct). The HDL rascas_dec
  (a=ram_sel_n, b=phi1, c=phi2) is functional-intent — RECONCILIATION TODO logged.
- **D92/ЛЕ4's three NOR sections read** ((1,2,13->12), (3,4,5->6), (9,10,11->8) pattern) and
  **D36's two extra ЛА12 sections** ((12,13->11)->R57 20?; (10,9->8)<-D33 11->10 section).
- Board regen (net names shifted 172->177 after the D41 work) + route v53: 1156/1156,
  0 unconnected, 0 electrical DRC, power widened.

## Iteration 59 — PIT channel map: etch "2" = VER RTR; the ECO story tightens to the frame int
Sheet-2 PIT column (D54/D55 ВИ53 timers), channels read in full:
- **D54**: CLK0=9/G0=11/OUT0=10 -> **1MHz (line ref 7)**; CLK1=15/G1=14/OUT1=13 -> **HOR RTR
  (ref 1)**; CLK2=18/G2=16/OUT2=17 -> H.SYNC DSL.
- **D55**: OUT1 -> **VER RTR (ref 2)**; OUT2 -> VERT.SYNC.DEL; CLK1 <- ref 16.
- **E18 reassigned (2nd revision): the etched "2" via = VER RTR** — the vertical-retrace/frame
  signal. Combined with E7 (frame-int corner) and the D37 LATCH-gate section, the ECO now reads:
  **frame-interrupt qualification built from VER RTR-family timing through D37's gate** — the
  iteration-8 hypothesis with real signal names. Beeper pair #1 update: E18 ↔ D55.13 (OUT1).
- РУ5 pin wiring on the sheet matches dram_64kx1 exactly (A0-A7=6/12/13/5/10/7/11/9, RAS=4,
  CAS=15, W=3, DI=2, DO=14) ✓.
- **Numbering caveat logged**: the schematic's edge numbers are per-sheet-boundary line refs
  (collisions exist: "7" = 1MHz on sheet 2 vs Φ1's sheet-1 ref) — the etched-number Rosetta holds
  net-by-net but needs a dedicated cross-reference table pass (nets 11/18/41/102 status: 41=SYNC
  solid, 2=VER RTR strong, 11=CLKG_D36 iter-8 proof stands, 18/102 open).

## Iteration 60 — drawing index read: the quadrant glue has NO schematic; 11 PROM drawings found
The ДГШ 3.031.006 ВС drawing index settles the КП12 hunt: the machine's drawing tree contains NO
FDC module, and the title block shows revision ДГШ003-87 — our Э3 scans are the pre-revision
originals while board 7.102.158 is the '87+ FDC-integrated build. **The ВГ93-quadrant TTL glue
(КП12 ×2, АГ3 ×2-3, ЛП11, ИЕ7/ЛН3/ТМ2) therefore has no schematic in the archive** — placement is
photo-done; nets are formally owner-gated (beeper/etch). Program step 2 closes at maximum
desk-reachable depth. Bonus: **eleven programmed-chip drawings (ДГШ 5.106.037-.047)** documented
into the processor module — the РЕ3/РТ4/ROM programming set; dump procedure updated with the refs.

## Iteration 61 — WIRE-NUMBER TABLE assembled; manual = software volume; jumper family found
- The 286-page "part 3" manual is the SOFTWARE volume (RomBios/EKDOS/NETOS/compilers + DIAGNOSTICS
  docs; useful for the emulation track) — NO revised schematics, so the FDC-glue verdict of
  iteration 60 stands.
- **Etch↔schematic wire-number map (the Rosetta table, from the sheet-2 column sweep)**:
  1=HOR RTR · 2=VER RTR · 7=1MHz · 11-14=D53/ИД7 strobe family (via R49-52 100Ω) ·
  15-18=PIT/mesh links · **21-28=MA bus (D48/D49 КП14 outputs -> РУ5 address)** ·
  **31-38=DB data bus** · 40-44=tape (40=TAPE RUN, 41=SYNC, 42=REC.DATA, 43/44=DATA IN) ·
  5xx=X3/X4/X5 connector pins · 1xxB/C=X1 edge pins. Solder-side digit sweeps can now be READ
  against this table directly.
- **Configuration-jumper family**: E2/E3 (D53 A/B source select), E13 (4-position, video addr
  zone), E10 (sheet 3) — physical solder links, to be footprinted in a future pass.
- D44-D47 ИЕ7 + D48/D49 КП14 schematic pinouts confirm the model's video-address chain wiring ✓.

## Iteration 62 — BOM (ДГШ3.031.006 ВП) fully mined; IO decoder refdes CORRECTED (D2 -> D9)
The purchased-parts list for ДГШ5.109.006, extracted and cross-checked against the model:
- **Near-total count verification**: КР580: ИК80А=1, ИР82=1, ВА86=3 (D4/D29/D107 ✓), ВИ53=3,
  ВК38=1, ВН59=1, **ВВ51А=2** (D11 + the tape USART ✓), ВВ55А=2; К555: ИЕ7=4, ИЕ10=1, **ИР16=3**
  (D41/D42/D43 ✓), ЛА3=3 (D7/D37/D39), ЛЕ4=1, ЛП5=1, ТЛ2=1, ТМ2=1; К531: ИД7=1, ИЕ17=1,
  **КП14=4** + **К555КП14=1** (the 5th mux = the D53-select MX — series mix EXPLAINED);
  К170 АП2=2/УП2=1; К561 tape cluster ЛН2=2 (D3+D94 ✓), ЛА7=1, ЛП2=1, ТМ2=1, ИЕ11=1, ИМ1=1,
  ТВ1=1 (!), ИР9=1 (!) — the last two conflict with my two-refdes sheet-3 reads, flagged;
  565РУ3Г=32 (full population was the spec; board #2 carries 8); К554СА3=1.
- **Programmed-chip drawings decoded**: К573РФ5 ×8 = ДГШ5.106.040-.047 (one per ROM socket!),
  КР556РТ4 ×2 = .037/.038, К155РЕ3 ×1 = .039. **The original module had ONE РЕ3, ONE АГ3, THREE
  ВА87** — the board's extra РЕ3/АГ3×2/ВА87×2 are '87 FDC-revision parts, closing those puzzles.
- **Model correction: the IO decoder (К555ИД7, BOM x1) is D9, not D2** — physical D2 is the 2nd
  РТ4 PROM (drawing .038, socketed by the CPU ✓ photo). All 14 decoder nets renamed D2->D9 in
  board.json/map; D9's footprint is now the netlisted decoder at the bus-band spot (122,136);
  D2 stays as the untraced РТ4 socket at (83,158). **LVS IN SYNC (157), BOOT-CHECK PASS.**
- Solder-side digit harvest round 1: second "18" etch at comp ~(277,56) — net 18 runs vertically
  through the ЛП11 zone (PIT clock-link family); E15/ВК38 zone shows no digits. Sheet-1 X1 table
  extracted in full (ADR 117-124, DAT 129-132, control 102-111 B/C) — solder "102" = AMWC corridor.
- Route v56: 1156/1156, 0 unconnected, 0 electrical DRC (PHI1/PHI2TTL/MA7/ADRB each lost one roll
  in v54/v55 — the KP12A nudge cleared it).

## Iteration 63 — cheap fixes + the D53/D52/E2/E3 netlist session (LVS 161, boot PASS)
Corrections 1-2 (re-zooms): **D97 = ONE К561ТВ1** (sections .1/.2 -- my 'D87' was a misread;
D88 = the one ТМ2 likewise) ✓ BOM count holds. **D99+D100 = TWO ИР9** unambiguous on the sheet --
the BOM's 'x1' is a BOM error (schematic wins). **MX = D52 definitively** (КП14 label crisp);
КП14 = 74S258-class (Y=4/7/9/12) -- which exposed that the model's KP14_MUX pinmap was wrong
(Y on 10-13). D48/D49 net pins renumbered to the real pinout.
Netlist session (3+4):
- **D53 reconciled to sheet-2**: real 74S138 pinout (A/B/C=1/2/3, G1=6, V0-V3=15/14/13/12);
  A/B now fed by the **E2/E3 configuration jumpers** selecting between the **D52 КП14 mux**
  (video/µP address) and Φ1/Φ2 (the traced/boot 2-3 position -- jumper3 model passes Φ, so the
  boot stays byte-identical); C grounded; G1=RAM_SEL; RAS = V3(12) [wire 11], CAS = V2(13)
  [assumed]; R49-R52 100Ω are LVS-invisible series parts (ledger). mem_active became the SACTIVE
  sim-only qualifier (SIM_ONLY allowlist).
- **D52/E2/E3 net-modeled and placed** (D52 at (238,225) beside D53; E2/E3 pin-header jumper
  footprints at (247,237)/(247,241)). Board: 165 footprints, 181 nets.
- **LVS IN SYNC (161 matched, was 157); BOOT-CHECK PASS.** Route v57 in flight.
