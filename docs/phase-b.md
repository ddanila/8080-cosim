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
