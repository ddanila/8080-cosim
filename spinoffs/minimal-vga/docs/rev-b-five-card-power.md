# VJUGA rev B five-card power and VGA output — R5.V2

Status: **PASS / R5.V6 SYSTEM MODEL FROZEN** on 2026-08-28. The desk budget,
routed-board voltage drop, exact normal supply, protected inputs and assembled
clearance are now one machine-checked contract.

## Video bypass and bulk capacitance

The populated digital set is U1-U23. The generated board contains exactly C1-C23,
each 100 nF from VCC5 to GND, with the numbering contract `Cn` local to `Un` at layout.
`C_BULK` is 47 uF from VCC5 to GND near the card power entry. The machine check rejects
a missing bypass capacitor and requires the bypass count to equal the IC count.

R5.V5 places every 100 nF VCC pad within 12.85 mm of its corresponding package
supply pad and gives it a short solid-ground-plane return. Seven constrained parts
(C5, C7-C11 and C21) sit on the card back directly between front-side socket rows;
their assembled height is included in the passing R5.V6 STEP clearance. The bulk part
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
the order must not be presented as USB-powered. First power-up still uses a current
limit and staged card insertion.

The original R5.V2 desk placeholder allowed 30 mA for the oscillator. R5.V4 selected
the exact `ECS-100A-251.7`; its datasheet permits 70 mA at 24–69.999 MHz, so this table
was conservatively raised by 40 mA rather than preserving the obsolete placeholder.

## R5.V6 protected normal input and supply

Normal operation uses a center-positive **Mean Well GST25A05-P1J**, rated 5 V/4 A,
through exact Wurth `694106301002` barrel jack `J_PWR` (5 A). `F_MAIN` is a Bourns
MF-R250 in series between `PWR_RAW` and `VCC_BUS`; it holds 1.53 A even at 70 C, above
the 1.351 A frozen load. `D_REV` is a 5 A Vishay SB560 crowbar after that fuse,
cathode to `VCC_BUS` and anode to `GND_BUS`. A reversed center contact therefore
becomes a protected fault instead of reverse rail voltage.

USB-C remains an independent service input. MF-R110 fuses its VBUS and a Vishay
1N5822 feeds the system rail anode-to-cathode, blocking the normal barrel supply from
back-powering a USB source. It is explicitly **not** credited for the five-board load.
`W_VCC` and `W_GND` are fitted insulated 22-AWG links that join the high-current bus
rails to the backplane's local logic rails.

The selected adapter publishes a broad +/-5% voltage tolerance, so its nameplate
alone is insufficient for this conservative TTL corner. Receipt acceptance is an
electronic-load test at **1.351 A**: at the plug, require at least **4.90 V average**
and no more than **80 mV peak-to-peak** ripple. A delivered unit that misses either
limit is not qualified for this machine.

## Routed voltage-drop result

The backplane routes `VCC_BUS` and `GND_BUS` at 0.80 mm on 1 oz copper and the short
barrel-to-fuse `PWR_RAW` link at 2.00 mm. The checker turns every actual routed segment
into a resistor, bridges plated pads/vias, and solves all occupied-slot currents. It
also charges maximum initial fuse resistance, both barrel contacts, one VCC and one
GND bus contact per card, and half the adapter ripple limit.

| Slot / card | routed copper drop | modeled rail trough | margin over 4.50 V |
|---|---:|---:|---:|
| 1 / CPU | 79.13 mV | 4.624 V | 124 mV |
| 2 / Memory | 74.21 mV | 4.629 V | 129 mV |
| 3 / I/O | 64.63 mV | 4.641 V | 141 mV |
| 5 / Video | 39.59 mV | 4.650 V | 150 mV |

The effective raw-path resistance is 2.782 mOhm and the shared worst-case input drop
is 149.67 mV. At the adapter's unqualified published -5% corner the modeled trough
would be only 4.474 V; this is why the delivered-unit receipt test is mandatory.

## Machine gate

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_power.py --self-test
. spinoffs/minimal-vga/kicad/revb/env.sh
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_system_physical.py --self-test
```

Negative controls cover the Video capacitor/RGB defects plus a narrow distribution
rail, narrow raw path, wrong slot pitch, low supply and stale current total.

Primary sources: [Microchip ATF22V10C](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0735.pdf),
[TI CD74ACT08](https://www.ti.com/lit/ds/symlink/cd74act08.pdf), and
[Alliance AS6C1008](https://www.alliancememory.com/wp-content/uploads/pdf/AS6C1008_Mar_2023V1.2.pdf).
