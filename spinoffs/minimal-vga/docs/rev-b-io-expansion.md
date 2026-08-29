# VJUGA rev B D57 and POST contract

Status: **R5.I1 CONTRACT FROZEN / R5.I2 TWIN PASS / R5.I4-I5 PHYSICAL PASS**.

This document is the pin-level review record for R5.I1 in
`rev-b-five-board-order-plan.md`. The machine-readable authority is
`../kicad/revb/io-expansion.json`; run its exhaustive arithmetic and decode check
with:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_expansion.py
```

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

U7 already divides the 4.9152 MHz oscillator. Its `/4` node becomes
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

The conservative expansion allowance is 304 mA, raising the I/O-card allowance
from 150 mA to 454 mA and the five-card allowance from 1,351 mA to 1,655 mA.
That leaves 345 mA on the already-qualified 2 A design limit. R5.I7 must replace
this desk allowance with the final exact-population calculation and rerun the
distribution/voltage-drop model.

R5.I4 implements this contract in the generated board source, including the
socket, one local 100 nF capacitor per U1--U9, defined gates, all clock/output
test points, both jumpers, POST bit labels, and sound network. R5.I5 retains the
100x100 mm two-layer policy: bounded attempt-1 routing reaches DRC 0/0, the nine
front-side capacitors preserve a measured 3.24 mm card-stack clearance, and the
reviewed top/bottom renders carry complete GOST reference plus value/role silk.

Executable physical evidence is `check_revb_io_board_expansion.py --self-test`,
`check_revb_io_pcb.py --self-test`, `sync/revb_lvs.sh io`, the total KiCad DRC
gate, and the generated `rev-b-mating-report.md`.

## R5.I2 executable evidence

`sim/revb_io_expansion_check.sh` runs the machine contract and five physical-rate
HDL cases. PIT normal, direct 19,200 and direct 9,600 must pass. A wrong U7 tap
and a POST address alias must fail. The positive cases program and latch D57
channel 0, measure count-four output, measure a full 5,102-clock channel-1 mode-3
period, prove POST reset/retention/read silence and M1 exclusion, and loop byte
`A6h` through the real root 8251 model. The retained per-card, 47-byte bring-up,
two decode-mode EKTA, chip-level TTL-video and serial-console checks also pass.
