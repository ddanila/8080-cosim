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
