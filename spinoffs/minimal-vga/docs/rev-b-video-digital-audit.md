# VJUGA rev B Video digital audit — R5.V1

Status: **PASS / ARCHITECTURE AND GAL LOGIC FROZEN; PHYSICAL ACCEPTANCE PENDING.**
Exact parts and land patterns are specified in the
[Video parts contract](rev-b-video-parts.md); routed layout and assembly checks
are described in the [Video PCB guide](rev-b-video-pcb.md).

## Pin, level and timing constraints

- Memory U2 and Video U21 use the Alliance AS6C1008 PDIP-32 pinout:
  pin 1 NC, CE1# pin 22, OE# pin 24, WE# pin 29, CE2 pin 30 and A15 pin 31.
- Video U16 adds `0x1800` using CD74HC283 S0/A0/B0 on pins 4/5/6,
  S1/A1/B1 on 1/3/2 and S2/A2/B2 on 13/14/15.
- Unused CMOS/PLD inputs are tied low; unused outputs remain intentionally NC.
- ACT/HCT inputs accept TTL-level Z80, GAL and ALS outputs. HC parts are used
  where their input-high requirements are met by the preceding drivers.
- U2-U4 are ST M74HC393B1R counters (34 MHz minimum at 4.5 V over -40..85 C);
  U19 is SN74ALS166N (45 MHz), and the scan counters are CD74ACT161E (91 MHz).
- H-decode receives `RESET_N` and forces `H_END` active during reset; V-decode
  propagates reset to `V_END`. Two HCT08 gates translate these TTL-level outputs
  to full-rail `H_CLR`/`V_CLR` for the HC393 asynchronous clears.
- H-decode pin 21 supplies the four-dot `FETCH` window to control-GAL pin 1.
  The separate one-dot `BYTE_TICK` increments the scan counters once per byte.

## Component closure

| Refs | Frozen device/family | Pin, threshold, reset and ownership result |
|---|---|---|
| U1 | 25.175 MHz 5 V oscillator | ECS-100A-251.7; seven local clock inputs; pin 1 NC, 7 GND, 8 output, 14 +5 V. |
| U2-U4 | ST M74HC393B1R | All 42 pins closed; guaranteed clock margin; H/V clear is full-rail through U22. |
| U5 | ATF22V10 H-decode | Counter inputs, global reset, sync/blank, phase, shifter and fetch outputs closed. |
| U6 | ATF22V10 V-decode | Vertical timing, active, row-base, frame-top and frame-tick roles closed. |
| U7 | ATF22V10 control | CPU window, FETCH arbitration, SRAM/buffer ownership and open-drain WAIT role closed. |
| U8-U11 | TI CD74ACT157E | TTL-compatible Z80/GAL inputs; all scan/CPU address lanes and unused inputs closed. |
| U12-U15 | TI CD74ACT161E | 91 MHz minimum, direct reset, one-dot byte enable, row load and carry chain closed. |
| U16 | TI CD74HC283E | Correct physical pinout; inputs come from full-swing ACT counters and outputs feed ACT muxes. |
| U17-U18 | TI CD74ACT273E | TTL-compatible GAL clock/reset, 97 MHz rating, row-base lanes and unused inputs closed. |
| U19 | TI SN74ALS166N | 45 MHz rated shift register; SRAM data and GAL controls are TTL compatible. |
| U20 | TI CD74HCT245E | CPU bus is isolated during scan fetch; TTL inputs accept both bus and SRAM levels. |
| U21 | Alliance AS6C1008-55PCN | Correct 32-pin map; A14-A16 low, CE2 high, 16 KiB local address span. |
| U22 | TI CD74HCT08E | H/V active combine, pixel blanking and H/V reset-level translation; all four gates are used. |
| U23 | TI CD74ACT08E | Three independent high-current RGB outputs; unused fourth gate inputs tied low. |

The generated board has 23 populated digital packages and 398 physical package
pins. Full structural LVS covers every one, including supply pins, and matches 106
multi-endpoint nets. This LVS compares the structural HDL with
`video.board.json`, not extracted PCB copper. The independent pin guard hashes all 398 `(ref,type,pin,net)`
records and separately spells out the SRAM, adder, control GAL, unused-input and bus
isolation contracts. Its self-test rejects both a swapped U16 input and a missing U21
select pin. The LVS negative test makes the same two mutations in a temporary board
and requires `sync/lvs.py` to report a mismatch.

The guard also checks that the frequency limits recorded in
`video-digital-audit.json` exceed the dot clock and that the fetch/WAIT arithmetic
is consistent, with at least 20 ns calculated fetch margin. These are checks of
the frozen assumptions; the script does not retrieve datasheets, calculate
loaded propagation delays or measure the assembled board.

