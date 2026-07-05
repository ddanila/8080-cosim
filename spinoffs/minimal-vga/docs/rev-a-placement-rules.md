# Rev A Placement Rules

These rules document the placement style used by the generated VJUGA Rev A PCB.
They are intended to keep later edits visually tidy and electrically defensible.

## Placement Order

1. Place mechanical and user-facing parts first: power input, USB-C input,
   keyboard header, VGA/debug headers, LEDs, mounting holes, and board labels.
2. Place ICs by functional flow: CPU/ROM/bus buffers, DRAM timing, DRAM bank,
   keyboard decode, and VGA output.
3. Place each local passive as part of its owner component cell, not in a
   separate decorative row.
4. Route only after the placement preview looks coherent; moving any footprint
   after routing invalidates the routed board and requires rerouting.

## Decoupling

- Every IC gets one local 100 nF capacitor.
- The capacitor should sit beside the IC power-pin end, close enough that it
  visually reads as belonging to that IC.
- Long vertical DIP packages place the local capacitor on the right side of the
  package, vertical, aligned near the relevant power-pin Y coordinate.
- Horizontal DIP packages place the local capacitor above the package,
  horizontal, aligned near the relevant VCC pin X coordinate.
- For this through-hole 4-layer board, the current generated placement targets
  about 5-10 mm from the nearest VCC/GND pin. This is a practical compromise
  between socket access, silkscreen readability, and routing clearance.
- DRAM decouplers sit in a uniform row immediately below the DRAM packages,
  keeping one repeated IC+cap cell across the memory bank.
- Timing/glue decouplers sit above their owner ICs where that keeps the DRAM
  timing row open for signal routing.

## Visual Alignment

- Repeated ICs use uniform spacing and orientation.
- Repeated passives use matching orientation within a functional block.
- Section labels go below the block when practical; refdes stays close to the
  component body.
- Small side labels use the same style as J1/F1 pin/type labels.

## Sources

- Renesas/Adesto AN105: place decoupling capacitors as close as practical to
  VCC/GND pins and keep traces/vias short.
- KiCad layout practice: place fixed mechanical parts first, then ICs, then
  passives while using the ratsnest to minimize crossings and trace length.
