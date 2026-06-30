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
