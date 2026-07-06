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

## Placement Priorities

These are the practical rules for judging whether the board is well arranged.
They are intentionally priority-ordered: do not make a lower item prettier by
breaking a higher item.

1. Fixed/mechanical constraints win first: board outline, mounting holes,
   power input, keyboard header, VGA/debug headers, LEDs, and anything that a
   cable, enclosure, finger, or factory fixture must reach.
2. Electrical ownership wins next: each passive should sit with the active part
   it supports, and each connector should sit near the block whose signals it
   exports.
3. Main buses should flow naturally. CPU address/data/control signals should
   not wrap around DIP bodies just to align packages visually.
4. Functional blocks should read left-to-right/top-to-bottom on Rev A:
   power/input, CPU, ROM/bus glue, DRAM timing, DRAM bank, keyboard, VGA/debug.
5. Repeated blocks should be regular once the electrical constraints are met:
   DRAM chips, decouplers, series resistors, headers, and LED rows should use a
   consistent pitch/orientation.
6. Silkscreen is an assembly aid. Refdes stays near the part, values/types stay
   inside or immediately beside the footprint when readable, and block labels
   should explain the board without occupying routing or soldering clearance.
7. A clean autoroute is placement feedback, not final validation. Use routing
   to expose bad placement and hard nets, but defer production copper polish
   until cosim, schematic review, and sourcing have frozen the netlist.

## VJUGA Block Rules

- CPU/ROM/decode should stay close enough that `A*`, `D*`, `MREQ_N`, `RD_N`,
  `WR_N`, and the GAL decode outputs do not need long detours through
  unrelated blocks. Rev A routes the direct Z80 data bus; optional bus-buffer
  glue is deferred unless verification proves it is needed.
- DRAM timing glue should sit between CPU/ROM glue and the DRAM bank, so
  `RAS_N`, `CAS_N`, `DRAM_WE_N`, address mux control, refresh, and video
  arbitration nets have short paths into the memory row.
- The DRAM bank should remain a repeated IC+decoupler cell. If one DRAM part is
  moved, move the row as a row unless a specific hard net proves otherwise.
- Keyboard decode parts should stay near `J30`; the 8255/74148 behavior is part
  of what this spin-off is meant to prove, so avoid hiding that path behind
  unrelated routing.
- VGA/debug headers should remain reachable from the board edge. The Rev A U40
  TTL640x480 bring-up interface is a boundary for test equipment, not a
  decorative internal block.
- Diagnostic LEDs are review/debug indicators. Keep the LED bank regular and
  labeled, but do not let it steal short routes from CPU/DRAM control nets.

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
- Functional sections use generated F.SilkS block outlines with labels anchored
  at the lower-left inside corner. The checked Rev A blocks are power,
  clock/reset, DRAM refresh/timing, DRAM bank, keyboard matrix, VGA out,
  diagnostic LEDs, and debug headers.
- CPU/ROM/decode/control interface labels sit below their owner chip with a
  uniform 2 mm gap, so the large IC functions can be read without relying only
  on refdes.
- Connector, diagnostic LED, TVS, fuse, and bring-up header values are placed
  below their footprints where practical; their refdes remain near the body.
- GAL U5/U24 silkscreen values are intentionally generic `GAL22V10`; their
  function is carried by the nearby block label and the GAL-equation document.
- Small side labels use the same style as J1/F1 pin/type labels.
- Board-owned silkscreen text keeps at least 1 mm edge clearance.

## Sources

- General layout practice: place fixed/mechanical/user-interface parts first,
  then major ICs, then passives; use the ratsnest to minimize crossings and
  trace length before routing. See KiCad PCB editor docs:
  https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html
- Decoupling guidance from TI and PCB design references: local bypass
  capacitors should minimize the power-pin/ground return loop, with short
  traces/vias and same-side placement when practical. See:
  https://www.ti.com/content/dam/videos/external-videos/de-de/9/3816841626001/6313253251112.mp4/subassets/notes-decoupling_capacitors.pdf
  and
  https://www.protoexpress.com/blog/decoupling-capacitor-placement-guidelines-pcb-design/
- KiCad's auto-place/ratsnest tools are useful for feedback, but final
  placement remains a design decision based on block ownership, routing
  topology, assembly access, and review readability.
