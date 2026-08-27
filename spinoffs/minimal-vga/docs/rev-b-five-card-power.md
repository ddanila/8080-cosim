# VJUGA rev B five-card power and VGA output — R5.V2

Status: **PASS / DESK MODEL FROZEN** on 2026-08-28. The final routed-board voltage-drop,
input-protection and connector-current review remains R5.V6.

## Video bypass and bulk capacitance

The populated digital set is U1-U23. The generated board contains exactly C1-C23,
each 100 nF from VCC5 to GND, with the numbering contract `Cn` local to `Un` at layout.
`C_BULK` is 47 uF from VCC5 to GND near the card power entry. The machine check rejects
a missing bypass capacitor and requires the bypass count to equal the IC count.

These values do not excuse poor placement: R5.V5 must put each 100 nF part at its
corresponding socket/package supply pins with a short ground-plane return. The bulk part
handles card-scale transients; the solid four-layer GND/VCC planes supply the high-
frequency return path.

## VGA RGB electrical model

The monitor, not the card, supplies 75 ohms to ground on each RGB input. Each on-card
part is a **470 ohm series resistor**. U23 assigns a separate CD74ACT08 output to red,
green and blue, avoiding the previous 27 mA combined load on one logic gate.

At a 5.0 V ideal source, each monitor pin receives:

`5.0 × 75 / (470 + 75) = 0.688 V`

and its driver sources `5.0 / 545 = 9.174 mA`. At a guarded 4.4 V driver-high, the
monitor sees 0.606 V. Thus the frozen expected range is 0.606-0.688 V, close to the
nominal 0.7 V VGA level and comfortably below the ACT output's 24 mA/channel rating.
There are no on-card 75-ohm “terminations.”

## Conservative +5 V current budget

The budget uses actual first-article population, conservative datasheet/planning
ceilings and explicit per-card allowances. In particular, each non-low-power
ATF22V10 is allowed 125 mA, matching Microchip's 15 MHz maximum-current revision;
Video has three. RGB assumes all three channels continuously high.

| Card/block | Budget |
|---|---:|
| CPU complete card | 250 mA |
| Memory complete card | 235 mA |
| I/O UART tier, B3 parts DNP | 150 mA |
| Backplane/reset/console/pulls | 30 mA |
| Video oscillator (`ECS-100A-251.7`, 25.175 MHz band maximum) | 70 mA |
| Video 3 x ATF22V10 | 375 mA |
| Video 3 x M74HC393 | 24 mA |
| Video 4 x CD74ACT157 | 20 mA |
| Video 4 x CD74ACT161 | 40 mA |
| Video CD74HC283 | 5 mA |
| Video 2 x CD74ACT273 | 10 mA |
| Video SN74ALS166 | 24 mA |
| Video CD74HCT245 | 10 mA |
| Video HCT08 + ACT08 | 10 mA |
| Video AS6C1008 | 40 mA |
| Video three RGB loads | 28 mA |
| Video card allowance | 30 mA |
| **Video subtotal** | **686 mA** |
| **Five-card total** | **1351 mA** |

A regulated 5 V, 2 A supply leaves 649 mA (32.45%) planning headroom. The USB branch's
MF-R110 has 1.1 A hold current and therefore is not qualified for the complete machine;
the order must not be presented as USB-powered. R5.V6 must qualify and protect the
normal 2 A-or-better bench input, then check routed copper/connector drop. First power-up
still uses a current limit and staged card insertion.

The original R5.V2 desk placeholder allowed 30 mA for the oscillator. R5.V4 selected
the exact `ECS-100A-251.7`; its datasheet permits 70 mA at 24–69.999 MHz, so this table
was conservatively raised by 40 mA rather than preserving the obsolete placeholder.

## Machine gate

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_power.py --self-test
```

The negative controls remove C23 and merge two RGB outputs; both changes must fail.

Primary sources: [Microchip ATF22V10C](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0735.pdf),
[TI CD74ACT08](https://www.ti.com/lit/ds/symlink/cd74act08.pdf), and
[Alliance AS6C1008](https://www.alliancememory.com/wp-content/uploads/pdf/AS6C1008_Mar_2023V1.2.pdf).
