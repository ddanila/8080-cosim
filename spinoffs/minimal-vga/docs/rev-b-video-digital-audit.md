# VJUGA rev B Video digital audit — R5.V1

Status: **PASS / ARCHITECTURE FROZEN** on 2026-08-28. This closes the desk-level
real-silicon and pin-connectivity gate; exact purchasing/land-pattern work remains
R5.V4 and equations/timing simulation remain R5.V3.

## Corrections made by the audit

- Both AS6C1008 definitions had omitted physical pin 1 (NC), shifting nearly the
  entire package. Memory U2 and Video U21 now use the Alliance PDIP-32 pinout:
  CE1# pin 22, OE# pin 24, WE# pin 29, active-high CE2 pin 30, A15 pin 31.
- Video U16 had used a non-existent CD74HC283 pin order. It now adds `0x1800`
  using S0/A0/B0 on pins 4/5/6, S1/A1/B1 on 1/3/2 and S2/A2/B2 on 13/14/15.
- Unused CMOS/PLD inputs are tied low. Unconnected outputs remain intentionally NC.
- Generic HC parts were removed at TTL-level boundaries. ACT/HCT inputs accept the
  guaranteed high levels of the Z80, GAL and ALS shifter.
- Generic HC393 and HC166 timing was too marginal at 25.175 MHz. U2-U4 are the ST
  M74HC393B1R (34 MHz minimum at 4.5 V over -40..85 C); U19 is SN74ALS166N
  (45 MHz). The scan counters are CD74ACT161E (91 MHz minimum).
- H-decode now receives `RESET_N`. Its `H_END` is forced active during reset; V-decode
  propagates reset to `V_END`. Two spare HCT08 gates translate these TTL-level signals
  to full-rail `H_CLR`/`V_CLR` for the HC393 asynchronous clears.
- `FETCH` is separate from the one-clock `BYTE_TICK`: H-decode pin 21 supplies a
  four-dot SRAM ownership window to control-GAL pin 1. This avoids incrementing the
  scan counters four times while still giving the 55 ns SRAM a real access interval.

## Component closure

| Refs | Frozen device/family | Pin, threshold, reset and ownership result |
|---|---|---|
| U1 | 25.175 MHz 5 V oscillator | Seven local clock inputs; exact MPN/OE meaning deferred to R5.V4. |
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
| U22 | TI CD74HCT08E | Pixel blanking plus H/V reset-level translation; only fourth gate is unused and tied. |
| U23 | TI CD74ACT08E | Three independent high-current RGB outputs; unused fourth gate inputs tied low. |

The generated board has 23 populated digital packages and 398 physical package
pins. Full structural LVS covers every one, including supply pins, and matches 104
multi-endpoint nets. The independent pin guard hashes all 398 `(ref,type,pin,net)`
records and separately spells out the SRAM, adder, control GAL, unused-input and bus
isolation contracts. Its self-test rejects both a swapped U16 input and a missing U21
select pin. The LVS negative test makes the same two mutations in a temporary board
and requires `sync/lvs.py` to report a mismatch.

## SRAM phase and WAIT closure

One video byte occupies 16 dots. `FETCH` is high for phases 12-15; the scan address
therefore has three dot periods (119.166 ns) before the phase-15 shifter load. The
guarded path budget is 15 ns ACT157 selection + 55 ns SRAM access + 20 ns shifter
setup = 90 ns, leaving 29.166 ns. The adder settles hundreds of nanoseconds earlier,
immediately after the preceding byte increment, and is not part of that last-edge path.

During `FETCH`, scan address owns U8-U11, U20 is disabled, SRAM read is enabled and
the CPU cannot touch FD. A simultaneous CPU framebuffer request enables U7's
open-drain `WAIT_N` low driver; the backplane 4.7 kohm resistor supplies the high
level. The maximum raw overlap is four dots (158.888 ns). At 2.000 MHz the Z80 may
insert a full wait state, after which U7 selects CPU address/data direction and only
then permits OE# or WE#. No write is dropped and no two outputs own FD or D together.

R5.V3 must express this frozen phase/ownership table in the three GAL sources and
prove it across every CPU/dot-clock phase. R5.V5 must keep the clock and ACT output
traces short and add source damping where the routed topology requires it.

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

## Reproduction

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_digital.py --self-test
spinoffs/minimal-vga/sync/revb_lvs.sh video
spinoffs/minimal-vga/sync/revb_video_lvs_mutation_check.sh
```