## SRAM phase and WAIT budget

One video byte occupies 16 dots. `FETCH` is high for phases 12-15 in every
horizontal group, including blanking; it is not gated by H/V active video.
This includes the prefetch at dots 796-799 before the next line. The scan address
has a conservatively credited three dot periods (119.166 ns) before the phase-0
shifter load. The assumed path budget is 15 ns ACT157 selection + 55 ns SRAM access + 20 ns shifter
setup = 90 ns, leaving 29.166 ns. The adder settles hundreds of nanoseconds earlier,
immediately after the preceding byte increment, and is not part of that last-edge path.

During `FETCH`, scan address owns U8-U11, U20 is disabled, SRAM read is enabled and
the CPU cannot touch FD. A simultaneous CPU framebuffer request enables U7's
open-drain `WAIT_N` low driver; the backplane 4.7 kohm resistor supplies the high
level. The maximum raw overlap is four dots (158.888 ns). At 2.000 MHz the Z80 may
insert a full wait state, after which U7 selects CPU address/data direction and only
then permits OE# or WE#. The GAL equation oracle checks the digital ownership
outputs. The HDL WAIT test checks the expected phase signal and completion of
81 synthetic writes, including a forced phase-12 collision and active/blanking
writes. It uses a reduced raster and a bus driver that obeys WAIT, not a Z80 CPU.
These checks do not establish physical wait sampling or analog bus timing.

R5.V3 expresses this phase/ownership table in three tracked GAL sources. U6 uses a
registered, illegal-state-recovering modulo-six divider clocked by the dot-640
`RB_STROBE`; `FRAME_TICK` is a roughly 25.4 us pulse on line 524 of every sixth VGA
frame. The equation oracle exhausts all 1024 horizontal and vertical counter states,
all divider states, all 32 address classes, four memory modes, reset and read/write
ownership. The reduced-raster frame-divider test observes three ticks across
18 frames with six-frame spacing. The full-raster scanout test checks sync and pixel output.
The separate integrated TTL-card boot compares framebuffer output with cosim;
it is not run by `revb_video_check.sh`.

The routed-board gate checks the source-local 33 ohm clock resistor, bounds the
seven-load clock tree to 200 mm and the `PIXEL`/`VID_PIXEL` routes to 30/45 mm,
and caps every ACT-to-RGB-resistor path at 20 mm. Current measured CAD route
lengths are recorded in the [Video PCB guide](rev-b-video-pcb.md).

## Primary datasheets

- [Alliance AS6C1008 SRAM](https://www.alliancememory.com/wp-content/uploads/pdf/AS6C1008_Mar_2023V1.2.pdf)
- [ST M74HC393 counter](https://www.st.com/resource/en/datasheet/m74hc393.pdf)
- [TI CD74ACT157 mux](https://www.ti.com/lit/ds/symlink/cd74act157.pdf)
- [TI CD74ACT161 counter](https://www.ti.com/lit/ds/symlink/cd74act161.pdf)
- [TI CD74HC283 adder](https://www.ti.com/lit/ds/symlink/cd74hc283.pdf)
- [TI CD74ACT273 register](https://www.ti.com/lit/ds/symlink/cd74ac273.pdf)
- [TI SN74ALS166 shifter](https://www.ti.com/lit/ds/symlink/sn74als166.pdf)
- [TI CD74HCT245 transceiver](https://www.ti.com/lit/ds/symlink/cd74hc245.pdf)
- [Microchip ATF22V10C](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0735.pdf)

## Verification

Run from the repository root:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_digital.py --self-test
spinoffs/minimal-vga/pld/revb/build_revb_gals.sh
spinoffs/minimal-vga/sim/revb_video_check.sh
spinoffs/minimal-vga/sync/revb_lvs.sh video
spinoffs/minimal-vga/sync/revb_video_lvs_mutation_check.sh
```

`build_revb_gals.sh` requires Galette 0.3.0 and compares freshly compiled outputs
with the five tracked GAL artifact sets; it does not update them unless given
`--update`. The equation oracle checks the source equations and recorded artifact
hashes, not a physical GAL's programmed contents.

`revb_video_check.sh` runs timing-parameter, crop, scanout, WAIT, frame-divider and
address-generator checks. Its crop check reads the existing `cosim/vram.bin`;
it neither generates that framebuffer nor identifies which boot produced it.
Missing or incorrectly sized VRAM skips the crop check. Missing Icarus skips the
HDL simulations, and missing Yosys skips LVS. Inspect these messages before
interpreting an overall successful exit. For integrated firmware boot commands,
see the [execution guide](rev-b-execution-guide.md).
