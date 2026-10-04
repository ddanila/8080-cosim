# VJUGA rev B D57 and POST contract

Status: **CONTRACT FROZEN / HDL AND PCB MODEL QUALIFIED / BENCH ACCEPTANCE PENDING**.

This is the pin-level contract for the expanded I/O card in
[the five-board order plan](rev-b-five-board-order-plan.md). The machine-readable
authority is [io-expansion.json](../kicad/revb/io-expansion.json). From the
repository root, check its arithmetic and declared decode regions with:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_expansion.py
```

This checker evaluates the declared regions across all 256 ports and both
IORQ/M1 states, checks clock/current arithmetic and selected pin contracts, and
confirms the board's U7 `/4` tap. The [GAL checker](rev-b-gal-equations.md)
separately evaluates the implemented decode equations.

## Address and decode decision

The replacement I/O glue is an `ATF22V10C-15PU` in a socketed narrow DIP-24.
Ordinary device selects require `/IORQ=0` and `/M1=1`, so a Z80 interrupt
acknowledge (`/IORQ=0`, `/M1=0`) cannot select a peripheral. The frozen groups
are PIC `00h-03h`, PPI `04h-07h`, USART `08h-0Bh`, D57 `18h-1Bh`, and write-only
POST `20h-23h`. The groups at `0Ch-17h` and `1Ch-1Fh` remain reserved.

The GAL has eleven used array inputs and eight used outputs. `POST_CLK` is high
at idle, goes low only during a selected write, and clocks the positive-edge
`CD74ACT273E` when the write ends. `/INT` remains open-drain: the GAL may pull it
low for active `PIC_INT`, but never sources the shared bus line.

## Timer and serial clock

U7 divides the 4.9152 MHz oscillator. Its `/4` node supplies
`PIT_CLK0=1.2288 MHz`; D57 channel 0 count four produces 307.2 kHz and drives
both 8251 clock inputs for exact 19,200 baud at x16. Channel 1 receives the
2.000 MHz CPU clock and drives the sound transistor. Channel 2 is deliberately
not a surrogate for original `SYNC B`: its clock is grounded, gate held high,
and output exposed only as a test point.

Two jumpers keep intent visible. `JP_CLK_SRC` selects `PIT` (default, normal) or
`DIRECT` (recovery). Existing rate selection becomes `JP_BAUD`, choosing direct
/16 = 19,200 or /32 = 9,600. NETC10 acceptance always uses the PIT position.

## Layered POST and sound

The eight active-high green LEDs use 2.2 kΩ resistors. At the guarded 5.5 V rail
and 1.8 V LED corner, each is limited to 1.682 mA. Reset directly clears the
latch; reads remain electrically silent. The byte convention is:

- high nibble `1` through `8`: entry, ROM, RAM-data, RAM-address, D57, USART,
  PPI/PIC, VGA/frame;
- low nibble `0`: entered, `1`: passed, `F`: failed;
- `FFh`: ready.

D57 channel 1 drives a 2N3904 low-side stage through 4.7 kΩ with a 100 kΩ base
pulldown. The nominal 5 V passive transducer is the Same Sky
`CPT-1207-5LTH-T`; an optional parallel header permits a bench transducer.
The LED latch does not depend on the PIT or USART.

## Power and physical consequences

The I/O-card current allowance is 454 mA; the complete five-card allowance is
1,655 mA, leaving 345 mA under the 2 A design limit. The exact populated set
and routed voltage-drop model are recorded in
[the five-card power contract](rev-b-five-card-power.md). These modeled margins
do not establish measured board current or physical supply acceptance.

The generated board source implements this contract, including the
socket, one local 100 nF capacitor per U1--U9, defined gates, all clock/output
test points, both jumpers, POST bit labels, and sound network. The I/O card uses
a 100x100 mm two-layer PCB with nine front-side capacitors and GOST reference
plus value/role silkscreen. The [mating report](rev-b-mating-report.md) records
a minimum 3.24 mm card-stack gap computed from the populated STEP models;
physical fit remains part of first-article acceptance.

Executable PCB-model evidence is `check_revb_io_board_expansion.py --self-test`,
`check_revb_io_pcb.py --self-test`, `sync/revb_lvs.sh io`, the total KiCad DRC
gate, and the generated `rev-b-mating-report.md`.

## R5.I2 executable evidence

Run from the repository root:

```sh
spinoffs/minimal-vga/sim/revb_io_expansion_check.sh
```

The script runs the JSON contract check and five HDL cases using 2 MHz CPU and
approximately 4.9152 MHz baud-master clocks. PIT-normal, direct 19,200 and direct
9,600 modes must pass; wrong PIT-tap and POST-alias variants must fail. Icarus
Verilog is required; its absence exits 2 rather than skipping the simulations.

Each positive case checks:

- POST clear at reset, retained `A5h` after a write to `20h`, read silence at
  that port, and no POST change during an M1-low acknowledge cycle;
- PIT channel 0 programmed to count four, with a rising-edge period of 16 baud
  master clocks, and a latched count in `1..4`;
- selected USART clock periods of 16 or 32 baud-master clocks;
- channel 1 mode-3 count 5,102, with a rising-edge period of 5,102 CPU clocks;
- `A6h` TX-to-RX loopback through the root 8251 model and POST clear after activity.

Period checks allow one clock either side of the expected count. The bus driver
is synthetic, and loopback directly joins the model's TX/RX wires. These cases
do not run a ROM, exercise the backplane electrical boundary, or measure the
sound transistor/transducer. Integrated firmware and serial-console checks are
listed separately in the [execution guide](rev-b-execution-guide.md).

## Physical acceptance

Order authorization and assembled-board acceptance remain separate from HDL,
CAD, DRC and STEP checks. Record measured PIT clocks, POST stages, serial
loopback, sound and power behavior with the board identity in
[the bench record](rev-b-b1-bench-log.md). The R5.R1 order hold is controlled by
the five-board plan; this contract does not authorize an order.
