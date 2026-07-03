# Open questions

These should not block the first simulator/schematic scaffold. They must be
answered before ordering hardware.

1. Physical CPU target:
   - Use a real Z80 DIP part for the first board, or keep an FPGA/adapter option
     for the earliest bring-up?
2. ROM device:
   - 27C256/27C512 EPROM/EEPROM, flash, or a small adapter board?
3. DRAM part:
   - Exact 4164-compatible part and speed grade to source first.
4. Keyboard:
   - Reuse the original matrix connector/pinout, or define a simpler local
     keyboard connector while preserving the 8255/74148 decode behavior?
5. VGA:
   - Redraw TTL640x480 as board logic, use it as a daughterboard/header, or keep
     it as an optional timing source during the first PCB revision?
6. Manufacturing:
   - Bare PCB only for revision A, or factory assembly for sockets/passives?
7. Logic-family policy:
   - Prefer HCT/ACT western parts for +5V TTL compatibility, or preserve Soviet
     part footprints where practical?
