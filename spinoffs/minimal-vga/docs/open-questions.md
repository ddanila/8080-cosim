# Open Questions And Rev A Decisions

These items should not block simulator/schematic work. They must be resolved
before ordering hardware.

## Resolved For Rev A

1. Physical CPU target:
   - Use a real DIP-40 Z80 on the first board. No FPGA CPU adapter is part of
     the Rev A baseline.
2. ROM device:
   - Use a 27C256-class DIP-28 ROM footprint. 32 KiB is enough for the current
     recovered Juku ROM image. Keep the footprint compatible with common
     27C256/28C256 programming workflows where possible.
3. DRAM part:
   - Use western 4164-compatible 64K x 1, DIP-16, +5V DRAM parts. Source NOS
     parts first, with 150 ns or faster as the initial speed target.
4. Keyboard:
   - Preserve the Juku-style 8255/74148 keyboard matrix decode on the PCB side.
     Prefer compatibility with the original keyboard connector/pinout for Rev A.
     A PS/2 or AT keyboard adapter can be a later add-on if needed.
5. VGA:
   - Integrate the TTL640x480-derived VGA timing logic onto the PCB. A header
     may remain only as a debug/integration aid, not as the intended Rev A video
     implementation.
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

1. Exact 4164 source:
   - Choose the first buy target from available NOS western 4164-compatible
     parts, then lock speed grade and vendor.
2. Keyboard connector pinout:
   - Confirm the original keyboard connector pinout and mechanical connector.
3. TTL640x480 physical integration:
   - Convert the current VGA timing placeholder into actual onboard logic and
     update the schematic/PCB/BOM.
4. JLCPCB assembly BOM:
   - Assign JLCPCB/LCSC part numbers for sockets, passives, connectors, fuse,
     TVS, reset supervisor, oscillator, and any factory-mounted logic.
5. GAL equations:
   - Freeze decode and DRAM timing equations, then bind GAL pinouts to the
     schematic and PCB.
6. Diagnostic LED values and loading:
   - Confirm final LED colors and resistor values. The Rev A baseline uses 2.2k
     through-hole resistors to keep logic loading modest.
7. Autoroute cleanup:
   - Review trace geometry, via count, power trace widths, and return paths.
     Decide whether to reintroduce GND/+5V pours after manual cleanup.
8. Factory assembly scope:
   - Confirm whether JLCPCB will mount the selected through-hole sockets,
     headers, LEDs, and connectors, or whether any of those become manual
     assembly/DNP rows.
