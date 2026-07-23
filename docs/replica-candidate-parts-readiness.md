# Replica candidate-part readiness

Status date: **2026-07-23**.

Status: **DATA-SHEET COMPATIBILITY GUARDED / E4, RECEIPT, AND BENCH ACCEPTANCE OPEN**.

This report closes the static pinout, voltage, clock/refresh, speed-grade,
and package questions for two functional-build candidates. It is not a
vendor cart, stock claim, received-part test, or authorization to seat parts.

## Command

```sh
python3 scripts/report_replica_candidate_parts.py
```

## Guarded checks

| Check | Result | Evidence |
| --- | --- | --- |
| Target bank identity and population match | PASS | D84-D91 are eight populated К565РУ5Г devices |
| All populated DRAM sockets retain the JEDEC 4164 pin classes | PASS | pins 2/3/4/14/15/16 = DIN/WE/RAS/DOUT/CAS/GND; pins 5-7,9-13 = MA0-MA7 |
| DRAM option rails preserve the required conditional +5 V configuration | PASS | E4.1=+12 V, E4.2=DRAM pin-8 rail, E4.3=+5 V; 4164 requires E4 2-3 |
| MK4564 primary artifact and interpreted eligibility facts are pinned | PASS | Mostek MK4564-12: JEDEC 64Kx1, single +5 V, 120 ns access, 220 ns cycle, 128/2 ms refresh |
| DRAM source and routed footprints accept the dual-in-line candidate | PASS | D84-D91 use 16-pin, 7.62 mm-row, 2.54 mm-pitch DIP footprints |
| D93 carries the complete FD1793 pin contract | PASS | all 40 host, drive, separator, status, clock, and supply pins match |
| FD179X primary artifact and interpreted supply/clock facts are pinned | PASS | FD1793: pin20 GND, pin21 +5 V, pin40 +12 V, 1 MHz mini-drive clock |
| Board rails and D95 provide the FD1793 operating configuration | PASS | D93 has GND/+5 V/+12 V and D95 selects the source-proved 1 MHz mini-drive clock |
| FDC source and routed footprints accept the plastic candidate | PASS | FD1793B-01 plastic package: 40 pins, 0.600-inch rows, 0.100-inch pitch |

## Eligible functional-build candidates

| Board role | Candidate | Static disposition |
| --- | --- | --- |
| D84-D91 К565РУ5Г bank | Mostek MK4564-12 in the manufacturer's 16-pin dual-in-line option | Pin/function, +5 V, 128-cycle/2 ms refresh, 120 ns access, 220 ns cycle, and footprint eligible; E4 must bridge 2-3 |
| D93 КР1818ВГ93 | Western Digital FD1793B-01 plastic DIP | Complete pin contract, +5/+12 V rails, 1 MHz mini-drive mode, and 0.600-inch DIP footprint eligible |

The candidate names are deliberately exact enough to reject a wrong package
or voltage family. Other 4164/1793 manufacturers and grades remain unapproved
until added here with their own primary data.

## Remaining acceptance gates

- Fit E4 only in the 2-3 position and verify DRAM pin 8 is +5 V before seating any MK4564; the source model preserves all three pads but does not claim the installed jumper position.
- The MK4564-12 maximum access/cycle figures are faster than the recorded 200 ns РУ5Г grade, but unresolved physical CAS/slot timing still requires a scope or staged memory test.
- Do not seat the FD1793 until the remaining D96/D99/D101 support-device continuity and powered-behavior gates close; verify D93 clocks and host strobes at the socket.
- Live seller stock, authenticity, date-code condition, pricing, purchase authorization, receipt inspection, and tester results remain procurement-time evidence.

## Primary evidence

- Mostek `MK4564(P/N/J/E)-12` data sheet SHA-256: `8a6169963c020c1ff8b3c413356ed8f354b9963b77dab8f9bd2af22560c44093`.
- Western Digital `FD179X-01` data sheet SHA-256: `e51aef0933d88e7705f6f774ffb3238e8e8096bd9b9d774a985d95ef5766e3ce`.
- Board pin and rail authority: `kicad/juku.board.json`.
- Package authority: source and promoted routed KiCad PCBs.
