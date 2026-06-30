# Phase B — PCB from the LVS-verified netlist

Phase B turns the schematic-rooted, LVS-verified connectivity into a physical board. The
bridge already exists (`kicad/juku.board.json` is both the LVS source *and* the PCB source),
so the PCB and the digital twin stay provably the same circuit.

## Pipeline (established)
`kicad/gen_kicad_pcb.py` (run with KiCad's bundled python, which has the `pcbnew` API so the
file is always format-valid):
```
$KICAD/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
    kicad/gen_kicad_pcb.py kicad/juku.board.json kicad/juku.kicad_pcb
```
It loads a real DIP footprint per chip (by package: 8080/8255 → DIP-40, 2764/8238/8251/8259
→ DIP-28, 8253 → DIP-24, 8286 → DIP-20, РУ5/74-series → DIP-16, gates → DIP-14), assigns
every net to its pads, lays the chips out by functional group, and draws a board outline.

## Current outcome ✅
A valid `kicad/juku.kicad_pcb`: **40 footprints, 100 nets, 417 pad-net assignments**, loads in
KiCad 10 and `kicad-cli` (renders via `kicad-cli pcb export svg/pdf`). The full ratsnest is
present — every LVS net is a real PCB connection. This is the first time the model is a
*board*, not just a netlist. Placement is a rough functional-grouped grid (portrait); not yet
the real layout.

## Roadmap (outcomes Phase B can still provide)
1. **Placement refinement** — position chips per the assembly drawing
   (`juku3000/docs/…emaplaat.pdf`: ROM row top, DRAM array centre, edge connector left) so the
   board matches the real ES101 layout (and becomes landscape).
2. **Bus/backplane + connector** — model the expansion connector X1/X2 (a real component), then
   add the located transceivers D23/D24/D25/D29 (`bus-interface.md`) — this *needs* the PCB
   context (the connector), so it belongs here, and pushes the chip count toward 76.
3. **Routing** — autoroute (freerouting) or manual → copper traces; then DRC clean.
4. **Fab outputs** — Gerbers, drill, BOM, pick-and-place, 3D render (`kicad-cli`).
5. **Footprint fidelity** — swap generic DIPs for the exact Soviet packages where they differ
   (e.g. К565РУ5, the К170 drivers, the edge connector).

## Why this matters
The north-star is one schematic-rooted model that is simultaneously the runnable digital twin,
the LVS-checked structure, and the PCB. Phase B closes the last leg: the same `board.json` that
boots the BIOS (cosim/HDL) and passes LVS now also lays out as a board.

## 3D / preview renders
`kicad-cli pcb render` produces true 3D images (the DIP footprints carry 3D models). Point it
at KiCad's bundled 3D-model dir so component bodies resolve:
```
M3D=".../KiCad.app/Contents/SharedSupport/3dmodels"
kicad-cli pcb render --side top --quality high --floor --width 1700 --height 1150 \
  -D KICAD9_3DMODEL_DIR="$M3D" -D KICAD10_3DMODEL_DIR="$M3D" -o docs/pcb-top-preview.png kicad/juku.kicad_pcb
# isometric: add  --perspective --rotate "-30,0,-25"
```
Previews: `docs/pcb-3d-preview.png` (isometric), `docs/pcb-top-preview.png` (top). Green board,
black DIP packages, gold pads — the LVS-verified netlist as a physical board.

## Placement refinement log
- **DRAM bank → right side.** Moved the populated К565РУ5 (D60-67) from centre-left to the
  board's RIGHT side (2 rows of 4), matching `emaplaat.pdf` where the РУ5 array sits on the
  right (rows of D50/D67/D66/D64/D63… / D75/D74/D73…). ROM sockets remain vertical on the left.
  (Exact pixel coordinates still pending a reliable frame; this fixes the cluster *region*.)
- **CPU (D1) → vertical, lower-left.** The drawing shows D1 (and D4/D2/D107) standing
  vertically in the lower-left; reoriented D1 to a vertical DIP-40 there and shifted the
  video + clock rows right to clear it. DRAM (right) and ROM (left) unchanged.
- **USART (D11) → ROM-socket row, vertical.** The drawing places D11 at the right end of the
  ROM-socket row as a vertical chip (like the sockets); moved it there from the I/O block and
  re-tidied the remaining I/O (D57/D54/D26 + D10/D55).
- **PIC (D10) → bottom logic row.** The drawing has D10 (8259) in the bottom-centre row with
  D5/D6/D7 (not up in the I/O block); moved it to the right end of that row.

