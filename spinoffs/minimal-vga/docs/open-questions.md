# Open Questions And Rev A Decisions

These items should not block simulator/schematic work. They must be resolved
before ordering hardware.

## Resolved For Rev A

1. Physical CPU target:
   - Use a real DIP-40 Z80 on the first board. No FPGA CPU adapter is part of
     the Rev A baseline.
   - Owner-ordered CPU target: `Z0840004PSC` 4 MHz DIP Z80. Bring up slower
     first, then validate the 4 MHz target.
2. ROM device:
   - Use a 27C256-class DIP-28 ROM footprint. 32 KiB is enough for the current
     recovered Juku ROM image. Keep the footprint compatible with common
     27C256/28C256 programming workflows where possible.
3. DRAM part:
   - Use western 4164-compatible 64K x 1, DIP-16, +5V DRAM parts. Source NOS
     parts first, with 150 ns or faster as the initial speed target.
   - Owner-ordered DRAM target: Samsung `KM4164B-10`, 100 ns DIP-16.
4. Keyboard:
   - Preserve the Juku-style 8255/74148 keyboard matrix decode on the PCB side.
   - Use a simple 1x15 2.54 mm inline header for Rev A. Pins 1-8 carry keyboard
     columns, pins 9-15 carry row inputs 0-6. The owner will wire an adapter to
     the original keyboard later. A PS/2 or AT keyboard adapter can be a later
     add-on if needed.
5. VGA:
   - For Rev A, use the TTL640x480-derived timing/header interface and export
     RGB/HSYNC/VSYNC/GND plus BLANK_N on a simple 1x7 VGA bring-up/debug
     header. Full onboard TTL640x480 logic expansion is deferred until the
     CPU/DRAM/refresh path is proven.
6. Manufacturing and assembly:
   - Aim Rev A at factory assembly, including passives and sockets where the
     assembler can source and mount them. Vintage/programmable ICs may still be
     supplied separately and inserted into sockets after assembly.
   - The factory assembly BOM must not include the Z80, ROM, DRAM, 8255,
     GAL/PAL, or other socketed ICs as IC parts. It should include the matching
     sockets plus passives, connectors, protection parts, oscillator/reset, and
     diagnostic LEDs. Owner-supplied IC insertion is tracked separately.
7. Logic-family policy:
   - Use western +5V TTL-compatible parts only for this spin-off. Prefer HCT
     where CMOS drive and TTL thresholds matter.
8. Rev A programmable logic policy:
   - Use GAL/PAL-style programmable logic for the first DRAM timing/decode
     iteration, matching the original Juku design approach where practical.
9. Diagnostic policy:
   - Add a first-pass LED bank for +5V, PWR_OK, CLK, RESET_N, M1_N instruction
     fetch activity, and RFSH_N refresh activity. Treat these as bring-up/post
     indicators; use the logic-analyzer headers for precise timing debug.

## Still Open Before Ordering

1. JLCPCB assembly BOM:
   - Remaining missing generated BOM CPN rows are C50, D1, J30, J40,
     J90-J93, R6, R15, U40, and U50.
   - Socket CPNs, common resistor CPNs, USB-C, J1 terminal candidate, reset
     supervisor candidate, decouplers, LEDs, and fuse candidate are assigned in
     `../kicad/rev-a.bom.csv` and `../kicad/rev-a-jlcpcb-cpn-checklist.csv`.
   - Several assigned rows still need footprint confirmation immediately before
     upload, especially J1 5.00/5.08 mm pitch, F1 lead spacing, U51 TO-92
     pinout, and the mechanically smaller 5.1k CC pulldown resistor candidate.
2. TTL640x480 physical integration:
   - Deferred from Rev A. Do not block this manufacturing slice on full onboard
     VGA logic unless the Rev A scope changes.
3. GAL equations:
   - Freeze decode and DRAM timing equations, then bind GAL pinouts to the
     schematic and PCB.
4. Diagnostic LED values and loading:
   - Confirm final LED colors and resistor values. The Rev A baseline uses 2.2k
     through-hole resistors to keep logic loading modest.
5. Autoroute cleanup:
   - Review trace geometry, via count, power trace widths, and return paths.
     Decide whether to reintroduce GND/+5V pours after manual cleanup.
6. Factory assembly scope:
   - Confirm whether JLCPCB will mount the selected through-hole sockets,
     headers, LEDs, and connectors, or whether any of those become manual
     assembly/DNP rows.