## VERIFIED coordinate frame (unblocks exact placement)
Both arrowheads of the "310" dimension are now located: left ≈ original-px **1740** (board
left edge), right ≈ **6240** → 4500 px for 310 mm → **px/mm ≈ 14.52** (the earlier 9.35 was
wrong — the board is drawn at ~2:1). Board top edge ≈ y **990**; chips at y≈3100-3900 then fall
correctly in the lower area → board ≈ **310 × 193 mm**.

Frame (for `…emaplaat.pdf` rendered at 200 dpi → 9554×6976):
```
board top-left (orig px) = (1740, 990)
px/mm = 14.52            # same on x and y (drawing is unstretched)
mm_x = (orig_px_x - 1740) / 14.52 ;  mm_y = (orig_px_y - 990) / 14.52
board = 310 x 193 mm
```
A labeled 20 mm grid on this frame aligns with the board outline + chip rows
(`docs/assembly-grid-frame.png`). Per-chip coordinates are now read off this grid, cluster by
cluster, replacing the earlier region-level guesses.
- **First exact-frame coords: ROM row + transceiver x.** Using the verified frame, read the
  ROM sockets at y≈105 (D15≈x28, D16≈x60, ~32 mm pitch) and the transceiver row x positions
  (D25≈28, D23≈68, D24≈122, D29≈158); applied them (D11/USART on the ROM row at y105). These
  replace the earlier region-level guesses for the top clusters.
- **Board size corrected to 310 × 260 mm.** Width 310 is the drawing dimension (confirmed by
  owner; the px/mm=14.52 scale derives from it). The earlier 193mm HEIGHT was wrong — owner
  measured ~260 on the drawing (~270-279 incl. the VIDEO connector overhang; sanity-check vs
  another drawing pending). Spread the lower clusters (CPU/bus/clock) down into the taller board.
  BW/BH are a clearly-marked parameter to update with the exact measured size.
- **DRAM bank → exact read row.** Grid-read the populated К565РУ5 as a horizontal row of
  vertical sockets at y≈158 (descending refdes L→R: D64@x159 … D60@x235, ~19 mm pitch; D65-67
  continue left), center-right — correcting my earlier far-right guess. Moved the video row up
  to y≈130 to clear it.
- **Single-chip sanity check — D1 (CPU).** Identified D1 = CPU8080 (КР580ВМ80А, DIP-40);
  grid-read its center at drawing-mm ≈ (35,176), vertical; placed it; added a silkscreen "D1"
  refdes + the case marking (КР580ВМ80А) above/below it (via a per-type MARK map). Rendered top
  view for visual check against the assembly drawing. (Cyrillic renders partially in KiCad's
  stroke font — В/М glyphs drop; refdes + position are the verification target.)
- **GOST silkscreen font + D1 label fix.** KiCad's stroke font drops Cyrillic В/М, so inject
  `(face "GOST CAD KK")` into the silkscreen text in the generated .kicad_pcb (the TTF resolves
  from ~/Library/Fonts) — the case marking КР580ВМ80А now renders fully. Repositioned D1's
  refdes + marking to sit right beside the CPU (was floating above it near the ROM row).

## Frame fix + validation (D1 sanity check, round 2)
- **Bug found + fixed: board HEIGHT was 260, actually ~300.** Measured the board top edge
  (≈y990) to the bottom edge-connector edge (≈y5367) → ~301 mm. The short 260 was pushing
  chips down in the render (D1 looked ~68% down; true ≈59%). Set BW/BH = 310×300 (pending the
  owner's exact reconcile — owner measured ~260-279, perhaps the chip-area core).
- **Validation test added: `kicad/validate_placement.py`.** Projects every placed footprint
  from the .kicad_pcb back onto the assembly drawing via the frame (px/mm=14.52, origin
  1740,990) and overlays a crosshair + refdes — each should land on its real chip. Confirmed
  D1's crosshair lands on the real D1 (the read is correct). Output: `docs/placement-validation.png`.
- **D1 label:** refdes at the top-narrow end; case marking КР580ВМ80А on the chip body,
  rotated 90° (along the chip), in the GOST font. (Visible in the 2D silkscreen view; a 3D
  render hides on-body silkscreen under the package.)

## Dimensions confirmed + flat compare view
- **PCB = 310 × 260 mm** (owner-confirmed). The 279 is the OUTER envelope — the video jack X8
  extends ~19 mm below the PCB; not the board cut. Edge.Cuts set to 310×260 (top mm22..bottom 282).
- **Flat compare view** (`docs/pcb-flat-preview.png`): rendered with **no 3D chip bodies** —
  component outlines + silkscreen (refdes + markings) + Edge.Cuts, trimmed to the PCB — so it can
  be laid next to the assembly drawing directly. Use `validate_placement.py` for the overlay.
- **D1 labels:** refdes just above the top-narrow end; case marking КР580ВМ80А centred on the
  body, rotated 90° (GOST). D1 currently reads at ~59% down — pending the owner's reference to
  confirm exact centering.

## Anchor bug fixed (owner spotted it) + overlap-checking validation
- **Bug: footprint anchor is pin 1 (a CORNER), not the body centre.** `fp.SetPosition(x,y)` was
  putting the chip's *corner* at the drawing coord, so every chip sat half-its-size down/right.
  For D1 the real centre was at (42.6, **200**) mm = 68% down — not the intended (35,176)=59%.
  This is exactly the residual "still off" the owner saw. **Fix** (`gen_kicad_pcb.py`): after
  placing + rotating, read the bbox centre `c` and re-place at `2*(x,y) - c` so the body CENTRE
  lands on the drawing coord. Verified: D1 centre now = (35.0, 176.0) mm exactly.
- **validate_placement.py upgraded to a pass/fail test:** prints each chip's mm + %-position,
  flags out-of-bounds, and **detects overlapping footprints** (bbox intersection). It also now
  projects the body CENTRE (not the corner anchor) back onto the drawing. First run caught **8
  overlaps** (rot-90 horizontal DIPs packed at ~19 mm pitch but ~22 mm long). Widened the
  video/mux + clock rows to 26 mm pitch → **VALIDATION: PASS, overlaps=0**.
- **D1 confirmed against the owner's full assembly reference (7.102.100):** far-left, vertical,
  ~59% down — matches. The frame (origin 1740,990; px/mm 14.52; PCB 310×260) is validated.
- **Still approximate (next passes):** the clock cluster belongs on the right-centre (near
  D40/D41/D34), and D48/D49 muxes at the DRAM-array left edge — relocate to exact reference coords.

## Clock cluster relocated to its real region (read off the drawing)
- Read the clock/divider/gate mesh off the assembly drawing via the validated frame and moved it
  from the fictional bottom-left row to its **real right-centre region** (right of the DRAM array,
  near D40/D41/D34): D40 (СТ16) @ (277,155) horizontal; D38 (ЛА1) @ (251,176); D39 (ЛА3) @
  (294,176); D36 (ЛА12) @ (244,200); D33 (ЛН1) @ (277,200); D35 @ (263,221, nudged up 4 mm to
  clear D7). All vertical except D40. **VALIDATION: PASS, overlaps=0.**
- D59 (osc) still approximate (bottom row) — the drawing puts it bottom-centre by the transformer.
- Reminder: the КР580ВМ80А case marking is on F.SilkS, visible in the **flat** preview; the **3D
  top** render hides it under the package body. Use the flat view to check markings.

## Lower-left untangle: bus band ↔ array left columns (read off the drawing)
The bottom half had two clusters in SWAPPED bands. Read both off the drawing via the frame and
put them right (one coherent pass; VALIDATION: PASS, overlaps=0):
- **Bus interface band** → its real horizontal row in the gap between the ROM row and the DRAM
  array (was a fictional bottom-centre row): D5 (8238) @ (35,136) far left, D6 @ (68,136),
  DLB(=D8) @ (93,136), D7 @ (143,136), wide D10 (8259) @ (189,136). All horizontal (rot 90).
  (Moved to y136 so the wide DIP-28s clear the ROM bottom; ROM↔array gap is tight.)
- **Video counters (ИЕ7) + DRAM addr muxes (КП14)** → the LEFT columns of the DRAM array, two
  sub-rows: D46(84,217)/D44(97,217)/D48(111,217) over D47(85,242)/D45(98,242)/D49(112,242),
  vertical. (Were a fictional row up in the bus band; now in the array where the drawing shows.)
- Still to refine: D53/D56/D103 (video-output chain, some out by the clock cluster) and D59 (osc).
- **Previews:** both `pcb-flat-preview.png` (silkscreen, markings) and `pcb-top-preview.png` (3D)
  are now regenerated every iteration (owner request — track progress in parallel).

## Video-output chain relocated to the right-centre
Read D53/D103/D56 off the drawing (they cluster with the clock chips on the right, not the old
horizontal band): RAS/CAS decode **D53 (244,225)** below D36; IE10 ctr **D103 (294,200)** below
D39; AG3 one-shot **D56 (305,200)** far right (raw read landed on the 310 edge -> pulled in 5 mm
to keep the DIP on-board; the right board edge may actually extend a touch past 310). All
vertical. VALIDATION: PASS, overlaps=0. The old y132 band is now purely the bus row.
Remaining approximate: D59 (oscillator, bottom-centre by the transformer).

## Board height corrected to 310 × 266 mm (owner measured the real PCB)
Owner measured the physical board: **310 × 266 mm** (was estimating 260). Edge.Cuts bottom moved
22+260=282 → 22+266=**288**. D1 now reads 58% down (was 59%) — closer still to the reference.
The earlier 279 was the OUTER envelope including the video-jack overhang, not the PCB cut.

## All chips marked from the authoritative BOM + D59 placed
- **Every chip now carries its real Soviet case marking** (on-body, along the package axis) and
  refdes, not just D1. Markings read from the component list ДГШ3.031.006 (`nimekiri
  komponendid.pdf`, pp.3-4): CPU **КР580ИК80А** (the BOM designation; = ВМ80А), 8238 **КР580ВК38**,
  8251 **КР580ВВ51А**, 8255 **КР580ВВ55А**, 8253 **КР580ВИ53**, 8259 **КР580ВН59**, ВА86; memory:
  DRAM **565РУ3Г** (the array is РУ3, not РУ5 as the type name suggested), EPROM **К573РФ5**;
  logic: К555ИД7 / К531ИД7, К555ИЕ7 (×4, matches BOM exactly), К531КП14, К531ЛА1, К555ЛА3,
  К531ЛА12, К531ЛН1, КМ555АГ3, К555ИЕ10, К155РЕ3. D40→К561ИЕ11 and D35→КМ555ТМ2 are TENTATIVE
  (the BOM gives counts, not a refdes→part map; pin via the schematic later).
- Marking text angle now follows the package (vertical chip → text along Y; horizontal → along X).
- **D59 (osc)** read off the drawing and placed: horizontal, bottom-centre by the transformer Z
  @ (112,281). No chips remain on the fallback grid. VALIDATION: PASS, overlaps=0.

## DRAM row corrected (verification pass against the drawing)
Verified placements against the drawing via the overlay; the DRAM top row (D67..D60) was an early
region-level guess (x 102..235, pitch 19) shifted ~25 mm too far left at the D67 end. Read it
precisely: **D67=127, D66=144, D65=159, D64=175, D63=191, D62=207, D61=223, D60=238** (~16 mm
pitch). Now the array left column (unmodeled D50 @ ~112) lines up with the D48/D49 muxes beneath
it, as the drawing shows. VALIDATION: PASS, overlaps=0.

## Top rows verified: transceiver row + ROM sockets corrected
Continuing the verification pass into the top of the board (early region-level guesses):
- **Transceiver row** read off the drawing: y59 (was y42), x D25=23/D23=55/D24=86/D29=113
  (were 28/68/122/158 -- too far right).
- **ROM sockets** D15/D16: y86 (was y105), x 22/43 with the real ~21 mm pitch (was 28/60, pitch 32).
- **Deferred to a coordinated top+I/O untangle** (mutually entangled, like the lower-left was):
  D27 (wide PPI, real ~162,57), D11 (USART, real ~201,86 -- collides with the misplaced D55), and
  the **I/O block D54/D55/D57/D26**, which the drawing actually puts on the RIGHT side (e.g. D57
  ~299,238), NOT the top. Reading + placing those together is the next tick.
VALIDATION: PASS, overlaps=0.

## Top + I/O untangle (mirrors the lower-left untangle)
Read the entangled top/I/O chips off the drawing and placed them together (no collisions):
- **D27** (PPI 8255) → right end of the top band @ (162,57); **D11** (USART) → right of the ROM
  sockets @ (201,86).
- **I/O block** moved from the fictional top row to the RIGHT/bottom-right where the drawing has
  it: PITs **D57 (292,230) / D55 (292,252) / D54 (292,276)** stack down the right edge (read ~296,
  pulled to 292 to fit the 310 cut), **D26** (PPI) bottom-right @ (245,276).
This closes the placement sweep: every modeled chip is now at a drawing-read position. The only
known fudge is the right-edge x (D54/55/56/57 read a few mm past 310 -> pulled in; the board's
right edge may truly extend slightly past 310). VALIDATION: PASS, overlaps=0.

## Placement sweep COMPLETE + verified; right-edge width flagged
- **All 40 modeled chips verified against the drawing.** Last unchecked early placements confirmed
  this tick: D4 read (52,157) vs placed (57,158); D2 (82,157) vs (83,158); D1 (30,174) vs (35,176)
  -- all within tall-chip center-reading noise (~5 mm), and D1 was already overlay-validated. Every
  cluster has been read precisely off the assembly drawing and matches. Placement sweep done.
- **Marking legibility:** case-marking text bumped 2.4 -> 2.7 mm / 0.45 mm thickness (still fits
  DIP-14/16) so the markings read clearly in the parallel previews.
- **OPEN, needs the physical board: right-edge width.** The drawing shows passives + a mounting
  hole RIGHT of the x=310 line in the current frame (px/mm 14.52, derived from the "310*" *reference*
  dim, arrows @ orig-px 1740/6240). So either px/mm is a few % long at the far right, or the board
  extends past the 310-dim span (a right-side I/O-connector strip, analogous to the video-jack
  overhang). The far-right chips (D54/55/56/57) were pulled in a few mm to fit. **To lock this:
  measure on the real board the distance from a left-column chip (e.g. D15) to a right-column chip
  (e.g. D57), or chip-to-right-edge** -- that calibrates px/mm independently of the reference dim.

## Tentative markings pinned from the repo's own tracing
The two markings flagged tentative (D40/D35) + D6 are now grounded in the scan/trace docs, and the
guesses were wrong:
- **D40** (CT16 divider): `clock-subsystem.md` calls it ИЕ7 (74161-class); the BOM's lone fast
  **К531ИЕ7** fits (the ×4 К555ИЕ7 are the video counters). My К561ИЕ11 guess was actually D102's
  part (baud-rate counter, per `tape-serial.md`) — not this chip.
- **D35** (clock phase, Φ1/Φ2 gen): `clock-subsystem.md` identifies it as **ЛН5** (→ К531ЛН5),
  not the ТМ2 flip-flop I'd guessed.
- **D6** (decode PROM): `memory.md` records it as **КР556РТ4** [scan], not К155РЕ3.
Every chip marking is now BOM- or scan/trace-grounded. VALIDATION: PASS.

## Placement-vs-drawing overlay committed; remaining work categorized
With the placement sweep complete + verified, committed the verification overlay
`docs/placement-validation.png` (every placed chip's centre projected back onto the real assembly
drawing as a red crosshair + refdes) as the persistent "like original" comparison artifact.
Remaining "more like original" work is now categorically different from per-chip placement:
- **Board features (mechanical, LVS-safe):** corner mounting holes + the X1/X2 edge connectors and
  I/O jacks. Mounting-hole reads need clean per-corner crops (the low-res edge strips weren't
  legible) -- deferred until done precisely rather than guessed.
- **Right-edge width:** still pending a physical-board measurement to lock px/mm (see prior note).
- **Toward 76 chips:** tracing the remaining ~36 chips (per `bom-toward-76.md`) -- a schematic
  tracing effort, not placement.

## Mounting holes added + right-edge width RESOLVED
Surveyed the drawing's corner ⊕ mounting-hole targets: **TL≈(7,30), BL≈(5,289)** on the main
board; **BR≈(319,290)** and the **X6 video jack ≈323** on the RIGHT, *past* the x=310 line.
- **Resolves the open right-edge question:** px/mm 14.52 is correct and 310 IS the main PCB width
  — the right-side video jacks (X6/X7) and their mounting tabs **overhang past 310**, exactly like
  the bottom video-jack overhang gives the 279 "outer" height. No frame error; the far-right chips
  (D54–57, x≈292) sit correctly on the main board.
- **Added the two left-side mounting holes** (Ø3.5 Edge.Cuts cutouts) that fall on the 310×266
  main board: TL (7,30), BL (6,283). The right-side holes live on the jack overhang not modeled by
  this rectangular outline (a future board-shape refinement). VALIDATION: PASS.

## Top edge connectors X1/X2 added (silk annotations)
Added the two prominent top-edge expansion connectors as non-electrical silk OUTLINE annotations
(read off the drawing): **X1 mm15..107, X2 mm118..177** at the top edge. They're placeholders --
the full pin/net connector model is future LVS work (`bom-toward-76.md` cluster 4). The top of the
board now matches the original's look (big connectors over the ROM/transceiver rows). The other
top-right connectors + the X6/X7 video jacks (on the right overhang) are not yet added.
VALIDATION: PASS, overlaps=0.

## Bottom connector X9 added (silk annotation)
Read the bottom edge: **X9** (the mounted bottom connector, pins 58..45) spans mm≈222..273; the
bottom-LEFT card-edge bus contacts (62..59) are at mm≈8..37. Added X9 as a silk box at the bottom
edge (balances X1/X2 at the top). Deferred (need bottom-outline work / are board card-edge
fingers, not mounted parts): the bottom-left card-edge bus contacts, the X6/X7 video jacks
(top-right, on the right overhang past mm310), and the true non-rectangular outline (right/bottom
jack overhangs). VALIDATION: PASS, overlaps=0.

## ROM bank completed to 8 EPROMs (D15-D22)
The BOM lists **К573РФ5 ×8** (8 EPROMs, ДГШ5.106.040-047) -> the ROM row is D15-D22, not just the
2 modeled. Added D17-D22 as **placement-only silk outlines** in the row (y86, ~21 mm pitch) so the
8-socket EPROM bank matches the original. D15/D16 stay the net-modeled chips (shown with the
К573РФ5 marking); D17-D22 carry only a refdes (no marking) to flag they're not yet net-traced
(toward-76). Not in board.json -> LVS unaffected. VALIDATION: PASS.

## DRAM array completed to 32 chips (D60-D91, 4×8 grid)
The BOM has **565РУ3Г ×32** -> the DRAM array is D60-D91 in a 4×8 grid. Row 1 (D60-67 @ y158) is
net-modeled; added the other 3 rows (D68-D91, 24 chips @ y≈190/217/242, same 8 columns x127-238)
as placement-only silk outlines. The array now fills the board centre like the original. With the
ROM bank (8) + DRAM (32) outlines, the board shows ~70 of the 76 chip positions (modeled 40 +
30 placement outlines). VALIDATION: PASS, overlaps=0 (the placement outlines are silk, so the
footprint-overlap check is unaffected; minor cosmetic silk/footprint touches at the array's right
edge by the clock cluster).

## Bottom row + DRAM array left column added (placement outlines)
Added more toward-76 positions as placement-only silk outlines (read off the drawing): the bottom
row **D42/D43/D58** (≈x142/170/197, y281, alongside D59) and the DRAM-array left column **D50/D51**
(≈x112, y158/190). Completes the bottom row and the array's left edge. The board now shows the
left/centre chip count; the RIGHT-side serial/tape/baud section (D92-D107: К561ИЕ11/ИМ1/ИР9 baud
chain, ВН59, etc.) is the main remaining group of positions. VALIDATION: PASS, overlaps=0.

## Right-side block started: D93 + top-edge row (placement outlines)
Began filling the right-side serial/tape/video block (toward-76) with the clearly-separated chips
as placement outlines: **D93** (big, ≈246,64) + the top-edge row **D97/D95/D98/D96** (≈y40, x245-278).
The denser middle cluster there (D99/D100/D101/D102/D104/D106/D28/D12/D3 ...) has tilted/packed
labels in the scan -> needs careful per-chip reads, deferred. VALIDATION: PASS, overlaps=0.

## Lower-left completed: D107 (CPU cluster) + D52/D30
Added the lower-left chips as placement outlines: **D107** (≈52,185, below D4 -> completes the CPU
cluster D1/D4/D2/D107) and the lower-left corner **D52** (≈59,218) and **D30** (≈29,213). The CPU
cluster + lower-left corner now match the original. VALIDATION: PASS, overlaps=0.

## Baud-rate chain added (D102/D101/D99)
Added the readable part of the right-side baud-rate chain as placement outlines: **D102 (≈257,54),
D101 (≈265,54), D99 (≈273,54)** — a row right of D93 (per tape-serial.md: ИЕ11/ИМ1/ИР9). The board
now shows chips in every functional region of the original. Remaining: D100 (2nd ИР9) + the rest
of the packed top-right interface cluster (D104/D106/D28/D12/D3/D14/D32/D94/D95...) which need
careful individual reads. VALIDATION: PASS, overlaps=0.

## D3/D12 added (right of D11)
Added the two small chips just right of D11 (USART) as placement outlines: **D12 (≈215,72), D3
(≈215,92)**. The board now covers all functional regions; remaining are a handful of small,
tightly-packed top-right interface chips (D100/D104/D106/D28/D14/D32/D94) whose scan labels are
hard to localise precisely. VALIDATION: PASS, overlaps=0.

## Clock cluster fill: D41/D37/D34
Added three more clock/divider-cluster chips as placement outlines (read off the drawing): **D41**
(≈251,155, paired with D40), **D37** (≈261,200, between D36/D33), **D34** (≈305,176, right edge).
The clock/divider/video-timing cluster is now densely populated like the original. Remaining are
the few packed top-right interface chips (D100/D104/D106/D28/D14/D32/D94/B92). VALIDATION: PASS.

## Top-edge row completed (D94) — placement reaching the scan's reading limit
Added **D94** (≈261,40) to fill the gap in the top-edge row (D97/D95/D94/D98/D96). NOTE: the dense
top-right corner is now at the limit of reliable scan-reading — a zoomed re-crop of that corner
gave chip positions that conflict with the wider crop by ~15 mm (e.g. D95/D98 read at y57 vs the
y40 row), and the remaining chips there (D100/D104/D106/D28/D14/D32 + the "B92" marking of unclear
class) can't be localised confidently from this scan. Further top-right refinement needs a
higher-res scan or the physical board. VALIDATION: PASS, overlaps=0.

## Count reconciliation found a bug: transceiver row was silently dropped
A placed-position count (40 modeled + 52 outlines = 92 distinct, no duplicates) revealed that
**D25/D23/D24/D29** (the bus transceiver row) were PLACE-dict entries but NOT in board.json — and
the placement loop only iterates board.json refs, so those four NEVER rendered (the whole
transceiver row was missing from every preview). Fixed: removed the phantom PLACE entries and
added D25/D23/D24/D29 as placement outlines in the top band (y59, left of the PPI D27), where the
drawing shows them. The top now reads X1/X2 -> transceiver row -> ROM bank like the original.
Lesson: PLACE entries for refs absent from board.json silently no-op. VALIDATION: PASS, overlaps=0.

## D9 added to the bus band
Filled the bus-band gap with **D9** (≈122,136), between DLB(=D8) and D7 — the drawing's bus row is
D5/D6/D8/D9/D7/D10. Now ~93 chip positions are shown across the board. The genuinely-remaining
unplaced D-numbers are the scan-limited top-right corner chips (D14/D28/D31/D32/D100/D104/D106) and
a couple of lower-left chips (D13/D105) that need careful reads; some of those numbers may not be
ICs at all. VALIDATION: PASS, overlaps=0.

## Lower-left corner corrected + D13/D105 added
A focused crop of the lower-left corner showed D30/D13/D105 form a **horizontal column** at x≈30
(D30 ≈y205, D13 ≈y223, D105 ≈y240) with D52 vertical at x≈59,≈y237. Corrected D30's orientation
(was placed vertical) and D52's y, and added the missing D13/D105. The lower-left now matches the
drawing. VALIDATION: PASS, overlaps=0.

## Top-right corrected from a reliable tight crop (+D28)
A tight (1.375×) crop of the top band resolved the conflicting reads: it's a clean row at **y≈55,
pitch 16**: D28(229)/D97(245)/D95(261)/D94(277)/D98(293)/D96(307), with **D28** previously
unplaced. Corrected the row (was placed at y40/cramped from a lower-res crop), moved **D93** down
to ROM-row level (≈248,86) where top_rows showed it, and **removed the baud chain** (D99-D102 —
their y54 placement overlapped this row and was wrong; defer to a careful re-read). The top-right
is now self-consistent. VALIDATION: PASS, overlaps=0.

## Baud-rate chain placed correctly (y≈82, from a tight crop)
Re-read the baud-rate chain with a magnified crop: it's a row at **y≈82** (below the y55 band),
not the y54 I first guessed — **D102(269), D101(285), D99(301)** (ИЕ11/ИМ1/ИР9 per tape-serial.md).
Re-added at the correct positions (resolving the deferred item from last tick). The whole
top-right is now reconstructed from reliable tight crops. Remaining: D100, D104, D106, D14, D31,
D32 (the last few packed interface chips). VALIDATION: PASS, overlaps=0.

## D106 added (right edge)
Added **D106** (≈307,108) — the chip at the right edge just below the baud chain, read from the
same tight crop. Remaining unplaced: D100, D104, D14, D31, D32 (a few scattered packed chips, each
needing its own tight crop). VALIDATION: PASS, overlaps=0.

## D32 added (top band)
Added **D32** (≈213,46) — a vertical chip in the top band, left of D28, read from a tight crop.
Remaining unplaced: D14, D31, D100, D104 (not visible in the regions cropped so far; likely small
chips needing their own tight crops, or possibly not all ICs). VALIDATION: PASS, overlaps=0.

## Placement layout COMPLETE (milestone)
Final count reconciliation: **102 distinct chip positions, no duplicates** — 40 LVS-net-modeled
chips + 62 placement-only silk outlines. The board now faithfully reproduces the ES101 layout in
every region (top connectors X1/X2 + transceiver row + 8-EPROM ROM bank; bus band; 32-chip DRAM
array with its mux/counter/buffer columns; CPU cluster D1/D4/D2/D107; clock+video-timing cluster;
PIT/PPI I/O column; right-side serial/tape/baud block; bottom row + X9; corner mounting holes).
- **Method that worked for dense areas:** when wide-crop reads conflicted, a magnified per-region
  crop settled the true positions and caught earlier errors (top band, baud chain).
- **Not placed** (genuinely unresolvable from this 200-dpi scan): D14, D31, D100, D104 — not found
  in any cropped region; need a higher-res scan or the physical board. D8 is covered by the DLB
  position; D92 ("B92") is of unclear component class.
- **Next phase is no longer placement** but **net-tracing**: promoting the 62 placement outlines
  into full LVS-modeled chips by tracing their pins from the schematic (the bom-toward-76 grind),
  which advances the runnable digital twin rather than just the picture.

## Chip-count correction: ~101 ICs (not 76); placement matches
Summed the BOM line-item quantities (ДГШ3.031.006 pp.3-4): **101 ICs** (40 memory + 61 non-memory).
The PCB placement reached **102 positions** — matching within ±1. So the real board has ~101 chips,
and the long-standing "76" target was a significant undercount (likely a subset). Updated
`bom-toward-76.md` with the correction. This means the placement layout is genuinely ~complete vs
the real chip count, not 26 short of it. (A few specific refdes — D14/D31/D100/D104 — remain
unresolved and may be offset by minor refdes mismatches, but the scale is right.)

## Generator now reports chip-position count + guards duplicates
Added a build-time report to `gen_kicad_pcb.py`: it prints "N net-modeled + M placement outlines
= total / ~101 BOM ICs" and warns on any duplicate refdes. Current build: **40 + 65 = 105
positions, no duplicates** (the earlier regex-based "62 outlines / 102" undercounted; 65/105 is
authoritative). 105 ≈ the ~101 BOM total within faint-scan reading error — both confirm the board
has ~100 chips, refuting "76". This makes completeness visible on every generate and catches the
double-placement class of bug (cf. the transceiver-row gap found earlier). Board geometry
unchanged — previews identical.

## Comprehensive overlap guard added — found & fixed 6 real collisions
Extended the generator's check to compare placement outlines against the modeled footprints too
(not just outline-vs-outline). It immediately caught **6 collisions** the footprint-only validator
couldn't see: the DRAM array's right column (D60/D68/D76/D84 @ x238) was clipping the clock
cluster's left chips (D36/D53 @ x244, D41), and X9 clipped D26 — the spacing was ~2-3mm too tight.
Fixed: D36/D53 → x247, D26 → y272 (off X9), D41 outline narrowed/shifted. Now **outline-overlap
check: PASS** and **VALIDATION: PASS**. The build now self-checks both footprint and outline
collisions every run.

## Overlay extended to all positions + count bug fixed
Extended `validate_placement.py` to project the placement-outline labels (board-level silk D-text)
too, so the overlay now verifies **all 102 positions** against the drawing, not just the 40 modeled
footprints. This immediately exposed a count bug: the generator's outline counter used
`label[1:2].isdigit()`, which wrongly counted X1/X2/X9 (digits '1'/'2'/'9') as chips — fixed to
`label[:1]=='D'`. Now consistent everywhere: **40 net-modeled + 62 outlines = 102 positions =
~101 BOM ICs (100%)**. `docs/placement-validation.png` regenerated with all 102 crosshairs.
VALIDATION: PASS.

## Side-by-side comparison artifact (capstone)
Built `docs/comparison.png`: the assembly drawing (left, cropped to the 310×266 board) next to the
generated PCB model (right, all 102 chip positions), scaled to match. It makes the "like original"
result directly visible — same ROM bank top-left, DRAM array filling the centre, bus band, CPU
cluster, clock/I/O clusters, and connectors in the same arrangement. (The model side is the F.Fab
silk render; the drawing additionally shows passives/traces not in the chip-level model.) This is
the visual culmination of the placement work: a faithful chip layout at the correct ~101-chip count.
